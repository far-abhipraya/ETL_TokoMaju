import sys
import pandas as pd
from sqlalchemy import create_engine, text

# ----------------------------------------------------------------------
# Konfigurasi
# ----------------------------------------------------------------------
# Samakan dengan connection string di 3_load.py
URL_DW = "mysql+pymysql://root:260412@localhost:3307/tokomain_dw"
TOLERANSI = 1.0  # toleransi selisih (Rp) untuk pembulatan


def rp(x):
    """Format angka ke Rupiah, contoh: Rp 446.380.700"""
    return "Rp " + f"{x:,.0f}".replace(",", ".")


# ----------------------------------------------------------------------
# 1. SEBELUM ETL: hitung dari data mentah (temp_penjualan.csv)
#    Logika parsing harga HARUS sama dengan 2_transform.py
# ----------------------------------------------------------------------
raw = pd.read_csv("temp_penjualan.csv")

raw["id_produk"] = raw["id_produk"].astype(str).str.strip()
raw["id_pelanggan"] = raw["id_pelanggan"].astype(str).str.strip()
raw["harga_satuan"] = pd.to_numeric(
    raw["harga_satuan"].astype(str)
    .str.replace("Rp", "", regex=False)
    .str.replace(".", "", regex=False)
    .str.strip(),
    errors="coerce",
)
raw["tanggal"] = pd.to_datetime(raw["tanggal"], format="mixed", dayfirst=True, errors="coerce")
raw["nilai"] = raw["qty"] * raw["harga_satuan"]

dim_produk = pd.read_csv("temp_dim_produk.csv")
dim_pelanggan = pd.read_csv("temp_dim_pelanggan.csv")

baris_sebelum = len(raw)
total_sebelum = raw["nilai"].sum()

# ----------------------------------------------------------------------
# 2. SESUDAH ETL: query langsung ke tabel fakta di MySQL
# ----------------------------------------------------------------------
engine = create_engine(URL_DW)
with engine.connect() as conn:
    baris_sesudah, total_sesudah = conn.execute(
        text("SELECT COUNT(*), COALESCE(SUM(total_penjualan), 0) FROM fakta_penjualan")
    ).one()
baris_sesudah = int(baris_sesudah)
total_sesudah = float(total_sesudah)

# ----------------------------------------------------------------------
# 3. Tabel perbandingan utama
# ----------------------------------------------------------------------
sel_baris = baris_sesudah - baris_sebelum
sel_total = total_sesudah - total_sebelum

print("=" * 78)
print("REKONSILIASI SEBELUM vs SESUDAH ETL")
print("=" * 78)
print(f"{'Metrik':<24}{'Sebelum ETL':>18}{'Sesudah ETL':>18}{'Selisih':>16}")
print("-" * 78)
print(f"{'Jumlah baris':<24}{baris_sebelum:>18,}{baris_sesudah:>18,}{sel_baris:>16,}")
print(f"{'Total penjualan':<24}{rp(total_sebelum):>18}{rp(total_sesudah):>18}{rp(sel_total):>16}")
print(f"Persentase total berubah : {sel_total / total_sebelum * 100:.2f}%")

# ----------------------------------------------------------------------
# 4. Waterfall: jelaskan selisih tahap demi tahap (mengikuti 2_transform.py)
# ----------------------------------------------------------------------
tahap = []
d = raw
tahap.append(("Data mentah", d))

d = d.drop_duplicates(subset=[c for c in raw.columns if c != "nilai"])
tahap.append(("Hapus duplikat", d))

d = d[d["qty"] > 0]
tahap.append(("Hapus qty <= 0", d))

d = d.dropna(subset=["harga_satuan", "tanggal"])
tahap.append(("Hapus harga/tanggal invalid", d))

d = d[d["id_produk"].isin(dim_produk["id_produk"])]
tahap.append(("Hapus id_produk tak terdaftar", d))

d = d[d["id_pelanggan"].isin(dim_pelanggan["id_pelanggan"])]
tahap.append(("Hapus id_pelanggan tak terdaftar", d))

print("\n" + "=" * 78)
print("RINCIAN SELISIH PER TAHAP TRANSFORM")
print("=" * 78)
print(f"{'Tahap':<34}{'Baris':>8}{'Total (Rp)':>20}{'Perubahan (Rp)':>16}")
print("-" * 78)
prev_total = None
for nama, df_t in tahap:
    tot = df_t["nilai"].sum()
    ubah = "" if prev_total is None else rp(tot - prev_total)
    print(f"{nama:<34}{len(df_t):>8,}{rp(tot):>20}{ubah:>16}")
    prev_total = tot
total_harapan = prev_total

# ----------------------------------------------------------------------
# 5. Status
# ----------------------------------------------------------------------
cocok = abs(total_sesudah - total_harapan) <= TOLERANSI
print("\n" + "=" * 78)
print("HASIL VALIDASI")
print("=" * 78)
print(f"Total hasil rekonstruksi transform : {rp(total_harapan)}")
print(f"Total di tabel fakta (MySQL)       : {rp(total_sesudah)}")
if cocok:
    print("Status: SESUAI. Seluruh selisih terjelaskan oleh tahap cleaning,")
    print("        dan tidak ada nilai yang hilang/berubah saat proses load.")
else:
    print(f"Status: PERLU DITINJAU. Ada selisih tak terjelaskan {rp(total_sesudah - total_harapan)}.")
    sys.exit(1)