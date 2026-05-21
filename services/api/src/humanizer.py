from __future__ import annotations

import logging
from collections.abc import Iterable
from typing import Literal, cast

import httpx

from .config import get_settings
from .data import load_cooking_method
from .models import IngredientUse, MealNarration, Plan

logger = logging.getLogger("gizigo.humanizer")

MEAL_TITLE: dict[str, str] = {
    "sarapan": "Sarapan",
    "makan_siang": "Makan Siang",
    "makan_malam": "Makan Malam",
    "kudapan": "Kudapan",
}


def _format_ingredient(use: IngredientUse) -> str:
    return f"{use.display_name} {round(use.grams)} g"


def _humanize_one(meal_slot: str, items: list[IngredientUse], cooking_method: dict[str, object]) -> MealNarration:
    overrides = cast("dict[str, str]", cooking_method.get("ingredient_overrides") or {})
    group_default = cast("dict[str, str]", cooking_method.get("food_group_default") or {})
    verb_templates = cast("dict[str, str]", cooking_method.get("verb_templates") or {})

    method_count: dict[str, int] = {}
    for u in items:
        method = overrides.get(u.ingredient_id) or group_default.get(u.food_group, "tumis")
        method_count[method] = method_count.get(method, 0) + 1
    method = max(method_count.items(), key=lambda kv: kv[1])[0] if method_count else "tumis"

    template = verb_templates.get(method, "Olah {ingredients} secukupnya.")
    rendered = ", ".join(_format_ingredient(u) for u in items)
    description = template.format(ingredients=rendered)
    title_prefix = MEAL_TITLE.get(meal_slot, meal_slot.capitalize())

    return MealNarration(
        meal_slot=cast("Literal['sarapan', 'makan_siang', 'makan_malam', 'kudapan']", meal_slot),
        title=f"{title_prefix}: {method.capitalize()}",
        description_id=description,
        rendered_via="templated",
    )


def _group_by_slot(plan: Plan) -> dict[str, list[IngredientUse]]:
    grouped: dict[str, list[IngredientUse]] = {}
    for u in plan.ingredients:
        grouped.setdefault(u.meal_slot, []).append(u)
    return grouped


def _validate_llm_text(text: str, items: list[IngredientUse]) -> bool:
    text_low = text.lower()
    for u in items:
        if u.display_name.lower().split()[0] not in text_low:
            return False
    return True


def _llm_generate(slot: str, items: list[IngredientUse]) -> str | None:
    settings = get_settings()
    if not settings.humanizer_llm_enabled:
        return None
    try:
        prompt = (
            "Tuliskan narasi singkat (max 30 kata, bahasa Indonesia) untuk "
            f"sajian {MEAL_TITLE.get(slot, slot)} dengan bahan: "
            + ", ".join(f"{u.display_name} {round(u.grams)}g" for u in items)
            + ". Sebutkan setiap bahan."
        )
        with httpx.Client(timeout=8.0) as client:
            resp = client.post(
                f"{settings.openai_base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.openai_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                    "max_tokens": 120,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        logger.warning("LLM humanize failed: %s", exc)
        return None


def humanize_plan(plan: Plan, use_llm: bool = False) -> list[MealNarration]:
    cooking_method = load_cooking_method()
    grouped = _group_by_slot(plan)
    settings = get_settings()
    enable_llm = use_llm and settings.humanizer_llm_enabled

    out: list[MealNarration] = []
    for slot in ("sarapan", "makan_siang", "makan_malam", "kudapan"):
        items = grouped.get(slot, [])
        if not items:
            continue
        templated = _humanize_one(slot, items, cooking_method)

        if enable_llm:
            llm_text = _llm_generate(slot, items)
            if llm_text and _validate_llm_text(llm_text, items):
                out.append(MealNarration(
                    meal_slot=templated.meal_slot,
                    title=templated.title,
                    description_id=llm_text,
                    rendered_via="llm_validated",
                ))
                continue
            elif llm_text is not None:
                out.append(MealNarration(
                    meal_slot=templated.meal_slot,
                    title=templated.title,
                    description_id=templated.description_id,
                    rendered_via="llm_rejected_fallback_templated",
                ))
                continue
        out.append(templated)
    return out


def _bullet_list(items: Iterable[IngredientUse]) -> str:
    return "\n".join(f"- {_format_ingredient(u)} ({u.food_group})" for u in items)
