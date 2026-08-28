-- Query 1: Tampilkan 2 produk elektronik (kategori 1) termahal yang stoknya masih ada
SELECT name, price, stock_quantity
FROM products
WHERE stock_quantity > 0 AND category_id = 1
ORDER BY price DESC
LIMIT 2;

-- Query 2: Tampilkan semua pesanan beserta produk-produknya (JOIN Many-to-Many)
-- Menunjukkan hubungan orders <-> products melalui order_items
SELECT 
    o.id AS order_id,
    u.username AS customer,
    o.status,
    o.total_amount,
    p.name AS product_name,
    oi.quantity,
    oi.price_at_purchase
FROM orders o
JOIN users u ON o.user_id = u.id
JOIN order_items oi ON o.id = oi.order_id
JOIN products p ON oi.product_id = p.id
ORDER BY o.id;

-- Query 3: Tampilkan produk yang pernah dipesan oleh lebih dari satu order (Many-to-Many proof)
SELECT 
    p.name AS product_name,
    COUNT(DISTINCT oi.order_id) AS total_orders
FROM products p
JOIN order_items oi ON p.id = oi.product_id
GROUP BY p.name
HAVING COUNT(DISTINCT oi.order_id) >= 1
ORDER BY total_orders DESC;
