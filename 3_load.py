import pandas as pd

dim_waktu = pd.read_csv("temp_dim_waktu.csv")
dim_produk = pd.read_csv("temp_dim_produk.csv")
dim_pelanggan = pd.read_csv("temp_dim_pelanggan.csv")
fakta_penjualan = pd.read_csv("temp_fakta_penjualan.csv")

from sqlalchemy import create_engine
engine_target = create_engine("mysql+pymysql://root:@localhost:3306/tokomain_dw")

dim_waktu.to_sql("dim_waktu", engine_target, if_exists="replace", index=False)
dim_produk.to_sql("dim_produk", engine_target, if_exists="replace", index=False)
dim_pelanggan.to_sql("dim_pelanggan", engine_target, if_exists="replace", index=False)
fakta_penjualan.to_sql("fakta_penjualan", engine_target, if_exists="replace", index=False)

print("✅ Semua tabel berhasil di-load ke MySQL!")