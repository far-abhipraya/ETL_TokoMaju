import pandas as pd
import numpy as np

# Baca kembali hasil extract
df_penjualan = pd.read_csv("temp_penjualan.csv")
df_produk = pd.read_csv("temp_produk.csv")
df_pelanggan = pd.read_csv("temp_pelanggan.csv")

jumlah_awal = len(df_penjualan)
print(f"Jumlah transaksi mentah: {jumlah_awal}")

# Cleaning df_penjualan
# Bersihkan ID: nilai kosong diganti ID khusus sebelum diubah ke string,
# supaya tidak berubah menjadi teks "nan"
def bersihkan_id(seri, id_kosong):
    seri = seri.astype("string").str.strip()
    seri = seri.replace({"": pd.NA, "nan": pd.NA, "NaN": pd.NA, "None": pd.NA})
    return seri.fillna(id_kosong).astype(str)

df_penjualan["id_produk"] = bersihkan_id(df_penjualan["id_produk"], "P_UNKNOWN")
df_penjualan["id_pelanggan"] = bersihkan_id(df_penjualan["id_pelanggan"], "C_UNKNOWN")
print(f"Transaksi dengan id_pelanggan kosong: {(df_penjualan['id_pelanggan'] == 'C_UNKNOWN').sum()}")
print(f"Transaksi dengan id_produk kosong: {(df_penjualan['id_produk'] == 'P_UNKNOWN').sum()}")

# Bersihkan kolom harga_satuan: hapus "Rp", ".", spasi lalu ubah ke angka
df_penjualan["harga_satuan"] = (
    df_penjualan["harga_satuan"]
    .astype(str)
    .str.replace("Rp", "", regex=False)
    .str.replace(".", "", regex=False)
    .str.strip()
)
df_penjualan["harga_satuan"] = pd.to_numeric(df_penjualan["harga_satuan"], errors="coerce")

# Terjemahkan nama bulan bahasa Indonesia yang tidak dikenali pandas
bulan_id = {"Mei": "May", "Agu": "Aug", "Okt": "Oct", "Des": "Dec"}
df_penjualan["tanggal"] = df_penjualan["tanggal"].astype(str).str.strip()
for indo, eng in bulan_id.items():
    df_penjualan["tanggal"] = df_penjualan["tanggal"].str.replace(rf"\b{indo}\b", eng, regex=True)

# Standarisasi semua format tanggal
df_penjualan["tanggal"] = pd.to_datetime(df_penjualan["tanggal"], format="mixed", dayfirst=True, errors="coerce")

# Hapus duplikat
sebelum = len(df_penjualan)
df_penjualan = df_penjualan.drop_duplicates()
print(f"Setelah hapus duplikat: {len(df_penjualan)} (hilang {sebelum - len(df_penjualan)})")

# Hapus baris dengan qty negatif atau nol
sebelum = len(df_penjualan)
df_penjualan = df_penjualan[df_penjualan["qty"] > 0]
print(f"Setelah hapus qty negatif/nol: {len(df_penjualan)} (hilang {sebelum - len(df_penjualan)})")

# Hapus baris dengan harga/tanggal tidak valid (NaN setelah konversi)
sebelum = len(df_penjualan)
df_penjualan = df_penjualan.dropna(subset=["harga_satuan", "tanggal"])
print(f"Setelah hapus harga/tanggal tidak terbaca: {len(df_penjualan)} (hilang {sebelum - len(df_penjualan)})")

print(f"Jumlah transaksi setelah cleaning: {len(df_penjualan)} (dari awal {jumlah_awal})")

# Cleaning df_produk
# Bersihkan spasi di id_produk dan nama_produk
df_produk["id_produk"] = df_produk["id_produk"].astype(str).str.strip()
df_produk["nama_produk"] = df_produk["nama_produk"].astype(str).str.strip()

# Standarisasi kategori
df_produk["kategori"] = df_produk["kategori"].astype(str).str.strip().str.lower()

