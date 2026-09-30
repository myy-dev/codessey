"""CLI 공통 관심사 분리용 데코레이터"""

from __future__ import annotations

import sys
from functools import wraps
from typing import Callable, ParamSpec

from .errors import BudgetAppError

P = ParamSpec("P")


def handle_cli_errors(func: Callable[P, int]) -> Callable[P, int]:
    """예상 오류의 스택트레이스 없는 원인·힌트 출력"""

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> int:
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            print("\n[취소] 사용자 요청으로 작업을 중단했습니다.", file=sys.stderr)
            return 130
        except BudgetAppError as exc:
            print(f"[오류] {exc.message}", file=sys.stderr)
            if exc.hint:
                print(f"[힌트] {exc.hint}", file=sys.stderr)
            return 2
        except (OSError, ValueError) as exc:
            print(f"[오류] 작업을 완료할 수 없습니다: {exc}", file=sys.stderr)
            print("[힌트] 파일 경로와 입력값을 확인하세요.", file=sys.stderr)
            return 3
        except Exception:
            print("[오류] 예상하지 못한 문제가 발생했습니다.", file=sys.stderr)
            print("[힌트] 입력값과 저장 파일을 확인한 뒤 다시 시도하세요.", file=sys.stderr)
            return 1

    return wrapper
