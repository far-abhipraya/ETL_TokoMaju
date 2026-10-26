import pandas as pd

# Baca kembali hasil extract
df_penjualan = pd.read_csv("temp_penjualan.csv")
df_produk = pd.read_csv("temp_produk.csv")
df_pelanggan = pd.read_csv("temp_pelanggan.csv")

jumlah_awal = len(df_penjualan)

# Cleaning df_penjualan
# Bersihkan spasi di kolom id (PENTING agar bisa match dengan id di tabel dimensi)
df_penjualan["id_produk"] = df_penjualan["id_produk"].astype(str).str.strip()
df_penjualan["id_pelanggan"] = df_penjualan["id_pelanggan"].astype(str).str.strip()

# Bersihkan kolom harga_satuan: hapus "Rp", ".", spasi lalu ubah ke angka
df_penjualan["harga_satuan"] = (
    df_penjualan["harga_satuan"]
    .astype(str)
    .str.replace("Rp", "", regex=False)
    .str.replace(".", "", regex=False)
    .str.strip()
)
df_penjualan["harga_satuan"] = pd.to_numeric(df_penjualan["harga_satuan"], errors="coerce")

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
print(f"Setelah hapus harga/tanggal invalid: {len(df_penjualan)} (hilang {sebelum - len(df_penjualan)})")

print(f"Jumlah transaksi setelah cleaning: {len(df_penjualan)} (dari awal {jumlah_awal})")

# Cleaning df_produk
# Bersihkan spasi di id_produk juga (bukan cuma nama_produk)
df_produk["id_produk"] = df_produk["id_produk"].astype(str).str.strip()

# Bersihkan spasi di nama_produk
df_produk["nama_produk"] = df_produk["nama_produk"].str.strip()

# Standarisasi kategori
df_produk["kategori"] = df_produk["kategori"].str.strip().str.lower()

# Mapping kategori yang tidak konsisten ke nama standar
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
df_produk["kategori"] = df_produk["kategori"].map(kategori_mapping).fillna("Lainnya")

# Hapus duplikat berdasarkan id_produk (ambil yang pertama)
df_produk = df_produk.drop_duplicates(subset=["id_produk"]).reset_index(drop=True)

print(f"Jumlah produk unik: {len(df_produk)}")
print(df_produk["kategori"].value_counts())

# Cleaning df_pelanggan
# Bersihkan spasi di id_pelanggan juga
df_pelanggan["id_pelanggan"] = df_pelanggan["id_pelanggan"].astype(str).str.strip()

# Ganti string kosong dengan NaN dulu
df_pelanggan["kota"] = df_pelanggan["kota"].replace("", None)

# Standarisasi nama kota
kota_mapping = {
    "mlg": "Malang",
    "malang": "Malang",
    "malang ": "Malang",
    "malang  ": "Malang",
    "kota malang": "Malang",
    "surabaya": "Surabaya",
    "kota surabaya": "Surabaya",
    "sby": "Surabaya",
    "batu": "Batu",
    "kota batu": "Batu",
    "jakarta": "Jakarta",
    "dki jakarta": "Jakarta",
    "sidoarjo": "Sidoarjo",
    "bandung": "Bandung",
    "semarang": "Semarang",
    "kediri": "Kediri",
    "pasuruan": "Pasuruan",
    "blitar": "Blitar",
    "denpasar": "Denpasar",
    "sda": "Sidoarjo",
    "yogyakarta": "Yogyakarta",
}
df_pelanggan["kota"] = (
    df_pelanggan["kota"]
    .str.strip()
    .str.lower()
    .map(kota_mapping)
    .fillna("Tidak Diketahui")
)

# Standarisasi jenis kelamin
df_pelanggan["jenis_kelamin"] = df_pelanggan["jenis_kelamin"].str.strip().str.lower()
jk_mapping = {
    "l": "Laki-laki", "laki-laki": "Laki-laki", "pria": "Laki-laki",
    "p": "Perempuan", "wanita": "Perempuan", "perempuan": "Perempuan",
}
df_pelanggan["jenis_kelamin"] = df_pelanggan["jenis_kelamin"].map(jk_mapping).fillna("Tidak Diketahui")

# Standarisasi nomor telepon (hapus semua karakter selain angka)
df_pelanggan["telepon"] = df_pelanggan["telepon"].astype(str).str.replace(r"[^0-9]", "", regex=True)

# Hapus duplikat id_pelanggan juga, untuk jaga-jaga
df_pelanggan = df_pelanggan.drop_duplicates(subset=["id_pelanggan"]).reset_index(drop=True)

print(f"Jumlah pelanggan: {len(df_pelanggan)}")

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
dim_waktu.insert(0, "id_waktu", dim_waktu.index + 1)

# Dimensi Produk
dim_produk = df_produk[["id_produk", "nama_produk", "kategori", "merek"]].copy()

# Dimensi Pelanggan
dim_pelanggan = df_pelanggan[["id_pelanggan", "nama", "jenis_kelamin", "kota", "provinsi"]].copy()

# Buat Tabel Fakta
fakta = df_penjualan.copy()

# PENTING: buang transaksi yang id_produk atau id_pelanggan-nya
# tidak terdaftar di tabel dimensi (mencegah error Foreign Key saat load)
sebelum = len(fakta)
fakta = fakta[fakta["id_produk"].isin(dim_produk["id_produk"])]
fakta = fakta[fakta["id_pelanggan"].isin(dim_pelanggan["id_pelanggan"])]
print(f"Buang transaksi dengan id_produk/id_pelanggan tidak valid: {sebelum - len(fakta)} baris dihapus")

# Gabungkan dengan dim_waktu untuk dapat id_waktu
fakta = fakta.merge(dim_waktu[["id_waktu", "tanggal"]], on="tanggal", how="left")

# Hitung total penjualan
fakta["total_penjualan"] = fakta["qty"] * fakta["harga_satuan"]

# Pilih kolom sesuai star schema
fakta_penjualan = fakta[[
    "id_transaksi", "id_waktu", "id_produk", "id_pelanggan",
    "qty", "harga_satuan", "total_penjualan", "metode_bayar"
]]

print(f"Jumlah transaksi di fakta: {len(fakta_penjualan)}")

# Simpan hasil transform supaya bisa dipakai 3_load.py
dim_waktu.to_csv("temp_dim_waktu.csv", index=False)
dim_produk.to_csv("temp_dim_produk.csv", index=False)
dim_pelanggan.to_csv("temp_dim_pelanggan.csv", index=False)
fakta_penjualan.to_csv("temp_fakta_penjualan.csv", index=False)
print("✅ Data hasil transform berhasil di-export sementara.")