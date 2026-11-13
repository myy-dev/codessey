"""인증·인가 및 도메인 오류 처리를 위한 공통 예외 정의"""

from __future__ import annotations


class AppError(Exception):
    """오류 메시지와 HTTP 상태 코드를 전달하는 공통 애플리케이션 예외"""
    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class AuthenticationRequired(AppError):
    """비로그인 요청의 로그인 화면 이동을 위한 인증 필요 예외"""
    def __init__(self, message: str = "로그인이 필요한 기능입니다.") -> None:
        super().__init__(message, status_code=401)


class NotFoundError(AppError):
    """조회 대상 부재를 나타내는 404 예외"""
    def __init__(self, message: str = "요청한 데이터를 찾을 수 없습니다.") -> None:
        super().__init__(message, status_code=404)


class ForbiddenError(AppError):
    """데이터 접근 권한 부족을 나타내는 403 예외"""
    def __init__(self, message: str = "이 데이터에 접근할 권한이 없습니다.") -> None:
        super().__init__(message, status_code=403)

