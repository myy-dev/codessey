-- SQLite 전용: FK 오류 검증 쿼리를 위해 외래 키 검사를 활성화한다.
PRAGMA foreign_keys = ON;

-- Query 01
-- 요구 사항: 기본 조회
-- 확인 목적: 2만원 이상 도서 중 높은 가격 순 상위 5권을 확인한다.
SELECT book_id, title, category, price, stock
FROM books
WHERE price >= 20000
ORDER BY price DESC
LIMIT 5;

-- Query 02
-- 요구 사항: 기본 조회
-- 확인 목적: 서울 고객을 가입일 순으로 확인한다.
SELECT customer_id, name, email, joined_at
FROM customers
WHERE city = '서울'
ORDER BY joined_at ASC
LIMIT 10;

-- Query 03
-- 요구 사항: 기본 조회
-- 확인 목적: 2026-06-10 이후 결제 또는 배송 완료 주문을 확인한다.
SELECT order_id, customer_id, ordered_at, status, shipping_city
FROM orders
WHERE status IN ('PAID', 'SHIPPED')
  AND ordered_at >= '2026-06-10 00:00:00'
ORDER BY ordered_at ASC
LIMIT 10;

-- Query 04
-- 요구 사항: 기본 조회
-- 확인 목적: 재고가 7권 이하인 도서를 재고 적은 순으로 확인한다.
SELECT book_id, title, category, stock
FROM books
WHERE stock <= 7
ORDER BY stock ASC, title ASC
LIMIT 10;

-- Query 05
-- 요구 사항: 조인
-- 확인 목적: 주문과 고객 정보를 INNER JOIN으로 연결해 주문자를 확인한다.
SELECT o.order_id, c.name, c.city, o.ordered_at, o.status
FROM orders AS o
INNER JOIN customers AS c
    ON o.customer_id = c.customer_id
ORDER BY o.ordered_at ASC, o.order_id ASC;

-- Query 06
-- 요구 사항: 조인
-- 확인 목적: 주문상세와 도서를 INNER JOIN으로 연결해 주문 도서를 확인한다.
SELECT oi.order_id, b.title, oi.quantity
FROM order_items AS oi
INNER JOIN books AS b
    ON oi.book_id = b.book_id
ORDER BY oi.order_id ASC, b.title ASC;

-- Query 07
-- 요구 사항: 조인
-- 확인 목적: 배송 완료 주문과 주문상세를 INNER JOIN으로 연결해 수량을 확인한다.
SELECT o.order_id, o.status, oi.book_id, oi.quantity
FROM orders AS o
INNER JOIN order_items AS oi
    ON o.order_id = oi.order_id
WHERE o.status = 'SHIPPED'
ORDER BY o.order_id ASC, oi.book_id ASC;

-- Query 08
-- 요구 사항: 조인
-- 확인 목적: 주문이 없는 고객까지 LEFT JOIN으로 포함해 주문 수를 확인한다.
SELECT c.customer_id, c.name, COUNT(o.order_id) AS order_count
FROM customers AS c
LEFT JOIN orders AS o
    ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.name
ORDER BY order_count ASC, c.customer_id ASC;

-- Query 09
-- 요구 사항: 집계
-- 확인 목적: 고객별 주문 수를 COUNT로 확인한다.
SELECT customer_id, COUNT(*) AS order_count
FROM orders
GROUP BY customer_id
ORDER BY customer_id ASC;

-- Query 10
-- 요구 사항: 집계
-- 확인 목적: 카테고리별 평균 도서 가격을 AVG로 확인한다.
SELECT category, ROUND(AVG(price), 2) AS average_price
FROM books
GROUP BY category
ORDER BY category ASC;

-- Query 11
-- 요구 사항: 집계
-- 확인 목적: 카테고리별 전체 재고를 SUM으로 확인한다.
SELECT category, SUM(stock) AS total_stock
FROM books
GROUP BY category
ORDER BY category ASC;

-- Query 12
-- 요구 사항: 서브쿼리
-- 확인 목적: 전체 평균 가격보다 비싼 도서를 서브쿼리로 확인한다.
SELECT book_id, title, price
FROM books
WHERE price > (
    SELECT AVG(price)
    FROM books
)
ORDER BY price DESC;

-- Query 13
-- 요구 사항: 데이터 추가
-- 확인 목적: 새 주문을 INSERT하고 생성된 주문 정보를 확인한다.
INSERT INTO orders (customer_id, status, shipping_city)
VALUES (11, 'PENDING', '성남')
RETURNING order_id, customer_id, status, shipping_city;

-- Query 14
-- 요구 사항: 데이터 수정 및 삭제
-- 확인 목적: 도서 재고를 UPDATE하고 변경된 값을 확인한다.
UPDATE books
SET stock = stock - 2
WHERE book_id = 10
  AND stock >= 2
RETURNING book_id, title, stock AS updated_stock;

-- Query 15
-- 요구 사항: 데이터 수정 및 삭제
-- 확인 목적: 대기 중인 주문을 DELETE하고 삭제된 주문을 확인한다.
DELETE FROM orders
WHERE order_id = 7
  AND status = 'PENDING'
RETURNING order_id, customer_id, status;

-- Query 16
-- 요구 사항: 인덱스
-- 확인 목적: 주문 시각 조회 성능 개선을 위해 인덱스를 생성하고 등록 여부를 확인한다.
CREATE INDEX IF NOT EXISTS idx_orders_ordered_at ON orders (ordered_at);
PRAGMA index_list('orders');

-- Query 17
-- 요구 사항: 보너스
-- 확인 목적: 보너스 - 2번 고객의 주문 수를 JOIN 방식으로 확인한다.
SELECT c.customer_id, c.name, COUNT(o.order_id) AS order_count
FROM customers AS c
INNER JOIN orders AS o
    ON c.customer_id = o.customer_id
WHERE c.customer_id = 2
GROUP BY c.customer_id, c.name;

-- Query 18
-- 요구 사항: 보너스
-- 확인 목적: 보너스 - 2번 고객의 주문 수를 서브쿼리 방식으로 확인한다.
SELECT c.customer_id, c.name,
       (
           SELECT COUNT(*)
           FROM orders AS o
           WHERE o.customer_id = c.customer_id
       ) AS order_count
FROM customers AS c
WHERE c.customer_id = 2;

-- Query 19
-- 요구 사항: 보너스
-- 확인 목적: 보너스 - 존재하지 않는 고객을 참조하는 주문 INSERT로 FK 오류를 확인한다.
INSERT INTO orders (customer_id, status, shipping_city)
VALUES (9999, 'PENDING', '서울');

-- Query 20
-- 요구 사항: 보너스
-- 확인 목적: 보너스 - 고객 수, 도서 수, 평균 도서 가격을 미니 리포트로 확인한다.
SELECT (SELECT COUNT(*) FROM customers) AS customer_count,
       (SELECT COUNT(*) FROM books) AS book_count,
       (SELECT ROUND(AVG(price), 2) FROM books) AS average_book_price;