kategori_mapping = {
    "elektronik": "Elektronik",
    "elektonik": "Elektronik",
    "fashion": "Fashion",
    "makanan & minuman": "Makanan & Minuman",
    "mamin": "Makanan & Minuman",
    "rumah tangga": "Rumah Tangga",
    "kesehatan & kecantikan": "Kesehatan & Kecantikan",
    "kesehatan dan kecantikan": "Kesehatan & Kecantikan",
    "olahraga": "Olahraga",
}

# Koreksi manual untuk kategori yang kosong di master produk (asumsi, dicatat di laporan)
kategori_manual = {"P032": "Kesehatan & Kecantikan"}

kategori_tidak_terpetakan = df_produk.loc[
    ~df_produk["kategori"].isin(kategori_mapping) & ~df_produk["id_produk"].isin(kategori_manual),
    "id_produk",
].tolist()
print(f"Produk dengan kategori tidak terpetakan (jadi 'Tidak Diketahui'): {kategori_tidak_terpetakan}")

df_produk["kategori"] = df_produk["kategori"].map(kategori_mapping)
df_produk["kategori"] = (
    df_produk["id_produk"].map(kategori_manual)
    .fillna(df_produk["kategori"])
    .fillna("Tidak Diketahui")
)

# Hapus duplikat berdasarkan id_produk (ambil yang pertama)
df_produk = df_produk.drop_duplicates(subset=["id_produk"]).reset_index(drop=True)

print(f"Jumlah produk unik: {len(df_produk)}")
print(df_produk["kategori"].value_counts())

# Cleaning df_pelanggan
df_pelanggan["id_pelanggan"] = df_pelanggan["id_pelanggan"].astype(str).str.strip()

# Standarisasi nama kota
kota_mapping = {
    "mlg": "Malang",
    "malang": "Malang",
    "kota malang": "Malang",
    "surabaya": "Surabaya",
    "kota surabaya": "Surabaya",
    "sby": "Surabaya",
    "batu": "Batu",
    "kota batu": "Batu",
    "jakarta": "Jakarta",
    "dki jakarta": "Jakarta",
    "sidoarjo": "Sidoarjo",
    "sda": "Sidoarjo",
    "bandung": "Bandung",
    "semarang": "Semarang",
    "kediri": "Kediri",
    "pasuruan": "Pasuruan",
    "blitar": "Blitar",
    "denpasar": "Denpasar",
    "yogyakarta": "Yogyakarta",
}
kota_bersih = df_pelanggan["kota"].astype("string").str.strip().str.lower().replace("", pd.NA)
kota_tidak_terpetakan = kota_bersih.dropna()[~kota_bersih.dropna().isin(kota_mapping)].unique()
print(f"Kota yang tidak terpetakan (jadi 'Tidak Diketahui'): {list(kota_tidak_terpetakan)}")
df_pelanggan["kota"] = kota_bersih.map(kota_mapping).fillna("Tidak Diketahui")

# Standarisasi jenis kelamin
jk_mapping = {
    "l": "Laki-laki", "laki-laki": "Laki-laki", "pria": "Laki-laki",
    "p": "Perempuan", "wanita": "Perempuan", "perempuan": "Perempuan",
}
df_pelanggan["jenis_kelamin"] = (
    df_pelanggan["jenis_kelamin"].astype("string").str.strip().str.lower().map(jk_mapping).fillna("Tidak Diketahui")
)

# Standarisasi nomor telepon (hapus semua karakter selain angka)
df_pelanggan["telepon"] = df_pelanggan["telepon"].astype(str).str.replace(r"[^0-9]", "", regex=True)

# Hapus duplikat id_pelanggan, untuk jaga-jaga
df_pelanggan = df_pelanggan.drop_duplicates(subset=["id_pelanggan"]).reset_index(drop=True)

print(f"Jumlah pelanggan: {len(df_pelanggan)}")

