#!/usr/bin/env bash
# pre-push-check: kiểm tra nhanh trước khi push / gắn tag phase-N.
# Chạy từ thư mục gốc repo:  .agents/skills/pre-push-check/check.sh [--save <dir>]
# Biến môi trường: SEED (mặc định 1), TICKS (mặc định 600).
set -u

SAVE_DIR=""
while [ $# -gt 0 ]; do
  case "$1" in
    --save)
      if [ $# -lt 2 ]; then echo "thiếu đối số cho --save" >&2; exit 2; fi
      SAVE_DIR="$2"; shift 2 ;;
    -h|--help)
      echo "Dùng: $0 [--save <dir>]   (env: SEED=1 TICKS=600)"; exit 0 ;;
    *)
      echo "đối số không hợp lệ: $1" >&2; exit 2 ;;
  esac
done

# --save: chạy lại chính script (không có --save) và tee toàn bộ đầu ra vào file.
if [ -n "$SAVE_DIR" ]; then
  mkdir -p "$SAVE_DIR" || { echo "không tạo được thư mục $SAVE_DIR" >&2; exit 2; }
  OUT_FILE="$SAVE_DIR/pre-push-check.txt"
  bash "$0" 2>&1 | tee "$OUT_FILE"
  rc=${PIPESTATUS[0]}
  echo "Đã lưu đầu ra vào: $OUT_FILE"
  exit "$rc"
fi

if [ ! -f game.contract.json ]; then
  echo "FAIL: không thấy game.contract.json — hãy chạy từ thư mục gốc repo." >&2
  exit 2
fi

SEED="${SEED:-1}"
TICKS="${TICKS:-600}"
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/pre-push-check.XXXXXX")" || exit 2
trap 'rm -rf "$TMP_DIR"' EXIT INT TERM

FAILS=0
SUMMARY=""
record() { # $1=PASS|FAIL $2=mô tả
  SUMMARY="${SUMMARY}  [$1] $2
"
  if [ "$1" = "FAIL" ]; then FAILS=$((FAILS + 1)); fi
}

echo "== pre-push-check =="
echo "Thời điểm: $(date '+%Y-%m-%d %H:%M:%S')"
if command -v git >/dev/null 2>&1; then
  echo "Git: $(git rev-parse --abbrev-ref HEAD 2>/dev/null) @ $(git rev-parse --short HEAD 2>/dev/null)"
fi
echo "SEED=$SEED TICKS=$TICKS"
echo

# Bước 1: unit test
echo "-- Bước 1: unit test --"
if PYTHONPATH=tests:. python3 -m unittest discover -s tests; then
  record PASS "Bước 1: unit test"
else
  record FAIL "Bước 1: unit test"
fi
echo

# Đọc headless_cmd từ contract (không hard-code)
HEADLESS_CMD="$(python3 -c 'import json; print(json.load(open("game.contract.json"))["headless_cmd"])')"
if [ -z "$HEADLESS_CMD" ]; then
  echo "FAIL: không đọc được headless_cmd từ game.contract.json"
  record FAIL "Đọc headless_cmd"
else
  echo "headless_cmd: $HEADLESS_CMD"

  # Bước 2: tất định — chạy 2 lần cùng seed, so byte
  echo "-- Bước 2: tất định (cùng seed => cùng byte) --"
  for mode in gather quan; do
    a="$TMP_DIR/$mode.a.jsonl"; b="$TMP_DIR/$mode.b.jsonl"
    # shellcheck disable=SC2086  # cố ý tách từ headless_cmd
    if $HEADLESS_CMD --mode "$mode" --seed "$SEED" --ticks "$TICKS" --out "$a" \
       && $HEADLESS_CMD --mode "$mode" --seed "$SEED" --ticks "$TICKS" --out "$b"; then
      if cmp -s "$a" "$b"; then
        echo "  $mode: giống hệt nhau ($(wc -c < "$a" | tr -d ' ') byte)"
        record PASS "Bước 2: tất định mode=$mode"
      else
        echo "  $mode: KHÁC NHAU giữa 2 lần chạy"
        cmp "$a" "$b" | head -1
        record FAIL "Bước 2: tất định mode=$mode"
      fi
    else
      echo "  $mode: headless chạy lỗi"
      record FAIL "Bước 2: tất định mode=$mode (headless lỗi)"
    fi
  done
  echo

  # Bước 3: đầu vào sai phải trả exit 2
  echo "-- Bước 3: đầu vào sai => exit 2 --"
  # shellcheck disable=SC2086
  $HEADLESS_CMD --mode gather --seed "$SEED" --ticks -1 --out "$TMP_DIR/bad.jsonl" 2>"$TMP_DIR/bad.err"
  rc=$?
  echo "  --ticks -1 => exit $rc ($(head -1 "$TMP_DIR/bad.err"))"
  if [ "$rc" -eq 2 ]; then
    record PASS "Bước 3: --ticks -1 trả exit 2"
  else
    record FAIL "Bước 3: --ticks -1 trả exit $rc (cần 2)"
  fi
  echo
fi

echo "== Tổng kết =="
printf "%s" "$SUMMARY"
if [ "$FAILS" -eq 0 ]; then
  echo "KẾT QUẢ: PASS — có thể push."
  exit 0
else
  echo "KẾT QUẢ: FAIL ($FAILS bước lỗi) — KHÔNG push. Sửa luật, không sửa test cho xanh."
  exit 1
fi
