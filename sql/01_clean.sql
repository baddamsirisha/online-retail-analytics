-- 01_clean.sql : build a clean sales table from the raw transactions
-- Rules: drop cancellations (invoice starting with 'C'), non-positive quantity/price,
-- non-product stock codes (postage, fees, manual adjustments) and exact duplicate rows.
DROP TABLE IF EXISTS sales;
CREATE TABLE sales AS
SELECT DISTINCT
    Invoice                         AS invoice,
    StockCode                       AS stock_code,
    TRIM(Description)               AS description,
    Quantity                        AS quantity,
    InvoiceDate                     AS invoice_date,
    substr(InvoiceDate, 1, 7)       AS month,
    Price                           AS price,
    Quantity * Price                AS revenue,
    CAST("Customer ID" AS INTEGER)  AS customer_id,
    Country                         AS country
FROM raw
WHERE Invoice NOT LIKE 'C%'
  AND Quantity > 0
  AND Price > 0
  AND StockCode NOT IN ('POST','DOT','M','C2','D','BANK CHARGES','AMAZONFEE','ADJUST','ADJUST2','TEST001','TEST002','PADS','B','S','CRUK');

-- Remove orders that were fully reversed later by a matching cancellation
-- (same customer, product and quantity). Without this, two one-off bulk orders
-- of 80,995 and 74,215 units that were cancelled right away would distort the top-product ranking.
DELETE FROM sales
WHERE EXISTS (
    SELECT 1 FROM raw c
    WHERE c.Invoice LIKE 'C%'
      AND CAST(c."Customer ID" AS INTEGER) = sales.customer_id
      AND c.StockCode = sales.stock_code
      AND -c.Quantity = sales.quantity
      AND c.InvoiceDate >= sales.invoice_date
      AND sales.quantity >= 1000
);
