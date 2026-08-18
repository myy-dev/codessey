# 보너스 과제 기록

## 조인 1개를 두 방식으로 풀기

- 요구사항: 2번 고객의 전체 주문 수를 구한다.
- JOIN 방식: `queries.sql`의 Query 17, 실행 결과 `results/query-17.txt`
- 서브쿼리 방식: `queries.sql`의 Query 18, 실행 결과 `results/query-18.txt`
- 비교: JOIN 방식은 고객과 주문을 직접 연결한 뒤 주문 수를 세고, 서브쿼리 방식은 고객 행마다 내부 조회로 주문 수를 구한다. 두 방식 모두 같은 `2`를 반환한다.

## 데이터 정합성 깨뜨려 보기

- 시도한 쿼리: `queries.sql`의 Query 19
- 오류 원인: `orders.customer_id`는 `customers.customer_id`를 참조하므로 존재하지 않는 `customer_id = 9999` 주문은 저장할 수 없다.
- 올바른 입력 방식: 먼저 `customers`에 고객을 등록한 뒤, 생성된 `customer_id`를 사용해 `orders`에 주문을 입력한다.
- 실행 결과: `results/query-19.txt`

## 미니 리포트 만들기

- 핵심 지표 1: 전체 고객 수
- 핵심 지표 2: 전체 도서 수
- 핵심 지표 3: 평균 도서 가격
- 산출 SQL: `queries.sql`의 Query 20
- 최종 리포트 결과: `results/query-20.txt`
