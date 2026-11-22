# 테스트 계정과 인증 방식

[README로 돌아가기](../README.md)

| 항목 | 내용 |
| --- | --- |
| 테스트 계정 | ID `demo` / PW `demo1234` |
| 저장 방식 | DB 저장, 서버 시작 시 계정이 없으면 생성 |
| 인증 방식 | 서명된 세션 쿠키의 `user_id`로 사용자 조회 |
| 선택 이유 | 브라우저 기반 SSR에 적합한 쿠키를 통한 로그인 상태 전달 |
| 비밀번호 저장 | passlib의 PBKDF2-SHA256 단방향 해시 |

## 세션 인증

1. 로그인 성공 시 `start_session`으로 기존 세션 초기화와 `user_id` 저장
2. 후속 요청에서 `SessionMiddleware`의 쿠키 서명 검증과 `request.session` 복원
3. `get_current_user_optional`의 `user_id` 기반 DB 사용자 조회
4. 보호 라우터의 `CurrentUser`와 `require_user`를 통한 로그인 필수 검사

- 세션 쿠키의 서명 검증과 암호화 미사용
- 세션에 `user_id`·CSRF 토큰·일회성 알림·OAuth state 보관
- 비밀번호·GitHub 액세스 토큰의 세션 저장 제외
- 로그아웃 시 기존 세션 초기화

HTTPS 전용 쿠키와 비밀키 설정은 [배포 문서](deployment.md#환경-변수) 참고

## 접근 제어와 요청 검증

- 비로그인 보호 경로 요청의 로그인 화면 이동
- 로그인 후 GET·HEAD는 원래 경로, 변경 요청은 프로젝트 목록으로 복귀
- `ProjectService.get_owned_project`의 사용자 ID·`owner_id` 비교와 할 일에 연결된 프로젝트의 소유권 검사
- 데이터 변경 폼의 CSRF 토큰과 세션 토큰 간 상수 시간 비교
- 로그인 후 복귀 경로의 내부 경로 제한

공개·보호 경로 구분은 [경로 문서](routes.md) 참고

## GitHub 계정 연결

1. GitHub 인증 시작과 사용자 승인
2. 콜백의 일회성 state 검증
3. 코드·액세스 토큰 교환과 GitHub 사용자 조회
4. 계정 조회·생성과 세션 시작

- `oauth_provider="github"`와 `oauth_subject`(GitHub 사용자 ID) 조합으로 계정 식별
- 최초 로그인 시 계정 생성과 이후 동일 계정 재사용
- 로컬 비밀번호 생성과 닉네임·아이디가 비슷한 다른 계정과의 자동 병합 미지원
- 일반 로그인과 동일한 세션 방식 사용

[설정 방법](deployment.md#github-소셜-로그인-설정) 참고
