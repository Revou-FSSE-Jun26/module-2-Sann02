-- Insert Users (dengan username, email, password_hash sesuai model)
INSERT INTO users (username, email, password_hash, role) VALUES
('ikhsan', 'ikhsan@email.com', 'hashed_password_1', 'user'),
('budi', 'budi@email.com', 'hashed_password_2', 'user');

-- Insert Categories
INSERT INTO categories (name, description) VALUES
('Elektronik', 'Barang elektronik dan gadget'),
('Pakaian', 'Pakaian pria dan wanita');

-- Insert Products
INSERT INTO products (category_id, name, description, price, stock_quantity) VALUES
(1, 'Acer Aspire 3', 'Laptop AMD Ryzen 5', 7500000, 10),
(1, 'Mouse Logitech', 'Mouse Wireless', 150000, 50),
(2, 'Kemeja Flannel', 'Kemeja bahan tebal', 200000, 25);

-- Insert Orders (Ikhsan membuat order, Budi membuat order)
INSERT INTO orders (user_id, status, total_amount) VALUES
(1, 'completed', 7650000),
(2, 'pending', 200000);

-- Insert Order Items (Menunjukkan hubungan Many-to-Many)
-- Order 1 milik Ikhsan: beli 1 Laptop DAN 1 Mouse (satu order -> banyak produk)
INSERT INTO order_items (order_id, product_id, quantity, price_at_purchase) VALUES
(1, 1, 1, 7500000),
(1, 2, 1, 150000);

-- Order 2 milik Budi: beli 1 Kemeja Flannel
INSERT INTO order_items (order_id, product_id, quantity, price_at_purchase) VALUES
(2, 3, 1, 200000);
