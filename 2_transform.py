import pandas as pd

# Baca kembali hasil extract
df_penjualan = pd.read_csv("temp_penjualan.csv")
df_produk = pd.read_csv("temp_produk.csv")
df_pelanggan = pd.read_csv("temp_pelanggan.csv")

# Bersihkan kolom harga_satuan: hapus "Rp", ".", spasi lalu ubah ke angka
jumlah_awal = len(df_penjualan)
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
df_penjualan = df_penjualan.drop_duplicates()

# Hapus baris dengan qty negatif atau nol
df_penjualan = df_penjualan[df_penjualan["qty"] > 0]

# Hapus baris dengan harga tidak valid (NaN setelah konversi)
df_penjualan = df_penjualan.dropna(subset=["harga_satuan", "tanggal"])

print(f"Jumlah transaksi setelah cleaning: {len(df_penjualan)}")

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
df_pelanggan["telepon"] = df_pelanggan["telepon"].str.replace(r"[^0-9]", "", regex=True)

print(f"Jumlah pelanggan: {len(df_pelanggan)}")

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

# Fact Table
fakta = df_penjualan.copy()

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
# Setelah hapus duplikat
df_penjualan = df_penjualan.drop_duplicates()
print(f"Setelah hapus duplikat: {len(df_penjualan)} (hilang {jumlah_awal - len(df_penjualan)})")

# Setelah hapus qty negatif
sebelum = len(df_penjualan)
df_penjualan = df_penjualan[df_penjualan["qty"] > 0]
print(f"Setelah hapus qty negatif/nol: {len(df_penjualan)} (hilang {sebelum - len(df_penjualan)})")

# Setelah hapus harga/tanggal tidak valid
sebelum = len(df_penjualan)
df_penjualan = df_penjualan.dropna(subset=["harga_satuan", "tanggal"])
print(f"Setelah hapus harga/tanggal invalid: {len(df_penjualan)} (hilang {sebelum - len(df_penjualan)})")

# Simpan hasil transform supaya bisa dipakai 3_load.py
dim_waktu.to_csv("temp_dim_waktu.csv", index=False)
dim_produk.to_csv("temp_dim_produk.csv", index=False)
dim_pelanggan.to_csv("temp_dim_pelanggan.csv", index=False)
fakta_penjualan.to_csv("temp_fakta_penjualan.csv", index=False)
print("✅ Data hasil transform berhasil di-export sementara.")