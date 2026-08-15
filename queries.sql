-- Tampilkan 2 produk elektronik (kategori 1) termahal yang stoknya masih ada
SELECT name, price, stock_quantity
FROM products
WHERE stock_quantity > 0 AND category_id = 1
ORDER BY price DESC
LIMIT 2;