# Standarisasi metode bayar (harus rapi dulu sebelum dijadikan dimensi sendiri)
metode_mapping = {
    "tunai": "Tunai",
    "qris": "QRIS",
    "transfer": "Transfer",
    "debit": "Debit",
}
df_penjualan["metode_bayar"] = (
    df_penjualan["metode_bayar"]
    .astype("string")
    .str.strip()
    .str.lower()
    .map(metode_mapping)
    .fillna("Tidak Diketahui")
)

# Buat Tabel Dimensi
tanggal_unik = df_penjualan["tanggal"].drop_duplicates().sort_values()

# Dimensi Waktu
dim_waktu = pd.DataFrame({
    "tanggal": tanggal_unik,
    "hari": tanggal_unik.dt.day,
    "nama_hari": tanggal_unik.dt.day_name(),
    "bulan": tanggal_unik.dt.month,
    "nama_bulan": tanggal_unik.dt.month_name(),
    "kuartal": tanggal_unik.dt.quarter,
    "tahun": tanggal_unik.dt.year,
}).reset_index(drop=True)

# SURROGATE KEY (sk_waktu, sk_produk, sk_pelanggan, sk_metode_bayar) DIBENTUK DI SINI:
dim_waktu.insert(0, "sk_waktu", dim_waktu.index + 1)

# Dimensi Produk
dim_produk = df_produk[["id_produk", "nama_produk", "kategori", "merek"]].copy()
dim_produk.insert(0, "sk_produk", dim_produk.index + 1)

# PRODUK YANG TIDAK TERDAFTAR DI MASTER (orphan child data)
# Transaksi dengan id_produk yang tidak ada di produk.xlsx TIDAK dibuang.
# ID-nya didaftarkan sebagai produk baru di dim_produk dengan atribut
# "Tidak Diketahui" (inferred member), sehingga total penjualan tetap utuh
# dan datanya mudah dilengkapi nanti (cukup UPDATE barisnya).
id_orphan_produk = sorted(set(df_penjualan["id_produk"]) - set(dim_produk["id_produk"]))
if id_orphan_produk:
    produk_baru = pd.DataFrame({
        "id_produk": id_orphan_produk,
        "nama_produk": [
            "Produk Tidak Diketahui" if i == "P_UNKNOWN" else f"Produk Tidak Terdaftar ({i})"
            for i in id_orphan_produk
        ],
        "kategori": "Tidak Diketahui",
        "merek": "Tidak Diketahui",
    })
    produk_baru.insert(0, "sk_produk", range(len(dim_produk) + 1, len(dim_produk) + len(produk_baru) + 1))
    dim_produk = pd.concat([dim_produk, produk_baru], ignore_index=True)
    jml_trx = df_penjualan["id_produk"].isin(id_orphan_produk).sum()
    print(f"Produk tidak terdaftar ditambahkan ke dim_produk: {id_orphan_produk} ({jml_trx} transaksi dipertahankan)")

# Dimensi Pelanggan
dim_pelanggan = df_pelanggan[["id_pelanggan", "nama", "jenis_kelamin", "kota", "provinsi"]].copy()
dim_pelanggan.insert(0, "sk_pelanggan", dim_pelanggan.index + 1)

