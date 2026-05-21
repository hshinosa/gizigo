from __future__ import annotations

import json
import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncIterator

import asyncpg
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from . import optimizer
from .config import get_settings
from .data import load_akg, load_catalog, load_prices
from .models import (
    ApiError,
    HumanizeRequest,
    HumanizeResponse,
    OptimizeRequest,
    OptimizeResponse,
    SensitivityRequest,
    SensitivityResponse,
)
from .humanizer import humanize_plan

logger = logging.getLogger("gizigo")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s :: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    optimizer.configure_determinism()
    settings = get_settings()
    pool: asyncpg.Pool | None = None
    try:
        pool = await asyncpg.create_pool(settings.database_url, min_size=1, max_size=4, timeout=5)
        async with pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS plans (
                    plan_hash      TEXT PRIMARY KEY,
                    request_json   JSONB NOT NULL,
                    response_json  JSONB NOT NULL,
                    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )
        logger.info("postgres pool ready")
    except Exception as exc:
        logger.warning("postgres unavailable, plan caching disabled: %s", exc)
        pool = None
    app.state.pool = pool

    load_catalog()
    load_akg()
    load_prices("dki_jakarta")
    load_prices("national_baseline")
    logger.info("data loaders warm")

    yield

    if pool is not None:
        await pool.close()


app = FastAPI(title="GiziGo API", version="0.1.0", lifespan=lifespan)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = uuid.uuid4().hex[:12]
    request.state.request_id = request_id
    started = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    response.headers["x-request-id"] = request_id
    response.headers["x-elapsed-ms"] = str(elapsed_ms)
    return response


@app.exception_handler(ValidationError)
async def validation_handler(request: Request, exc: ValidationError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "n/a")
    return JSONResponse(
        status_code=422,
        content=ApiError(
            error_code="VALIDATION_ERROR",
            message="Input tidak valid. Periksa kembali isian Anda.",
            request_id=request_id,
            details={"errors": exc.errors()},
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def generic_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "n/a")
    logger.exception("unhandled exception request_id=%s", request_id)
    return JSONResponse(
        status_code=500,
        content=ApiError(
            error_code="INTERNAL_ERROR",
            message="Terjadi kesalahan internal. Silakan coba lagi sebentar lagi.",
            request_id=request_id,
        ).model_dump(),
    )


settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_allowed_origin],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["x-request-id", "x-elapsed-ms"],
)


def _build_solver_inputs(req: OptimizeRequest):
    return optimizer.SolverInputs(
        catalog=load_catalog(),
        prices=load_prices(req.region),
        akg=load_akg(),
        members=tuple(req.members),
        daily_budget_idr=req.daily_budget_idr,
        restrictions=tuple(req.restrictions),
    )


async def _cache_get(pool: asyncpg.Pool | None, plan_hash: str) -> dict[str, object] | None:
    if pool is None:
        return None
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT response_json FROM plans WHERE plan_hash = $1", plan_hash)
    if row is None:
        return None
    return json.loads(row["response_json"]) if isinstance(row["response_json"], str) else row["response_json"]


