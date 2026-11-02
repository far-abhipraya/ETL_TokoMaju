-- ============================================================================
-- SKRIP VALIDASI & ANALISIS DATA WAREHOUSE (tokomain_dw)
-- Proyek: Pipeline ETL Toko Ritel "TokoMaju" (Kelompok 3)
-- ============================================================================

USE tokomain_dw;

-- ============================================================================
-- 1. VALIDASI JUMLAH BARIS (ROW COUNT)
-- Memastikan jumlah baris di setiap tabel sesuai dengan hasil tahap transform:
-- dim_waktu (363), dim_produk (40), dim_pelanggan (180), fakta_penjualan (2.282)
-- ============================================================================
SELECT 'dim_waktu' AS tabel, COUNT(*) AS jumlah FROM dim_waktu
UNION ALL
SELECT 'dim_produk', COUNT(*) FROM dim_produk
UNION ALL
SELECT 'dim_pelanggan', COUNT(*) FROM dim_pelanggan
UNION ALL
SELECT 'fakta_penjualan', COUNT(*) FROM fakta_penjualan;


-- ============================================================================
-- 2. VALIDASI INTEGRITAS RELASI STAR SCHEMA (JOIN SAMPLE)
-- Memastikan tabel fakta terhubung dengan benar ke ketiga tabel dimensi
-- ============================================================================
SELECT
    f.id_transaksi,
    w.tanggal,
    w.nama_bulan,
    w.tahun,
    p.nama_produk,
    p.kategori,
    c.nama AS nama_pelanggan,
    c.kota,
    f.qty,
    f.harga_satuan,
    f.total_penjualan,
    f.metode_bayar
FROM fakta_penjualan f
JOIN dim_waktu w ON f.id_waktu = w.id_waktu
JOIN dim_produk p ON f.id_produk = p.id_produk
JOIN dim_pelanggan c ON f.id_pelanggan = c.id_pelanggan
LIMIT 10;


-- ============================================================================
-- 3. QUERY ANALISIS: TOTAL PENJUALAN PER KATEGORI PER BULAN
-- Menghitung frekuensi transaksi dan total omzet tiap kategori produk per bulan
-- ============================================================================
SELECT 
    w.tahun,
    w.bulan,
    w.nama_bulan,
    p.kategori,
    COUNT(f.id_transaksi) AS jumlah_transaksi,
    SUM(f.total_penjualan) AS total_penjualan_rupiah
FROM fakta_penjualan f
JOIN dim_waktu w ON f.id_waktu = w.id_waktu
JOIN dim_produk p ON f.id_produk = p.id_produk
GROUP BY 
    w.tahun, 
    w.bulan, 
    w.nama_bulan, 
    p.kategori
ORDER BY 
    w.tahun ASC, 
    w.bulan ASC, 
    total_penjualan_rupiah DESC;


-- ============================================================================
-- 4. VERIFIKASI REKONSILIASI OMZET (AGREGASI VS FAKTA ASLI)
-- Memastikan tidak ada nilai transaksi yang terduplikasi atau hilang saat JOIN & GROUP BY
-- Target nilai yang diharapkan: Rp 446.380.700
-- ============================================================================

-- 4a. Total Hasil Agregasi (menggunakan subquery dari query analisis)
SELECT SUM(total_penjualan_rupiah) AS total_hasil_agregasi FROM (
    SELECT SUM(f.total_penjualan) AS total_penjualan_rupiah
    FROM fakta_penjualan f
    JOIN dim_waktu w ON f.id_waktu = w.id_waktu
    JOIN dim_produk p ON f.id_produk = p.id_produk
    GROUP BY w.tahun, w.bulan, p.kategori
) AS subquery;

-- 4b. Total Fakta Asli (menghitung langsung dari tabel fakta_penjualan)
SELECT SUM(total_penjualan) AS total_fakta_asli FROM fakta_penjualan;