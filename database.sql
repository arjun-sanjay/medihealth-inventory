-- 1️⃣ CREATE DATABASE
CREATE DATABASE medihealth_db;
USE medihealth_db;

-- ================================
-- 2️⃣ MEDICINES TABLE
-- ================================
DROP TABLE IF EXISTS customer_sales;
DROP TABLE IF EXISTS medicines;

CREATE TABLE medicines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(50),
    quantity INT NOT NULL,
    expiry_date DATE NOT NULL,
    selling_price DECIMAL(10,2) NOT NULL
);

-- ================================
-- 3️⃣ CUSTOMER SALES TABLE
-- ================================
CREATE TABLE customer_sales (
    id INT AUTO_INCREMENT PRIMARY KEY,
    medicine_id INT NOT NULL,
    customer_name VARCHAR(100) NOT NULL,
    quantity INT NOT NULL,
    total_amount DECIMAL(10,2),
    sale_date DATE,
    CONSTRAINT fk_medicine
        FOREIGN KEY (medicine_id)
        REFERENCES medicines(id)
        ON DELETE RESTRICT
);

-- ================================
-- 4️⃣ TRIGGERS
-- ================================

-- 🔹 Set current date automatically
DELIMITER //
CREATE TRIGGER trg_set_sale_date
BEFORE INSERT ON customer_sales
FOR EACH ROW
BEGIN
    IF NEW.sale_date IS NULL THEN
        SET NEW.sale_date = CURDATE();
    END IF;
END;
//
DELIMITER ;

-- 🔹 Calculate total amount
DELIMITER //
CREATE TRIGGER trg_calculate_total
BEFORE INSERT ON customer_sales
FOR EACH ROW
BEGIN
    DECLARE price DECIMAL(10,2);
    SELECT selling_price INTO price
    FROM medicines
    WHERE id = NEW.medicine_id;

    SET NEW.total_amount = price * NEW.quantity;
END;
//
DELIMITER ;

-- 🔹 Reduce stock after sale
DELIMITER //
CREATE TRIGGER trg_reduce_stock
AFTER INSERT ON customer_sales
FOR EACH ROW
BEGIN
    UPDATE medicines
    SET quantity = quantity - NEW.quantity
    WHERE id = NEW.medicine_id;
END;
//
DELIMITER ;

-- ================================
-- 5️⃣ VIEW
-- ================================
CREATE OR REPLACE VIEW sales_summary AS
SELECT
    m.name AS medicine_name,
    SUM(c.quantity) AS total_sold,
    SUM(c.total_amount) AS total_revenue
FROM customer_sales c
JOIN medicines m ON c.medicine_id = m.id
GROUP BY m.name;

-- ================================
-- END OF SCHEMA FILE
-- ================================
