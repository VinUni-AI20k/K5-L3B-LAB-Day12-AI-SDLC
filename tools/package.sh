#!/usr/bin/env bash
# Đóng gói bản chạy được cho GitHub Release.
#   bash tools/package.sh            -> dist/quan-an-cho-noi-v1.0.0.zip
#   VERSION=1.0.1 bash tools/package.sh
# Zip gồm: client/, chonoi/, game.contract.json, README.md, LICENSE, CREDITS.md,
# CHANGELOG.md, tools/, docs/contracts/ và hai file chạy nhanh run.sh / run.command.
# Không đưa vào: .git, .claude, .agents, tests, __pycache__, *.pyc, .DS_Store, dist/.
set -euo pipefail

VERSION="${VERSION:-1.0.0}"
NAME="quan-an-cho-noi-v${VERSION}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST="$ROOT/dist"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

command -v zip >/dev/null || { echo "Cần lệnh 'zip' (macOS có sẵn; Linux: apt install zip)" >&2; exit 1; }

OUT="$STAGE/$NAME"
mkdir -p "$OUT/docs"
cd "$ROOT"
for f in game.contract.json README.md LICENSE CREDITS.md CHANGELOG.md; do
  [ -f "$f" ] || { echo "Thiếu $f" >&2; exit 1; }
  cp "$f" "$OUT/"
done
cp -R client chonoi tools "$OUT/"
cp -R docs/contracts "$OUT/docs/contracts"
[ -f docs/release/RELEASE_NOTES_v${VERSION}.md ] && mkdir -p "$OUT/docs/release" \
  && cp "docs/release/RELEASE_NOTES_v${VERSION}.md" "$OUT/docs/release/"

# Dọn rác build / hệ điều hành
find "$OUT" \( -name __pycache__ -o -name .pytest_cache -o -name .mypy_cache \) -type d -prune -exec rm -rf {} +
find "$OUT" \( -name '*.pyc' -o -name '.DS_Store' -o -name '*.jsonl' \) -type f -delete

cat > "$OUT/run.sh" <<'EOF'
#!/usr/bin/env bash
# Chạy bản GUI: phục vụ thư mục này qua HTTP rồi mở trình duyệt. Ctrl+C để dừng.
cd "$(dirname "$0")"
PORT="${PORT:-8099}"
URL="http://127.0.0.1:${PORT}/client/index.html"
echo "Quán Ăn Chợ Nổi -> $URL  (Ctrl+C để dừng)"
( sleep 1; if command -v open >/dev/null; then open "$URL"; elif command -v xdg-open >/dev/null; then xdg-open "$URL"; fi ) >/dev/null 2>&1 &
exec python3 -m http.server "$PORT" --bind 127.0.0.1
EOF
cat > "$OUT/run.command" <<'EOF'
#!/usr/bin/env bash
# macOS: bấm đúp trong Finder để chạy (lần đầu có thể cần chuột phải -> Open).
cd "$(dirname "$0")" && exec bash ./run.sh
EOF
chmod +x "$OUT/run.sh" "$OUT/run.command" "$OUT/tools/package.sh"

mkdir -p "$DIST"
rm -f "$DIST/$NAME.zip"
( cd "$STAGE" && zip -qr -X "$DIST/$NAME.zip" "$NAME" )
echo "Đã tạo: dist/$NAME.zip ($(du -h "$DIST/$NAME.zip" | cut -f1))"
if command -v shasum >/dev/null; then (cd "$DIST" && shasum -a 256 "$NAME.zip" | tee "$NAME.zip.sha256"); fi
