#!/usr/bin/env bash

set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root"

step() {
    printf '%s\n' '------------------------------------------------------------'
    printf '# %s\n' "$1"
    printf '%s\n' '------------------------------------------------------------'
}

print_command() {
    local argument

    printf '$'
    for argument in "$@"; do
        if [[ "$argument" == *[[:space:]]* ]]; then
            printf ' "%s"' "$argument"
        else
            printf ' %s' "$argument"
        fi
    done
    printf '\n'
}

run() {
    print_command "$@"
    "$@"
    printf '\n'
}

add_transaction() {
    local title="$1"
    local date="$2"
    local transaction_type="$3"
    local category="$4"
    local amount="$5"
    local memo="$6"
    local tags="$7"
    local result

    step "$title"
    printf "%s\n" "$ python3 -m budget_app add <<'EOF'"
    printf '%s\n' "$date" "$transaction_type" "$category" "$amount" "$memo" "$tags"
    printf '%s\n' 'EOF'
    printf '실행 결과:\n'
    result="$(python3 -m budget_app add <<EOF
$date
$transaction_type
$category
$amount
$memo
$tags
EOF
    )"
    printf '%s\n' "$result" | sed -E 's/^.*(\[저장 완료\].*)$/\1/'
    printf '\n'
}

if [[ -e data ]]; then
    printf '[중단] ./data가 이미 존재합니다. 빈 상태 시연을 위해 IDE에서 data 폴더를 확인하세요.\n' >&2
    exit 1
fi

step "1. 최초 상태 및 자동 초기화 확인"
run python3 -m budget_app --help
run python3 -m budget_app category list
run python3 -m budget_app list

step "2. 카테고리 추가"
run python3 -m budget_app category add --name hobby
run python3 -m budget_app category list

add_transaction "3-1. 첫 지출 등록" \
    "2024-01-15" "expense" "food" "15000" "점심" "meal"
add_transaction "3-2. 수입 거래 등록" \
    "2024-01-25" "income" "salary" "3000000" "월급" "salary,monthly"
add_transaction "3-3. 추가 지출 거래 등록" \
    "2024-01-20" "expense" "hobby" "7000" "책" "book"

step "3-4. 거래 추가 후 월별 요약 확인"
run python3 -m budget_app summary --month 2024-01 --top 3

step "4. 거래 목록 및 검색"
run python3 -m budget_app list --limit 2
run python3 -m budget_app list --limit 10
run python3 -m budget_app search \
    --from 2024-01-01 \
    --to 2024-01-31 \
    --category food \
    --type expense
run python3 -m budget_app search --q 점심 --tag meal

step "5. 예산 설정 및 월별 요약"
run python3 -m budget_app budget set --month 2024-01 --amount 10000
run python3 -m budget_app budget get --month 2024-01
run python3 -m budget_app summary --month 2024-01 --top 3

step "6. 거래 수정"
run python3 -m budget_app update \
    --id TX-000001 \
    --date 2024-01-16 \
    --amount 18000 \
    --memo "저녁" \
    --tags dinner
run python3 -m budget_app search --q 저녁 --tag dinner

step "7-1. 사용 중인 카테고리 삭제 제한"
print_command python3 -m budget_app category remove --name hobby
if python3 -m budget_app category remove --name hobby; then
    printf '[오류] 사용 중인 카테고리가 삭제되었습니다.\n' >&2
    exit 1
else
    exit_code=$?
    printf '종료 코드: %s\n' "$exit_code"
    if [[ "$exit_code" -ne 2 ]]; then
        printf '[오류] 예상 종료 코드 2와 다릅니다.\n' >&2
        exit 1
    fi
fi
printf '\n'

step "7-2. 미사용 카테고리 삭제"
run python3 -m budget_app update --id TX-000003 --type income --category salary
run python3 -m budget_app list --limit 10
run python3 -m budget_app category remove --name hobby
run python3 -m budget_app category list

step "8. 거래 삭제"
run python3 -m budget_app delete --id TX-000003
run python3 -m budget_app list --limit 10

step "9-1. 반복 거래 규칙 등록"
run python3 -m budget_app recurring add \
    --type expense \
    --category rent \
    --amount 500000 \
    --day 31 \
    --memo "월세"
run python3 -m budget_app recurring list

step "9-2. 반복 거래 생성 및 ID 미재사용 확인"
run python3 -m budget_app recurring generate --month 2024-02
run python3 -m budget_app search \
    --from 2024-02-01 \
    --to 2024-02-29 \
    --category rent

step "9-3. 같은 달 중복 생성 방지"
run python3 -m budget_app recurring generate --month 2024-02

step "9-4. 반복 거래 규칙 삭제"
run python3 -m budget_app recurring remove --id RC-000001
run python3 -m budget_app recurring list
run python3 -m budget_app search \
    --from 2024-02-01 \
    --to 2024-02-29 \
    --category rent

printf '# 자동 시연 완료\n'
printf '1~9번 실행 완료, 10번 CSV와 11번 ZIP 백업 수동 시연\n'
