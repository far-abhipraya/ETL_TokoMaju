import pandas as pd
from sqlalchemy import create_engine, text, types
from sqlalchemy.dialects.mysql import YEAR

# Koneksi ke database target
engine_target = create_engine("mysql+pymysql://root:@localhost:3306/tokomain_dw")

# Baca hasil transform
dim_waktu = pd.read_csv("temp_dim_waktu.csv", parse_dates=["tanggal"])
dim_produk = pd.read_csv("temp_dim_produk.csv")
dim_pelanggan = pd.read_csv("temp_dim_pelanggan.csv")
dim_metode_bayar = pd.read_csv("temp_dim_metode_bayar.csv")
fakta_penjualan = pd.read_csv("temp_fakta_penjualan.csv")

print(f"Siap di-load: dim_waktu={len(dim_waktu)}, dim_produk={len(dim_produk)}, "
      f"dim_pelanggan={len(dim_pelanggan)}, dim_metode_bayar={len(dim_metode_bayar)}, "
      f"fakta_penjualan={len(fakta_penjualan)}")

# Bersihkan tabel lama jika sudah ada (mencegah error Foreign Key saat load ulang)
with engine_target.connect() as conn:
    conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
    conn.execute(text("DROP TABLE IF EXISTS fakta_penjualan;"))
    conn.execute(text("DROP TABLE IF EXISTS dim_waktu;"))
    conn.execute(text("DROP TABLE IF EXISTS dim_produk;"))
    conn.execute(text("DROP TABLE IF EXISTS dim_pelanggan;"))
    conn.execute(text("DROP TABLE IF EXISTS dim_metode_bayar;"))
    conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
    conn.commit()

# Load dim_waktu
dim_waktu.to_sql(
    "dim_waktu",
    engine_target,
    if_exists="replace",
    index=False,
    dtype={
        "sk_waktu": types.INTEGER(),
        "tanggal": types.DATE(),
        "hari": types.SMALLINT(),
        "nama_hari": types.VARCHAR(15),
        "bulan": types.SMALLINT(),
        "nama_bulan": types.VARCHAR(15),
        "kuartal": types.SMALLINT(),
        "tahun": YEAR(),
    }
)

# Load dim_produk
dim_produk.to_sql(
    "dim_produk",
    engine_target,
    if_exists="replace",
    index=False,
    dtype={
        "sk_produk": types.INTEGER(),
        "id_produk": types.VARCHAR(20),
        "nama_produk": types.VARCHAR(100),
        "kategori": types.VARCHAR(50),
        "merek": types.VARCHAR(50),
    }
)

# Load dim_pelanggan
dim_pelanggan.to_sql(
    "dim_pelanggan",
    engine_target,
    if_exists="replace",
    index=False,
    dtype={
        "sk_pelanggan": types.INTEGER(),
        "id_pelanggan": types.VARCHAR(20),
        "nama": types.VARCHAR(100),
        "jenis_kelamin": types.VARCHAR(20),
        "kota": types.VARCHAR(50),
        "provinsi": types.VARCHAR(50),
    }
)

# Load dim_metode_bayar
dim_metode_bayar.to_sql(
    "dim_metode_bayar",
    engine_target,
    if_exists="replace",
    index=False,
    dtype={
        "sk_metode_bayar": types.INTEGER(),
        "metode_bayar": types.VARCHAR(20),
    }
)

# Load fakta_penjualan (dimensi sudah di-load semua di atas)
fakta_penjualan.to_sql(
    "fakta_penjualan",
    engine_target,
    if_exists="replace",
    index=False,
    dtype={
        "id_transaksi": types.VARCHAR(10),
        "sk_waktu": types.INTEGER(),
        "sk_produk": types.INTEGER(),
        "sk_pelanggan": types.INTEGER(),
        "sk_metode_bayar": types.INTEGER(),
        "qty": types.INTEGER(),
        "harga_satuan": types.DECIMAL(12, 2),
        "total_penjualan": types.DECIMAL(14, 2),
    }
)

