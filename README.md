# ETL TokoMaju — Python + SQLAlchemy + MySQL

Proyek ini membangun pipeline ETL (Extract, Transform, Load) sederhana untuk data toko ritel **TokoMaju**, mengubah data mentah dari tiga sumber (CSV, Excel, dan SQL) menjadi *star schema* (tabel dimensi + tabel fakta) di dalam database MySQL.

## Struktur Proyek

```
ETL_TokoMaju/
│
├── pelanggan.sql        # Dataset sumber: tabel pelanggan (OLTP)
├── penjualan.csv         # Dataset sumber: data transaksi penjualan
├── produk.xlsx            # Dataset sumber: data produk
│
├── 1_extract.py            # Tahap Extract: membaca ketiga sumber data
├── 2_transform.py        # Tahap Transform: cleaning data & membangun star schema
├── 3_load.py                # Tahap Load: menyimpan hasil transform ke MySQL
│
└── README.md
```

> **Catatan:** File `temp_*.csv` yang mungkin muncul di direktori ini adalah file perantara hasil dari `1_extract.py` dan `2_transform.py`, dibuat agar variabel DataFrame bisa "diteruskan" antar script yang dijalankan terpisah. File-file ini bersifat sementara dan di-generate ulang setiap pipeline dijalankan — tidak perlu di-commit ke repository (lihat bagian [Catatan Tambahan](#catatan-tambahan)).

## Arsitektur Pipeline

```
penjualan.csv  ──┐
produk.xlsx     ──┤──► pandas (Extract & Transform) ──► SQLAlchemy ──► MySQL (tokomain_dw)
pelanggan.sql ──┘
```

- **Sumber data mentah** dibaca dari CSV, Excel, dan database MySQL (`tokomaju_oltp`)
- **Proses cleaning & transformasi** dilakukan dengan pandas (standarisasi tanggal, kategori, kota, format telepon, dll)
- **Hasil akhir** berupa 4 tabel (`dim_waktu`, `dim_produk`, `dim_pelanggan`, `fakta_penjualan`) disimpan ke database `tokomain_dw`

## Prasyarat

Pastikan sudah terinstall di laptop:

- [Python 3.x](https://www.python.org/downloads/)
- [MySQL Server](https://dev.mysql.com/downloads/mysql/)
- [DBeaver](https://dbeaver.io/download/) (untuk mengelola database MySQL)

## Langkah-Langkah Menjalankan Pipeline

### 1. Siapkan MySQL via DBeaver

Buka DBeaver, koneksikan ke MySQL Server lokal (`localhost:3306`), lalu buat dua database baru dengan menjalankan query berikut di SQL Editor:

```sql
CREATE DATABASE tokomaju_oltp;   -- untuk data sumber (pelanggan)
CREATE DATABASE tokomain_dw;     -- untuk hasil akhir ETL (star schema)
```

### 2. Import Data Pelanggan ke `tokomaju_oltp`

Masih di DBeaver:
- Klik kanan pada database `tokomaju_oltp` → **SQL Editor** → **New SQL Script**
- Buka file `pelanggan.sql`, copy seluruh isinya, paste ke editor, lalu jalankan (Execute Script)

Atau jalankan via terminal:
```bash
mysql -u root -p tokomaju_oltp < pelanggan.sql
```

Setelah ini, tabel `pelanggan` akan tersedia di database `tokomaju_oltp`.

### 3. Install Library Python yang Dibutuhkan

Buka terminal di direktori proyek ini, lalu jalankan:

```bash
pip install pandas openpyxl sqlalchemy pymysql
```

### 4. Sesuaikan Koneksi Database di Script

Buka `1_extract.py` dan `3_load.py`, pastikan connection string MySQL sesuai dengan konfigurasi lokal masing-masing (username, password, host, port). Contoh untuk MySQL tanpa password:

```python
create_engine("mysql+pymysql://root:@localhost:3306/tokomaju_oltp")
```

### 5. Jalankan Pipeline Secara Berurutan

```bash
python 1_extract.py
python 2_transform.py
python 3_load.py
```

- `1_extract.py` → membaca data dari CSV, Excel, dan MySQL, lalu menyimpan sementara sebagai `temp_*.csv`
- `2_transform.py` → membaca `temp_*.csv`, membersihkan data, membangun tabel dimensi & fakta, menyimpan hasil sebagai `temp_dim_*.csv` dan `temp_fakta_penjualan.csv`
- `3_load.py` → membaca hasil transform, lalu memuatnya ke database `tokomain_dw`

### 6. Verifikasi Hasil di DBeaver

Jalankan query berikut di database `tokomain_dw` untuk memastikan data sudah masuk dengan benar:

```sql
-- Cek jumlah baris tiap tabel
SELECT COUNT(*) FROM dim_waktu;
SELECT COUNT(*) FROM dim_produk;
SELECT COUNT(*) FROM dim_pelanggan;
SELECT COUNT(*) FROM fakta_penjualan;

-- Cek sample data gabungan
SELECT
    f.id_transaksi,
    w.tanggal, w.nama_bulan, w.tahun,
    p.nama_produk, p.kategori,
    c.nama AS nama_pelanggan, c.kota,
    f.qty, f.harga_satuan, f.total_penjualan, f.metode_bayar
FROM fakta_penjualan f
JOIN dim_waktu w ON f.id_waktu = w.id_waktu
JOIN dim_produk p ON f.id_produk = p.id_produk
JOIN dim_pelanggan c ON f.id_pelanggan = c.id_pelanggan
LIMIT 10;
```

## Masalah Data yang Ditangani pada Tahap Transform

| Sumber | Masalah | Penanganan |
|---|---|---|
| `penjualan.csv` | Format tanggal campur (`YYYY-MM-DD`, `DD/MM/YYYY`, `DD-MM-YYYY`, `21 Sep 2025`) | Distandarisasi dengan `pd.to_datetime` |
| `penjualan.csv` | Qty negatif | Baris dengan qty ≤ 0 dibuang |
| `penjualan.csv` | Harga satuan berformat teks (`Rp85.000`) | Dibersihkan & dikonversi ke numerik |
| `penjualan.csv` | Data duplikat | Dihapus dengan `drop_duplicates()` |
| `produk.xlsx` | ID produk duplikat | Diambil satu kemunculan pertama |
| `produk.xlsx` | Nama kategori tidak konsisten (`Mamin`, `KESEHATAN & KECANTIKAN`, dll) | Distandarisasi lewat mapping kategori |
| `produk.xlsx` | Spasi berlebih pada nama produk | Dibersihkan dengan `.str.strip()` |
| `pelanggan.sql` | Nilai kota kosong/NULL | Diisi `"Tidak Diketahui"` |
| `pelanggan.sql` | Nama kota tidak konsisten (`Mlg`, `MALANG`, `Kota Malang`) | Distandarisasi lewat mapping kota |
| `pelanggan.sql` | Format jenis kelamin tidak konsisten (`L`, `Pria`, `Laki-laki`) | Distandarisasi menjadi `Laki-laki` / `Perempuan` |
| `pelanggan.sql` | Format nomor telepon beragam | Dibersihkan menjadi angka saja |

## Catatan Tambahan

File `temp_*.csv` yang dihasilkan saat pipeline dijalankan **tidak perlu disertakan** di repository karena sifatnya sementara dan bisa dibuat ulang kapan saja dengan menjalankan ulang pipeline. Untuk mengecualikannya dari Git, tambahkan baris berikut ke file `.gitignore`:

```
temp_*.csv
```

Jika file-file tersebut sudah terlanjur ter-push ke GitHub, hapus dari tracking Git (tanpa menghapus file lokal) dengan:

```bash
git rm --cached temp_*.csv
git commit -m "Hapus file temporary dari tracking"
git push
```

## Anggota Kelompok

| Nama | Peran (PIC) |
|---|---|
| Alfarel Abhipraya | Instalasi & Konfigurasi |
| Fatih Ahmad Reza El N | Extract |
| Ferry Abdurahman | Transform — Data Cleaning |
| Satria Zaki Mahendrata | Transform — Dimensi & Fakta |
| Ahsan Faqih | Load & Validasi |

*(Catatan: seluruh anggota mengerjakan semua bagian pipeline; pembagian di atas hanya sebagai acuan PIC saat presentasi)*
