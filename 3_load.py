import pandas as pd
from sqlalchemy import create_engine, text, types
from sqlalchemy.dialects.mysql import YEAR

# ----------------------------------------------------------------------
# Koneksi ke database target
# ----------------------------------------------------------------------
engine_target = create_engine("mysql+pymysql://root:@localhost:3306/tokomain_dw")

# ----------------------------------------------------------------------
# Baca hasil transform
# ----------------------------------------------------------------------
dim_waktu = pd.read_csv("temp_dim_waktu.csv")
dim_produk = pd.read_csv("temp_dim_produk.csv")
dim_pelanggan = pd.read_csv("temp_dim_pelanggan.csv")
fakta_penjualan = pd.read_csv("temp_fakta_penjualan.csv")

# ----------------------------------------------------------------------
# Bersihkan tabel lama jika sudah ada (mencegah error Foreign Key saat replace)
# ----------------------------------------------------------------------
with engine_target.connect() as conn:
    conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
    conn.execute(text("DROP TABLE IF EXISTS fakta_penjualan;"))
    conn.execute(text("DROP TABLE IF EXISTS dim_waktu;"))
    conn.execute(text("DROP TABLE IF EXISTS dim_produk;"))
    conn.execute(text("DROP TABLE IF EXISTS dim_pelanggan;"))
    conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
    conn.commit()

# ----------------------------------------------------------------------
# Load dim_waktu
# ----------------------------------------------------------------------
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

# ----------------------------------------------------------------------
# Load dim_produk
# ----------------------------------------------------------------------
dim_produk.to_sql(
    "dim_produk",
    engine_target,
    if_exists="replace",
    index=False,
    dtype={
        "sk_produk": types.INTEGER(),
        "id_produk": types.VARCHAR(10),
        "nama_produk": types.VARCHAR(100),
        "kategori": types.VARCHAR(50),
        "merek": types.VARCHAR(50),
    }
)

# ----------------------------------------------------------------------
# Load dim_pelanggan
# ----------------------------------------------------------------------
dim_pelanggan.to_sql(
    "dim_pelanggan",
    engine_target,
    if_exists="replace",
    index=False,
    dtype={
        "sk_pelanggan": types.INTEGER(),
        "id_pelanggan": types.VARCHAR(10),
        "nama": types.VARCHAR(100),
        "jenis_kelamin": types.VARCHAR(15),
        "kota": types.VARCHAR(50),
        "provinsi": types.VARCHAR(50),
    }
)

# ----------------------------------------------------------------------
# Load fakta_penjualan
# ----------------------------------------------------------------------
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
        "qty": types.INTEGER(),
        "harga_satuan": types.DECIMAL(12, 2),
        "total_penjualan": types.DECIMAL(14, 2),
        "metode_bayar": types.VARCHAR(20),
    }
)

print("✅ Semua tabel berhasil di-load ke MySQL dengan tipe data yang sesuai!")

# ----------------------------------------------------------------------
# Tambahkan Primary Key & Foreign Key
# ----------------------------------------------------------------------
with engine_target.connect() as conn:
    # Primary Key tiap tabel dimensi
    conn.execute(text("ALTER TABLE dim_waktu ADD PRIMARY KEY (sk_waktu)"))
    conn.execute(text("ALTER TABLE dim_produk ADD PRIMARY KEY (sk_produk)"))
    conn.execute(text("ALTER TABLE dim_pelanggan ADD PRIMARY KEY (sk_pelanggan)"))

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

    conn.commit()

print("✅ Primary Key & Foreign Key berhasil ditambahkan!")