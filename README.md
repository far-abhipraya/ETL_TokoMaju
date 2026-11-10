# ETL TokoMaju — Python + SQLAlchemy + MySQL

Proyek ini membangun pipeline ETL (Extract, Transform, Load) untuk data toko ritel **TokoMaju**. Data mentah dari tiga sumber (CSV, Excel, dan SQL) dibersihkan lalu dimuat sebagai *star schema* (4 tabel dimensi + 1 tabel fakta) di database MySQL, dilengkapi skrip validasi dan query analisis.

## Struktur Proyek

```
ETL_TokoMaju/
│
├── pelanggan.sql               # Dataset sumber: tabel pelanggan (OLTP)
├── penjualan.csv               # Dataset sumber: data transaksi penjualan
├── produk.xlsx                 # Dataset sumber: data produk
│
├── 1_extract.py                # Tahap Extract: membaca ketiga sumber data
├── 2_transform.py              # Tahap Transform: cleaning data & membangun star schema
├── 3_load.py                   # Tahap Load: memuat hasil transform ke MySQL (tipe data, PK, FK)
├── 4_validasi.py               # Verifikasi: rekonsiliasi jumlah baris & total penjualan sebelum vs sesudah ETL
├── query_validasi-analisis.sql # Query cek total dan 3 query analisis (dijalankan di DBeaver)
│
└── README.md
```

> **Catatan:** File `temp_*.csv` adalah file perantara antar script. File ini dibuat ulang setiap pipeline dijalankan dan sudah dikecualikan lewat `.gitignore`.

## Arsitektur Pipeline

```
penjualan.csv  ──┐
produk.xlsx    ──┤──► pandas (Extract & Transform) ──► SQLAlchemy ──► MySQL (tokomain_dw)
pelanggan.sql  ──┘                                                        │
                                                                  4_validasi.py + query analisis
```

- **Sumber data mentah** dibaca dari CSV, Excel, dan database MySQL (`tokomaju_oltp`)
- **Cleaning & transformasi** dilakukan dengan pandas
- **Hasil akhir** disimpan ke database `tokomain_dw`
- **Validasi** membandingkan data mentah dengan isi tabel fakta

## Desain Star Schema

| Tabel | Jenis | Kunci | Isi utama |
|---|---|---|---|
| `fakta_penjualan` | Fakta | PK `id_transaksi`; FK `sk_waktu`, `sk_produk`, `sk_pelanggan`, `sk_metode_bayar` | `qty`, `harga_satuan`, `total_penjualan` |
| `dim_waktu` | Dimensi | PK `sk_waktu` | tanggal, hari, nama hari, bulan, nama bulan, kuartal, tahun |
| `dim_produk` | Dimensi | PK `sk_produk`, natural key `id_produk` | nama produk, kategori, merek |
| `dim_pelanggan` | Dimensi | PK `sk_pelanggan`, natural key `id_pelanggan` | nama, jenis kelamin, kota, provinsi |
| `dim_metode_bayar` | Dimensi | PK `sk_metode_bayar`, natural key `metode_bayar` | Tunai, QRIS, Transfer, Debit |

Setiap dimensi memiliki **surrogate key** (`sk_*`) berupa bilangan bulat berurutan. Tabel fakta menghubungkan transaksi ke dimensi lewat surrogate key tersebut.

## Prasyarat

Pastikan sudah terinstall di laptop:

