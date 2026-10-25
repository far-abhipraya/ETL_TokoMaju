import pandas as pd
from sqlalchemy import create_engine

# --- Extract CSV ---
df_penjualan = pd.read_csv("penjualan.csv", sep=";")
print("=== PENJUALAN ===")
print(df_penjualan.head())
print(df_penjualan.shape)

# --- Extract Excel ---
df_produk = pd.read_excel("produk.xlsx", engine="openpyxl")
print("\n=== PRODUK ===")
print(df_produk.head())
print(df_produk.shape)

# --- Extract dari MySQL ---
engine_sumber = create_engine("mysql+pymysql://root:@localhost:3306/tokomaju_oltp")
df_pelanggan = pd.read_sql("SELECT * FROM pelanggan", engine_sumber)
print("\n=== PELANGGAN ===")
print(df_pelanggan.head())
print(df_pelanggan.shape)

# Simpan hasil extract supaya bisa dipakai file berikutnya
df_penjualan.to_csv("temp_penjualan.csv", index=False)
df_produk.to_csv("temp_produk.csv", index=False)
df_pelanggan.to_csv("temp_pelanggan.csv", index=False)
print("✅ Data berhasil di-export sementara.")