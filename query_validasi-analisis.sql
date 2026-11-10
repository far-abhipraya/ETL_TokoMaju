USE tokomain_dw;

-- Cek awal: total harus sama dengan hasil validasi (Rp 465.542.900, 2.376 transaksi)
SELECT COUNT(*) AS jumlah_transaksi,
       SUM(total_penjualan) AS total_penjualan
FROM fakta_penjualan;


-- Query 1: Total penjualan per kategori per bulan
SELECT w.tahun,
       w.bulan,
       w.nama_bulan,
       p.kategori,
       SUM(f.total_penjualan) AS total_penjualan,
       SUM(f.qty)             AS total_qty
FROM fakta_penjualan f
JOIN dim_waktu  w ON f.sk_waktu  = w.sk_waktu
JOIN dim_produk p ON f.sk_produk = p.sk_produk
GROUP BY w.tahun, w.bulan, w.nama_bulan, p.kategori
ORDER BY w.tahun, w.bulan, total_penjualan DESC;


-- Query 2: 10 produk terlaris berdasarkan total penjualan
SELECT p.id_produk,
       p.nama_produk,
       p.kategori,
       p.merek,
       SUM(f.qty)             AS total_qty,
       SUM(f.total_penjualan) AS total_penjualan
FROM fakta_penjualan f
JOIN dim_produk p ON f.sk_produk = p.sk_produk
GROUP BY p.id_produk, p.nama_produk, p.kategori, p.merek
ORDER BY total_penjualan DESC
LIMIT 10;


-- Query 3: Kontribusi tiap metode pembayaran terhadap total penjualan
SELECT m.metode_bayar,
       COUNT(*)               AS jumlah_transaksi,
       SUM(f.total_penjualan) AS total_penjualan,
       ROUND(SUM(f.total_penjualan) * 100.0 /
             (SELECT SUM(total_penjualan) FROM fakta_penjualan), 2) AS persen_kontribusi
FROM fakta_penjualan f
JOIN dim_metode_bayar m ON f.sk_metode_bayar = m.sk_metode_bayar
GROUP BY m.metode_bayar
ORDER BY total_penjualan DESC;