- [Python 3.x](https://www.python.org/downloads/)
- [MySQL Server](https://dev.mysql.com/downloads/mysql/)
- [DBeaver](https://dbeaver.io/download/) (untuk mengelola database MySQL)

## Langkah-Langkah Menjalankan Pipeline

### 1. Siapkan MySQL via DBeaver

Buka DBeaver, koneksikan ke MySQL Server lokal (`localhost:3306`), lalu buat dua database baru:

```sql
CREATE DATABASE tokomaju_oltp;   -- untuk data sumber (pelanggan)
CREATE DATABASE tokomain_dw;     -- untuk hasil akhir ETL (star schema)
```

### 2. Import Data Pelanggan ke `tokomaju_oltp`

Di DBeaver:
- Klik kanan database `tokomaju_oltp` → **SQL Editor** → **New SQL Script**
- Buka file `pelanggan.sql`, copy seluruh isinya, paste ke editor, lalu jalankan (Execute Script)

Atau lewat terminal:
```bash
mysql -u root -p tokomaju_oltp < pelanggan.sql
```

### 3. Install Library Python

Buka terminal di direktori proyek ini, lalu jalankan:

```bash
pip install pandas openpyxl sqlalchemy pymysql
```

### 4. Sesuaikan Koneksi Database

Buka `1_extract.py`, `3_load.py`, dan `4_validasi.py`, lalu pastikan connection string sesuai konfigurasi lokal (username, password, host, port). Contoh untuk MySQL tanpa password:

```python
create_engine("mysql+pymysql://root:@localhost:3306/tokomaju_oltp")
```

### 5. Jalankan Pipeline Secara Berurutan

```bash
python 1_extract.py
python 2_transform.py
python 3_load.py
python 4_validasi.py
```

- `1_extract.py` → membaca CSV, Excel, dan tabel MySQL, lalu menyimpannya sebagai `temp_*.csv`
- `2_transform.py` → membersihkan data, membangun dimensi dan fakta, lalu menyimpannya sebagai `temp_dim_*.csv` dan `temp_fakta_penjualan.csv`
- `3_load.py` → memuat hasil transform ke `tokomain_dw`, lengkap dengan tipe data, Primary Key, Unique Key, dan Foreign Key, serta mencocokkan jumlah baris tiap tabel
- `4_validasi.py` → merekonsiliasi jumlah baris dan total penjualan sebelum vs sesudah ETL; keluar dengan status `SESUAI` bila seluruh selisih terjelaskan oleh tahap cleaning

> `4_validasi.py` membaca `temp_*.csv`, jadi jalankan setelah tiga script sebelumnya dan jangan hapus file temp sebelum validasi selesai.

### 6. Verifikasi dan Analisis di DBeaver

Buka `query_validasi-analisis.sql` di DBeaver (database `tokomain_dw`). File ini berisi:

- **Cek awal:** jumlah transaksi dan total penjualan (harus 2.376 transaksi dan Rp 465.542.900)
- **Query 1:** total penjualan per kategori per bulan
- **Query 2:** 10 produk terlaris
- **Query 3:** kontribusi tiap metode pembayaran

Contoh query cek relasi antar tabel:

```sql
SELECT
    f.id_transaksi,
    w.tanggal, w.nama_bulan, w.tahun,
    p.nama_produk, p.kategori,
    c.nama AS nama_pelanggan, c.kota,
    m.metode_bayar,
    f.qty, f.harga_satuan, f.total_penjualan
FROM fakta_penjualan f
JOIN dim_waktu w ON f.sk_waktu = w.sk_waktu
JOIN dim_produk p ON f.sk_produk = p.sk_produk
JOIN dim_pelanggan c ON f.sk_pelanggan = c.sk_pelanggan
JOIN dim_metode_bayar m ON f.sk_metode_bayar = m.sk_metode_bayar
LIMIT 10;
```

## Alur Jumlah Data

| Tahap | Dihapus | Sisa baris | Total penjualan |
|---|---|---|---|
| Data mentah | – | 2.445 | Rp 469.154.600 |
| Hapus duplikat | 45 | 2.400 | Rp 461.823.200 |
| Hapus qty ≤ 0 (18 negatif, 6 nol) | 24 | 2.376 | Rp 465.542.900 |
| Tanggal tidak terbaca | 0 | 2.376 | Rp 465.542.900 |
| ID pelanggan kosong dan produk orphan | 0 (dipertahankan) | 2.376 | Rp 465.542.900 |

Hasil akhir: **2.376 transaksi** dengan total **Rp 465.542.900** (turun 0,77% dari total mentah). Total mentah adalah nilai bersih yang sudah memuat pengurang dari qty negatif.

## Masalah Data yang Ditangani pada Tahap Transform

| Sumber | Masalah | Penanganan |
|---|---|---|
| `penjualan.csv` | Format tanggal campur (`YYYY-MM-DD`, `DD/MM/YYYY`, `DD-MM-YYYY`, `21 Sep 2025`) | Distandarisasi dengan `pd.to_datetime` |
| `penjualan.csv` | Nama bulan bahasa Indonesia (`Mei`, `Agu`, `Okt`, `Des`) tidak dikenali pandas | Diterjemahkan ke bahasa Inggris sebelum diparse (mencegah 61 transaksi terbuang) |
| `penjualan.csv` | Qty negatif atau nol | Baris dengan qty ≤ 0 dibuang (24 baris) |
| `penjualan.csv` | Harga satuan berformat teks (`Rp85.000`) | Dibersihkan dan dikonversi ke numerik |
| `penjualan.csv` | Data duplikat | Dihapus dengan `drop_duplicates()` (45 baris) |
| `penjualan.csv` | `id_pelanggan` kosong (25 transaksi) | Dipetakan ke anggota `C_UNKNOWN` ("Pelanggan Tidak Diketahui") |
| `penjualan.csv` | `id_produk` tidak ada di master (P077, P099, P120, X001; 9 transaksi) | Didaftarkan sebagai *inferred member* di `dim_produk` dengan atribut "Tidak Diketahui" |
| `produk.xlsx` | ID produk duplikat (P013, P017, P024) | Diambil satu kemunculan pertama |
| `produk.xlsx` | Nama kategori tidak konsisten (`Mamin`, `KESEHATAN & KECANTIKAN`, dll) | Distandarisasi lewat mapping kategori |
| `produk.xlsx` | Spasi berlebih pada ID, nama produk, dan kategori | Dibersihkan dengan `.str.strip()` |
| `produk.xlsx` | Kategori P032 kosong | Diisi manual "Kesehatan & Kecantikan" (asumsi, merek sama dengan produk di kategori tersebut) |
| `pelanggan.sql` | Nilai kota kosong/NULL | Diisi "Tidak Diketahui" |
| `pelanggan.sql` | Nama kota tidak konsisten (`Mlg`, `MALANG`, `Kota Malang`) | Distandarisasi lewat mapping kota |
| `pelanggan.sql` | Format jenis kelamin tidak konsisten (`L`, `Pria`, `Laki-laki`) | Distandarisasi menjadi `Laki-laki` / `Perempuan` |
| `pelanggan.sql` | Format nomor telepon beragam | Dibersihkan menjadi angka saja |

Transform juga menjalankan pengecekan otomatis (`assert`): tidak ada transaksi yang terbuang karena ID tidak terdaftar, tidak ada surrogate key kosong di tabel fakta, dan `id_transaksi` unik.

## Catatan Tambahan

- File `temp_*.csv` tidak perlu di-commit (sudah ada di `.gitignore`). Bila sudah terlanjur ter-push, hapus dari tracking Git:

```bash
git rm --cached temp_*.csv
git commit -m "Hapus file temporary dari tracking"
git push
```

- Folder `__pycache__` juga tidak perlu di-commit. Tambahkan `__pycache__/` ke `.gitignore`, lalu jalankan `git rm -r --cached __pycache__`.

## Anggota Kelompok

| Nama | Peran (PIC) |
|---|---|
| Alfarel Abhipraya | Instalasi & Konfigurasi |
| Fatih Ahmad Reza El N | Extract |
| Ferry Abdurahman | Transform — Data Cleaning |
| Satria Zaki Mahendrata | Transform — Dimensi & Fakta |
| Ahsan Faqih | Load & Validasi |

*(Catatan: seluruh anggota mengerjakan semua bagian pipeline; pembagian di atas hanya sebagai acuan PIC saat presentasi)*
