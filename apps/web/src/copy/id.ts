export const COPY = {
  app: {
    title: "GiziGo",
    tagline: "Rencana makan harian terjangkau yang memenuhi AKG keluarga Anda.",
    subtitle: "Berbasis Tabel Komposisi Pangan Indonesia (Kemenkes 2020) dan AKG Permenkes 28/2019.",
  },
  household: {
    sectionTitle: "Anggota Keluarga",
    addMember: "Tambah anggota",
    memberLabel: "Nama panggilan",
    memberCategory: "Kategori AKG",
    removeMember: "Hapus",
    minOneMember: "Minimal 1 anggota keluarga.",
  },
  budget: {
    sectionTitle: "Anggaran Harian",
    label: "Anggaran (Rp / hari)",
    helper: "Geser slider atau ketik langsung.",
  },
  region: {
    sectionTitle: "Wilayah Harga",
    options: {
      dki_jakarta: "DKI Jakarta",
      national_baseline: "Median Nasional",
    },
  },
  restrictions: {
    sectionTitle: "Pembatasan",
    placeholder: "Bahan/kelompok yang dihindari (mis. ikan, kacang)",
    addLabel: "Tambah pembatasan",
    typeAllergy: "Alergi",
    typeReligious: "Religius",
    typeDislike: "Tidak suka",
  },
  persona: {
    label: "Persona Demo",
    options: {
      bu_sari: "Keluarga Bu Sari (4 anggota, Rp 60k)",
      anggaran_ekstrem: "Anggaran Ekstrem (5 anggota, Rp 25k)",
    },
  },
  cta: {
    optimize: "Hitung Rencana",
    optimizing: "Menghitung...",
    reset: "Reset",
  },
  plans: {
    cheapest: "Termurah",
    balanced: "Paling Seimbang",
    diverse: "Paling Beragam",
    relaxedBadge: "Target sedikit dilonggarkan",
    foodGroupCount: (n: number) => `${n} kelompok pangan`,
    totalCost: "Total Biaya",
    relaxationReason: {
      budget_exhausted: "Anggaran tidak cukup untuk swap selanjutnya.",
      akg_bound_violated: "Diversifikasi terbatas oleh AKG.",
      no_unused_food_groups: "Semua kelompok pangan sudah terpakai.",
      underlying_cheapest_infeasible: "Plan dasar tidak fisibel.",
    } as Record<string, string>,
  },
  akg: {
    nutrient: {
      energy_kcal: "Energi",
      protein_g: "Protein",
      fat_g: "Lemak",
      carbohydrate_g: "Karbohidrat",
      iron_mg: "Zat Besi",
      zinc_mg: "Seng",
      vitamin_a_ug_rae: "Vitamin A",
      calcium_mg: "Kalsium",
    } as Record<string, string>,
  },
  infeasibility: {
    title: "Anggaran Saat Ini Tidak Mencukupi",
    minimumLabel: "Anggaran minimum perkiraan",
    deficitLabel: "Nutrisi yang belum tercapai",
    raiseBudget: "Naikkan ke anggaran minimum",
    restrictionsTitle: "Pembatasan Terlalu Ketat",
    restrictionsHint: "Coba longgarkan pembatasan agar ada kombinasi bahan yang fisibel.",
  },
  sensitivity: {
    title: "Skenario Harga (What-If)",
    subtitle: "Geser persentase harga bahan untuk melihat dampaknya.",
    presets: {
      cabai_50: "Cabai +50%",
      telur_minus10: "Telur −10%",
    },
    deltaCost: (delta: number) => {
      const sign = delta > 0 ? "+" : delta < 0 ? "−" : "";
      const abs = Math.abs(delta);
      return `Δ Biaya: ${sign}Rp ${abs.toLocaleString("id-ID")}`;
    },
  },
  drawer: {
    closeLabel: "Tutup",
    methodLabel: "Cara Olah",
    titlePrefix: "Resep:",
    ingredients: "Bahan",
  },
  errors: {
    generic: "Terjadi kesalahan. Silakan coba lagi sebentar lagi.",
    network: "Tidak dapat menghubungi server. Periksa koneksi Anda.",
    validation: "Periksa kembali isian Anda.",
  },
  empty: {
    hero: "Isi data keluarga, anggaran, dan tekan Hitung Rencana untuk mulai.",
  },
  meals: {
    sarapan: "Sarapan",
    makan_siang: "Makan Siang",
    makan_malam: "Makan Malam",
    kudapan: "Kudapan",
  } as Record<string, string>,
  akgCategoryLabel: {
    toddler_1_3: "Balita 1-3 tahun",
    child_4_6: "Anak 4-6 tahun",
    teen_male_13_15: "Remaja Pria 13-15",
    teen_female_13_15: "Remaja Wanita 13-15",
    adult_male_19_49: "Pria Dewasa 19-49",
    adult_female_19_49: "Wanita Dewasa 19-49",
    lactating_mother_0_6m: "Ibu Menyusui (0-6m)",
  } as Record<string, string>,
};
