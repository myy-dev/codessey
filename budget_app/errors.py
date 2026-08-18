"""사용자에게 안전하게 보여 줄 애플리케이션 오류."""


class BudgetAppError(Exception):
    """예상 가능한 오류와 해결 힌트를 함께 전달한다."""

    def __init__(self, message: str, hint: str = "--help로 사용 방법을 확인하세요.") -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint


class ValidationError(BudgetAppError):
    """사용자 입력값이 규칙에 맞지 않을 때 발생한다."""


class DataFileError(BudgetAppError):
    """저장 파일을 읽거나 해석할 수 없을 때 발생한다."""