# PELANGGAN YANG TIDAK TERDAFTAR DI MASTER (ID kosong atau tidak ada di master)
# Pendekatan sama seperti produk: didaftarkan sebagai inferred member
# agar transaksinya tetap masuk ke tabel fakta.
id_orphan_pelanggan = sorted(set(df_penjualan["id_pelanggan"]) - set(dim_pelanggan["id_pelanggan"]))
if id_orphan_pelanggan:
    pelanggan_baru = pd.DataFrame({
        "id_pelanggan": id_orphan_pelanggan,
        "nama": [
            "Pelanggan Tidak Diketahui" if i == "C_UNKNOWN" else f"Pelanggan Tidak Terdaftar ({i})"
            for i in id_orphan_pelanggan
        ],
        "jenis_kelamin": "Tidak Diketahui",
        "kota": "Tidak Diketahui",
        "provinsi": "Tidak Diketahui",
    })
    pelanggan_baru.insert(0, "sk_pelanggan", range(len(dim_pelanggan) + 1, len(dim_pelanggan) + len(pelanggan_baru) + 1))
    dim_pelanggan = pd.concat([dim_pelanggan, pelanggan_baru], ignore_index=True)
    jml_trx = df_penjualan["id_pelanggan"].isin(id_orphan_pelanggan).sum()
    print(f"Pelanggan tidak terdaftar ditambahkan ke dim_pelanggan: {id_orphan_pelanggan} ({jml_trx} transaksi dipertahankan)")

# Dimensi Metode Bayar (sebelumnya hanya atribut teks di tabel fakta)
dim_metode_bayar = (
    df_penjualan[["metode_bayar"]]
    .drop_duplicates()
    .sort_values("metode_bayar")
    .reset_index(drop=True)
)
dim_metode_bayar.insert(0, "sk_metode_bayar", dim_metode_bayar.index + 1)

# Buat Tabel Fakta
fakta = df_penjualan.copy()

# Pengaman: setelah inferred member, tidak boleh ada transaksi yang terbuang
sebelum = len(fakta)
fakta = fakta[fakta["id_produk"].isin(dim_produk["id_produk"])]
fakta = fakta[fakta["id_pelanggan"].isin(dim_pelanggan["id_pelanggan"])]
print(f"Transaksi dibuang karena id tidak terdaftar di dimensi: {sebelum - len(fakta)} baris")
assert sebelum == len(fakta), "Masih ada transaksi dengan id yang tidak terdaftar di dimensi"

# SURROGATE KEY DIPETAKAN KE TABEL FAKTA
fakta = fakta.merge(dim_waktu[["sk_waktu", "tanggal"]], on="tanggal", how="left")
fakta = fakta.merge(dim_produk[["sk_produk", "id_produk"]], on="id_produk", how="left")
fakta = fakta.merge(dim_pelanggan[["sk_pelanggan", "id_pelanggan"]], on="id_pelanggan", how="left")
fakta = fakta.merge(dim_metode_bayar[["sk_metode_bayar", "metode_bayar"]], on="metode_bayar", how="left")

# Hitung total penjualan
fakta["total_penjualan"] = fakta["qty"] * fakta["harga_satuan"]

# Pilih kolom sesuai star schema
# (metode_bayar tidak lagi disimpan di fakta, diganti foreign key sk_metode_bayar)
fakta_penjualan = fakta[[
    "id_transaksi", "sk_waktu", "sk_produk", "sk_pelanggan", "sk_metode_bayar",
    "qty", "harga_satuan", "total_penjualan"
]]

# Validasi hasil transform
assert fakta_penjualan.isna().sum().sum() == 0, "Ada nilai kosong (surrogate key) di tabel fakta"
assert fakta_penjualan["id_transaksi"].is_unique, "Ada id_transaksi ganda di tabel fakta"
assert len(fakta_penjualan) == len(df_penjualan), "Jumlah baris fakta tidak sama dengan hasil cleaning"

print(f"Jumlah transaksi di fakta: {len(fakta_penjualan)}")

# Simpan hasil transform supaya bisa dipakai 3_load.py
dim_waktu.to_csv("temp_dim_waktu.csv", index=False)
dim_produk.to_csv("temp_dim_produk.csv", index=False)
dim_pelanggan.to_csv("temp_dim_pelanggan.csv", index=False)
dim_metode_bayar.to_csv("temp_dim_metode_bayar.csv", index=False)
fakta_penjualan.to_csv("temp_fakta_penjualan.csv", index=False)
print("✅ Data hasil transform berhasil di-export sementara.")
