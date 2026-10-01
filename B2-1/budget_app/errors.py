"""사용자에게 안전하게 표시할 애플리케이션 오류"""


class BudgetAppError(Exception):
    """예상 가능한 오류와 해결 힌트 전달"""

    def __init__(self, message: str, hint: str = "--help로 사용 방법을 확인하세요.") -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint


class ValidationError(BudgetAppError):
    """사용자 입력값의 규칙 위반 오류"""


class DataFileError(BudgetAppError):
    """저장 파일 읽기·해석 실패 오류"""
