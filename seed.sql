-- Insert Users
INSERT INTO users (first_name, last_name, email) VALUES
('Ikhsan', 'Febrian', 'ikhsan@email.com'),
('Budi', 'Santoso', 'budi@email.com');

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

-- Insert Order Items
-- Ikhsan beli 1 Laptop dan 1 Mouse (Satu order, banyak barang)
INSERT INTO order_items (order_id, product_id, quantity, price_at_purchase) VALUES
(1, 1, 1, 7500000),
(1, 2, 1, 150000);

-- Budi beli 1 Kemeja Flannel
INSERT INTO order_items (order_id, product_id, quantity, price_at_purchase) VALUES
(2, 3, 1, 200000);