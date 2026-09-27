-- ЛР2: нормализация схемы.
-- Контактные данные клиента выносим из orders в отдельную таблицу customers,
-- а order_items переводим со скопированных product_name/product_price
-- на ссылку product_id.

CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    address VARCHAR(500),
    phone VARCHAR(50)
);

-- Переносим уже существующих клиентов, схлопывая одинаковые контакты.
INSERT INTO customers (full_name, address, phone)
SELECT DISTINCT customer_full_name, customer_address, customer_phone
FROM orders;

ALTER TABLE orders ADD COLUMN customer_id INTEGER;

UPDATE orders o
SET customer_id = c.id
FROM customers c
WHERE c.full_name = o.customer_full_name
  AND c.address IS NOT DISTINCT FROM o.customer_address
  AND c.phone IS NOT DISTINCT FROM o.customer_phone;

ALTER TABLE orders ALTER COLUMN customer_id SET NOT NULL;
ALTER TABLE orders
    ADD CONSTRAINT orders_customer_id_fkey
    FOREIGN KEY (customer_id) REFERENCES customers(id);

ALTER TABLE orders
    DROP COLUMN customer_full_name,
    DROP COLUMN customer_address,
    DROP COLUMN customer_phone;

-- Товары, на которые ссылаются позиции, но которых нет в products,
-- заводим из данных самих позиций, чтобы ссылку можно было проставить.
INSERT INTO products (name, price, description)
SELECT oi.product_name, MIN(oi.product_price), NULL
FROM order_items oi
WHERE NOT EXISTS (
    SELECT 1 FROM products p WHERE p.name = oi.product_name
)
GROUP BY oi.product_name;

ALTER TABLE order_items ADD COLUMN product_id INTEGER;

UPDATE order_items oi
SET product_id = p.id
FROM products p
WHERE p.name = oi.product_name;

ALTER TABLE order_items ALTER COLUMN product_id SET NOT NULL;
ALTER TABLE order_items
    ADD CONSTRAINT order_items_product_id_fkey
    FOREIGN KEY (product_id) REFERENCES products(id);

ALTER TABLE order_items
    DROP COLUMN product_name,
    DROP COLUMN product_price;
