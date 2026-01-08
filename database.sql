
-- MEDIHEALTH DATABASE SCHEMA
-- =========================================

CREATE DATABASE IF NOT EXISTS medicine_db;
USE medicine_db;

-- TABLE: medicines
-- =========================================
CREATE TABLE medicines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(100),
    quantity INT NOT NULL,
    expiry_date DATE NOT NULL,
    selling_price DECIMAL(10,2) NOT NULL
);


-- TABLE: customer_sales
-- =========================================
CREATE TABLE customer_sales (
    id INT AUTO_INCREMENT PRIMARY KEY,
    medicine_id INT NOT NULL,
    customer_name VARCHAR(100) NOT NULL,
    quantity INT NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    sale_date DATE NOT NULL,
    FOREIGN KEY (medicine_id) REFERENCES medicines(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);


-- TABLE: usage_logs (for demand prediction)
-- =========================================
CREATE TABLE usage_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    medicine_id INT NOT NULL,
    used_qty INT NOT NULL,
    usage_date DATE NOT NULL,
    FOREIGN KEY (medicine_id) REFERENCES medicines(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- SAMPLE DATA (OPTIONAL)
-- =========================================
INSERT INTO medicines (name, category, quantity, expiry_date, selling_price)
VALUES
('Paracetamol', 'Tablet', 100, '2026-12-31', 2.50),
('Amoxicillin', 'Capsule', 80, '2026-10-15', 5.00);