print("✅ Semua tabel berhasil di-load ke MySQL dengan tipe data yang sesuai!")

# Tambahkan Primary Key, Unique Key (natural key), dan Foreign Key
with engine_target.connect() as conn:
    # Primary Key tiap tabel dimensi
    conn.execute(text("ALTER TABLE dim_waktu ADD PRIMARY KEY (sk_waktu)"))
    conn.execute(text("ALTER TABLE dim_produk ADD PRIMARY KEY (sk_produk)"))
    conn.execute(text("ALTER TABLE dim_pelanggan ADD PRIMARY KEY (sk_pelanggan)"))
    conn.execute(text("ALTER TABLE dim_metode_bayar ADD PRIMARY KEY (sk_metode_bayar)"))

    # Natural key tidak boleh ganda
    conn.execute(text("ALTER TABLE dim_waktu ADD CONSTRAINT uq_waktu_tanggal UNIQUE (tanggal)"))
    conn.execute(text("ALTER TABLE dim_produk ADD CONSTRAINT uq_produk_id UNIQUE (id_produk)"))
    conn.execute(text("ALTER TABLE dim_pelanggan ADD CONSTRAINT uq_pelanggan_id UNIQUE (id_pelanggan)"))
    conn.execute(text("ALTER TABLE dim_metode_bayar ADD CONSTRAINT uq_metode_bayar UNIQUE (metode_bayar)"))

    # Primary Key tabel fakta
    conn.execute(text("ALTER TABLE fakta_penjualan ADD PRIMARY KEY (id_transaksi)"))

    # Foreign Key dari fakta_penjualan ke masing-masing dimensi
    conn.execute(text("""
        ALTER TABLE fakta_penjualan
        ADD CONSTRAINT fk_waktu FOREIGN KEY (sk_waktu) REFERENCES dim_waktu(sk_waktu)
    """))
    conn.execute(text("""
        ALTER TABLE fakta_penjualan
        ADD CONSTRAINT fk_produk FOREIGN KEY (sk_produk) REFERENCES dim_produk(sk_produk)
    """))
    conn.execute(text("""
        ALTER TABLE fakta_penjualan
        ADD CONSTRAINT fk_pelanggan FOREIGN KEY (sk_pelanggan) REFERENCES dim_pelanggan(sk_pelanggan)
    """))
    conn.execute(text("""
        ALTER TABLE fakta_penjualan
        ADD CONSTRAINT fk_metode_bayar FOREIGN KEY (sk_metode_bayar) REFERENCES dim_metode_bayar(sk_metode_bayar)
    """))

    conn.commit()

print("✅ Primary Key, Unique Key & Foreign Key berhasil ditambahkan!")

# Validasi jumlah baris: data di database harus sama dengan hasil transform
harapan = {
    "dim_waktu": len(dim_waktu),
    "dim_produk": len(dim_produk),
    "dim_pelanggan": len(dim_pelanggan),
    "dim_metode_bayar": len(dim_metode_bayar),
    "fakta_penjualan": len(fakta_penjualan),
}
with engine_target.connect() as conn:
    for tabel, jumlah_harapan in harapan.items():
        jumlah_db = conn.execute(text(f"SELECT COUNT(*) FROM {tabel}")).scalar()
        status = "OK" if jumlah_db == jumlah_harapan else "TIDAK SESUAI"
        print(f"{tabel}: {jumlah_db} baris (harapan {jumlah_harapan}) -> {status}")
        assert jumlah_db == jumlah_harapan, f"Jumlah baris {tabel} tidak sesuai"

    total = conn.execute(text("SELECT SUM(total_penjualan) FROM fakta_penjualan")).scalar()
    print(f"Total penjualan di fakta_penjualan: {total}")

print("✅ Validasi selesai, pipeline ETL berhasil end-to-end!")
