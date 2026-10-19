# IF3170 Tugas Besar 1 — Optimasi Muatan Truk (Local Search)

Repositori kelompok **G07 — LaCafeLapo** untuk Tugas Besar 1 IF3170 Inteligensi Artifisial.

## Deskripsi Singkat

Program ini menyelesaikan permasalahan **optimasi konfigurasi muatan truk**: memilih dan
menempatkan paket ke dalam bak truk agar **total `value` paket yang masuk (`inside`)
maksimal**. Ruang muat truk secara default berukuran `10 × 20 × 5` dengan `max_capacity = 500`.

Setiap paket memiliki atribut `id, w, l, h, value, weight, is_fragile, eta`, dan tiap paket
dapat diputar ke salah satu dari 6 orientasi (`src/core/models.py`). Sebuah konfigurasi
dianggap **valid** bila memenuhi seluruh batasan berikut:

- Tidak ada paket yang mengambang (*no floating*) — setiap paket harus ditopang oleh dasar
  truk atau paket lain.
- Tidak ada paket yang menembus dinding bak (*no wall piercing*).
- Paket **fragile** tidak boleh dijadikan penyangga dan tidak boleh berada di bawah paket lain
  (hanya kontak langsung).
- Total `weight` paket di dalam truk tidak melebihi `max_capacity`.

Algoritma *local search* yang diimplementasikan:

- **Hill-Climbing**: Steepest Ascent, Stochastic, Sideways Move, Random Restart
- **Simulated Annealing**
- **Genetic Algorithm**

Selain itu tersedia **CLI**, **visualisasi 3D** keadaan truk, **plot riwayat objective**,
**dataset tetap maupun generator dataset**, serta **runner eksperimen** untuk membandingkan
kinerja tiap algoritma.

### Struktur Repositori

```
src/
  core/           # models, evaluator, initializer, neighbors, loader
  algorithms/     # hill_climbing, simulated_annealing, genetic_algorithm
  visualization/  # render 3D state + plot objective
  experiments/    # configs + runner eksperimen
  main.py         # entrypoint CLI
data/             # dataset tetap + generator dataset
output/           # hasil run (JSON + PNG)
docs/             # dokumen laporan
```

## Cara Setup & Run

**Prasyarat:** Python 3.10+ dan `pip`.

```bash
# 1. Setup environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt    # numpy>=1.24, matplotlib>=3.7
```

**Menjalankan satu algoritma** (default dataset `data/fixed_packages.json`):

```bash
python src/main.py --algorithm hc_steepest --runs 3 --seed 42
```

Pilihan `--algorithm`: `hc_steepest`, `hc_stochastic`, `hc_sideways`, `hc_random_restart`,
`sa`, `ga`. Gunakan `--list-algorithms` untuk menampilkan daftar.

Opsi lain yang tersedia:

```bash
python src/main.py --algorithm ga \
  --dataset data/fixed_packages.json \
  --runs 3 --seed 42 --fill-ratio 0.7 \
  --param population_size=50 --param generations=50 \
  --output-dir output
```

- `--dataset`   : path JSON paket
- `--truck`     : path JSON konfigurasi truk (opsional, default `10×20×5` / `500`)
- `--runs`      : jumlah pengulangan (seed bertambah tiap run)
- `--fill-ratio`: peluang paket dimasukkan saat inisialisasi
- `--param KEY=VALUE`: parameter algoritma (boleh diulang)

**Membuat dataset acak:**

```bash
python data/generate.py --n 30 --seed 42 --out data/random_packages.json
```

**Menjalankan seluruh eksperimen** (semua algoritma, beberapa seed, sekaligus menulis
ringkasan):

```bash
python src/experiments/runner.py --output-dir output/experiments
# subset: --algorithms hc,sa,ga  |  seeds: --seeds 0,1,2
```

**Hasil** tersimpan di `output/`: file `*.json` (ringkasan + penempatan paket) dan
`*_initial.png`, `*_final.png`, `*_history.png` (serta `*_prob.png` untuk SA). Runner
eksperimen menambahkan `summary.json`, `summary.csv`, dan `summary.md`.

## Pembagian Tugas

| Anggota | NIM | Kontribusi |
|---|---|---|
| Stevanus Agustaf Wongso | `13524020` | Simulated Annealing, visualisasi (rendering 3D + plotting) |
| Jonathan Kris Wicaksono | `13524023` | Genetic Algorithm, model/representasi |
| Philipp Hamara | `13524101` | Hill-Climbing (4 varian), model/representasi |
