-- SQLite 전용: FK 오류 검증 쿼리를 위해 외래 키 검사를 활성화한다.
PRAGMA foreign_keys = ON;

-- Query 01: 2만원 이상 도서 중 높은 가격 순 상위 5권을 확인한다.
SELECT book_id, title, category, price, stock
FROM books
WHERE price >= 20000
ORDER BY price DESC
LIMIT 5;

-- Query 02: 서울 고객을 가입일 순으로 확인한다.
SELECT customer_id, name, email, joined_at
FROM customers
WHERE city = '서울'
ORDER BY joined_at ASC;

-- Query 03: 2026-06-10 이후 결제 또는 배송 완료 주문을 확인한다.
SELECT order_id, customer_id, order_date, status, shipping_city
FROM orders
WHERE status IN ('PAID', 'SHIPPED')
  AND order_date >= '2026-06-10'
ORDER BY order_date ASC
LIMIT 10;

-- Query 04: 재고가 7권 이하인 도서를 재고 적은 순으로 확인한다.
SELECT book_id, title, category, stock
FROM books
WHERE stock <= 7
ORDER BY stock ASC, title ASC
LIMIT 10;

-- Query 05: 주문과 고객 정보를 INNER JOIN으로 연결해 주문자를 확인한다.
SELECT o.order_id, c.name, c.city, o.order_date, o.status
FROM orders AS o
INNER JOIN customers AS c
    ON o.customer_id = c.customer_id
ORDER BY o.order_date ASC, o.order_id ASC;

-- Query 06: 주문상세와 도서를 INNER JOIN으로 연결해 주문 라인 금액을 확인한다.
SELECT o.order_id, b.title, oi.quantity, oi.unit_price,
       oi.quantity * oi.unit_price AS line_total
FROM order_items AS oi
INNER JOIN orders AS o
    ON oi.order_id = o.order_id
INNER JOIN books AS b
    ON oi.book_id = b.book_id
WHERE o.status <> 'CANCELLED'
ORDER BY o.order_id ASC, b.title ASC;

-- Query 07: 배송 완료 주문의 고객, 도서, 수량을 INNER JOIN으로 확인한다.
SELECT c.name, o.order_id, b.title, oi.quantity
FROM orders AS o
INNER JOIN customers AS c
    ON o.customer_id = c.customer_id
INNER JOIN order_items AS oi
    ON o.order_id = oi.order_id
INNER JOIN books AS b
    ON oi.book_id = b.book_id
WHERE o.status = 'SHIPPED'
ORDER BY o.order_id ASC, b.title ASC;

-- Query 08: 주문이 없는 고객까지 LEFT JOIN으로 포함해 주문 수를 확인한다.
SELECT c.customer_id, c.name, COUNT(o.order_id) AS order_count
FROM customers AS c
LEFT JOIN orders AS o
    ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.name
ORDER BY order_count ASC, c.customer_id ASC;

-- Query 09: 카테고리별 판매 수량과 매출 합계를 확인한다.
SELECT b.category,
       COUNT(oi.order_item_id) AS line_count,
       SUM(oi.quantity) AS total_quantity,
       SUM(oi.quantity * oi.unit_price) AS revenue
FROM orders AS o
INNER JOIN order_items AS oi
    ON o.order_id = oi.order_id
INNER JOIN books AS b
    ON oi.book_id = b.book_id
WHERE o.status IN ('PAID', 'SHIPPED')
GROUP BY b.category
ORDER BY revenue DESC;

-- Query 10: 배송지 도시별 주문 수와 평균 주문 금액을 확인한다.
SELECT order_totals.shipping_city,
       COUNT(order_totals.order_id) AS order_count,
       ROUND(AVG(order_totals.order_total), 2) AS avg_order_amount
FROM (
    SELECT o.order_id, o.shipping_city,
           SUM(oi.quantity * oi.unit_price) AS order_total
    FROM orders AS o
    INNER JOIN order_items AS oi
        ON o.order_id = oi.order_id
    WHERE o.status IN ('PAID', 'SHIPPED')
    GROUP BY o.order_id, o.shipping_city
) AS order_totals
GROUP BY order_totals.shipping_city
ORDER BY avg_order_amount DESC;