async def _cache_put(pool: asyncpg.Pool | None, plan_hash: str, request_json: dict[str, object], response_json: dict[str, object]) -> None:
    if pool is None:
        return
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO plans (plan_hash, request_json, response_json)
            VALUES ($1, $2::jsonb, $3::jsonb)
            ON CONFLICT (plan_hash) DO NOTHING
            """,
            plan_hash,
            json.dumps(request_json, ensure_ascii=False),
            json.dumps(response_json, ensure_ascii=False),
        )


@app.get("/v1/health")
async def health(request: Request) -> dict[str, object]:
    request_id = getattr(request.state, "request_id", "n/a")
    pool: asyncpg.Pool | None = request.app.state.pool
    db_ok = False
    if pool is not None:
        try:
            async with pool.acquire() as conn:
                await conn.execute("SELECT 1")
            db_ok = True
        except Exception:
            db_ok = False
    catalog = load_catalog()
    return {
        "ok": True,
        "request_id": request_id,
        "version": "0.1.0",
        "catalog_hash": catalog.catalog_hash,
        "ingredients_count": len(catalog.ingredients),
        "db_ok": db_ok,
    }


@app.post("/v1/optimize", response_model=OptimizeResponse)
async def optimize(req: OptimizeRequest, request: Request) -> OptimizeResponse:
    request_id = request.state.request_id
    started = time.perf_counter()

    inputs = _build_solver_inputs(req)
    plans_payload = []
    pool: asyncpg.Pool | None = request.app.state.pool

    plan_hash_input: dict[str, object] = {
        "members": [m.model_dump() for m in req.members],
        "daily_budget_idr": req.daily_budget_idr,
        "region": req.region,
        "restrictions": [r.model_dump() for r in req.restrictions],
        "plan_types": list(req.plan_types),
        "catalog_hash": inputs.catalog.catalog_hash,
    }
    plan_hash = optimizer.compute_plan_hash(plan_hash_input)

    cached = await _cache_get(pool, plan_hash)
    if cached is not None:
        cached["request_id"] = request_id
        cached["elapsed_ms"] = int((time.perf_counter() - started) * 1000)
        return OptimizeResponse.model_validate(cached)

    cheapest_result = None
    if "cheapest" in req.plan_types or "diverse" in req.plan_types:
        cheapest_result = optimizer.solve_cheapest(inputs)

    infeasibility = None
    if cheapest_result is not None and cheapest_result.status == "infeasible":
        infeasibility = optimizer.analyze_infeasibility(inputs)

    if "cheapest" in req.plan_types and cheapest_result is not None and cheapest_result.status == "optimal":
        plans_payload.append(optimizer.to_plan("cheapest", cheapest_result, inputs))

    if "balanced" in req.plan_types:
        balanced_result = optimizer.solve_balanced(inputs)
        if balanced_result.status == "optimal":
            plans_payload.append(optimizer.to_plan("balanced", balanced_result, inputs))
        elif infeasibility is None:
            infeasibility = optimizer.analyze_infeasibility(inputs)

    if "diverse" in req.plan_types and cheapest_result is not None and cheapest_result.status == "optimal":
        diverse_result, relaxed, reason = optimizer.derive_diverse(cheapest_result, inputs)
        plans_payload.append(optimizer.to_plan("diverse", diverse_result, inputs, relaxed=relaxed, relaxation_reason=reason))

    elapsed_ms = int((time.perf_counter() - started) * 1000)

    response = OptimizeResponse(
        request_id=request_id,
        plan_hash=plan_hash,
        plans=plans_payload,
        infeasibility=infeasibility,
        catalog_hash=inputs.catalog.catalog_hash,
        elapsed_ms=elapsed_ms,
    )

    if plans_payload and infeasibility is None:
        await _cache_put(pool, plan_hash, plan_hash_input, response.model_dump())

    return response


@app.post("/v1/sensitivity", response_model=SensitivityResponse)
async def sensitivity(req: SensitivityRequest, request: Request) -> SensitivityResponse:
    request_id = request.state.request_id
    started = time.perf_counter()

    base_inputs = _build_solver_inputs(req.base_request)
    base_plan_hash = optimizer.compute_plan_hash({
        "members": [m.model_dump() for m in req.base_request.members],
        "daily_budget_idr": req.base_request.daily_budget_idr,
        "region": req.base_request.region,
        "restrictions": [r.model_dump() for r in req.base_request.restrictions],
        "plan_types": req.base_request.plan_types,
        "catalog_hash": base_inputs.catalog.catalog_hash,
    })

    perturbed_prices = dict(base_inputs.prices.prices_per_100g)
    for p in req.perturbations:
        if p.ingredient_id in perturbed_prices:
            perturbed_prices[p.ingredient_id] = max(
                0.0,
                perturbed_prices[p.ingredient_id] * (1.0 + p.delta_pct / 100.0),
            )
    from .data import PriceTable
    new_prices = PriceTable(region=base_inputs.prices.region, prices_per_100g=perturbed_prices)
    new_inputs = optimizer.SolverInputs(
        catalog=base_inputs.catalog,
        prices=new_prices,
        akg=base_inputs.akg,
        members=base_inputs.members,
        daily_budget_idr=base_inputs.daily_budget_idr,
        restrictions=base_inputs.restrictions,
    )

    plans_payload = []
    base_cost = 0.0
    new_cost = 0.0

    if "cheapest" in req.base_request.plan_types:
        base = optimizer.solve_cheapest(base_inputs)
        new = optimizer.solve_cheapest(new_inputs)
        base_cost = base.total_cost_idr
        new_cost = new.total_cost_idr
        if new.status == "optimal":
            plans_payload.append(optimizer.to_plan("cheapest", new, new_inputs))

    if "balanced" in req.base_request.plan_types:
        new_balanced = optimizer.solve_balanced(new_inputs)
        if new_balanced.status == "optimal":
            plans_payload.append(optimizer.to_plan("balanced", new_balanced, new_inputs))

    perturbed_hash = optimizer.compute_plan_hash({
        **{
            "members": [m.model_dump() for m in req.base_request.members],
            "daily_budget_idr": req.base_request.daily_budget_idr,
            "region": req.base_request.region,
            "restrictions": [r.model_dump() for r in req.base_request.restrictions],
            "plan_types": req.base_request.plan_types,
            "catalog_hash": base_inputs.catalog.catalog_hash,
        },
        "perturbations": [p.model_dump() for p in req.perturbations],
    })

    return SensitivityResponse(
        request_id=request_id,
        base_plan_hash=base_plan_hash,
        perturbed_plan_hash=perturbed_hash,
        plans=plans_payload,
        cost_delta_idr=round(new_cost - base_cost, 0),
        elapsed_ms=int((time.perf_counter() - started) * 1000),
    )


@app.post("/v1/humanize", response_model=HumanizeResponse)
async def humanize(req: HumanizeRequest, request: Request) -> HumanizeResponse:
    request_id = request.state.request_id
    plan_hash = optimizer.compute_plan_hash({
        "plan_type": req.plan.plan_type,
        "ingredients": [i.model_dump() for i in req.plan.ingredients],
    })
    meals = humanize_plan(req.plan, use_llm=req.use_llm)
    return HumanizeResponse(request_id=request_id, plan_hash=plan_hash, meals=meals)
