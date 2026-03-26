CREATE DATABASE medihealth_db;
USE medihealth_db;

--------------------------------------------------


CREATE TABLE medicines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(50),
    quantity INT NOT NULL CHECK (quantity >= 0),
    expiry_date DATE NOT NULL,
    selling_price DECIMAL(10,2) NOT NULL CHECK (selling_price > 0)
);
-----------------------------------------------


CREATE TABLE customer_sales (
    id INT AUTO_INCREMENT PRIMARY KEY,
    medicine_id INT NOT NULL,
    customer_name VARCHAR(100),
    quantity INT NOT NULL CHECK (quantity > 0),
    total_amount DECIMAL(10,2),
    sale_date DATE,

    FOREIGN KEY (medicine_id)
    REFERENCES medicines(id)
    ON DELETE CASCADE
);

--------------------------------------------------


CREATE VIEW sales_summary AS
SELECT m.name, SUM(c.quantity) AS total_sold,
       SUM(c.total_amount) AS revenue
FROM customer_sales c
JOIN medicines m ON c.medicine_id = m.id
GROUP BY m.name;


--------------------------------------------------

DELIMITER $$

CREATE TRIGGER reduce_stock_after_sale
AFTER INSERT ON customer_sales
FOR EACH ROW
BEGIN
    UPDATE medicines
    SET quantity = quantity - NEW.quantity
    WHERE id = NEW.medicine_id;
END$$

DELIMITER ;