-- Query 11: 같은 카테고리 평균 가격보다 비싼 도서를 서브쿼리로 확인한다.
SELECT b.book_id, b.title, b.category, b.price
FROM books AS b
WHERE b.price > (
    SELECT AVG(b2.price)
    FROM books AS b2
    WHERE b2.category = b.category
)
ORDER BY b.category ASC, b.price DESC;

-- Query 12: 평균 고객 매출 이상 구매한 고객을 서브쿼리로 확인한다.
SELECT c.customer_id, c.name,
       SUM(oi.quantity * oi.unit_price) AS total_spent
FROM customers AS c
INNER JOIN orders AS o
    ON c.customer_id = o.customer_id
INNER JOIN order_items AS oi
    ON o.order_id = oi.order_id
WHERE o.status IN ('PAID', 'SHIPPED')
GROUP BY c.customer_id, c.name
HAVING total_spent >= (
    SELECT AVG(customer_total)
    FROM (
        SELECT SUM(oi2.quantity * oi2.unit_price) AS customer_total
        FROM orders AS o2
        INNER JOIN order_items AS oi2
            ON o2.order_id = oi2.order_id
        WHERE o2.status IN ('PAID', 'SHIPPED')
        GROUP BY o2.customer_id
    ) AS customer_totals
)
ORDER BY total_spent DESC;

-- Query 13: 새 주문을 INSERT하고 생성된 주문 정보를 확인한다.
INSERT INTO orders (customer_id, order_date, status, shipping_city)
VALUES (11, '2026-06-25', 'PENDING', '성남')
RETURNING order_id, customer_id, order_date, status, shipping_city;

-- Query 14: 도서 재고를 UPDATE하고 변경된 값을 확인한다.
UPDATE books
SET stock = stock - 2
WHERE book_id = 10
  AND stock >= 2
RETURNING book_id, title, stock AS updated_stock;

-- Query 15: 대기 중인 주문을 DELETE하고 삭제된 주문을 확인한다.
DELETE FROM orders
WHERE order_id = 7
  AND status = 'PENDING'
RETURNING order_id, customer_id, status;

-- Query 16: 주문일 조회 성능 개선을 위해 인덱스를 생성하고 등록 여부를 확인한다.
CREATE INDEX IF NOT EXISTS idx_orders_order_date ON orders (order_date);
PRAGMA index_list('orders');

-- Query 17: 보너스 - 고객별 구매 합계를 JOIN 방식으로 확인한다.
SELECT c.customer_id, c.name,
       SUM(oi.quantity * oi.unit_price) AS total_spent
FROM customers AS c
INNER JOIN orders AS o
    ON c.customer_id = o.customer_id
INNER JOIN order_items AS oi
    ON o.order_id = oi.order_id
WHERE c.customer_id = 2
  AND o.status IN ('PAID', 'SHIPPED')
GROUP BY c.customer_id, c.name;

-- Query 18: 보너스 - 고객별 구매 합계를 서브쿼리 방식으로 확인한다.
SELECT c.customer_id, c.name,
       (
           SELECT SUM(oi.quantity * oi.unit_price)
           FROM orders AS o
           INNER JOIN order_items AS oi
               ON o.order_id = oi.order_id
           WHERE o.customer_id = c.customer_id
             AND o.status IN ('PAID', 'SHIPPED')
       ) AS total_spent
FROM customers AS c
WHERE c.customer_id = 2;

-- Query 19: 보너스 - 존재하지 않는 고객을 참조하는 주문 INSERT로 FK 오류를 확인한다.
INSERT INTO orders (customer_id, order_date, status, shipping_city)
VALUES (9999, '2026-06-30', 'PENDING', '서울');

-- Query 20: 보너스 - 핵심 지표 3개를 미니 리포트 형태로 확인한다.
SELECT COUNT(*) AS paid_or_shipped_order_count,
       SUM(order_total) AS total_revenue,
       ROUND(AVG(order_total), 2) AS avg_order_amount
FROM (
    SELECT o.order_id,
           SUM(oi.quantity * oi.unit_price) AS order_total
    FROM orders AS o
    INNER JOIN order_items AS oi
        ON o.order_id = oi.order_id
    WHERE o.status IN ('PAID', 'SHIPPED')
    GROUP BY o.order_id
) AS paid_order_totals;
