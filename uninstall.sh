#!/bin/bash
# CC2Translate 제거 스크립트 (Linux / macOS)

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

OS_TYPE="$(uname -s)"
case "$OS_TYPE" in
    Linux*)  OS="linux";;
    Darwin*) OS="macos";;
esac

echo "==================================="
echo "  CC2Translate 제거"
echo "==================================="
echo ""

# 실행 중인 프로세스 종료
echo -e "${YELLOW}[1/4]${NC} 실행 중인 프로세스 종료..."
pkill -f CC2Translate 2>/dev/null || true
pkill -f cc2translate 2>/dev/null || true
echo -e "      ${GREEN}완료${NC}"

# 설치 파일 제거
echo -e "${YELLOW}[2/4]${NC} 설치 파일 제거..."
rm -f "$HOME/.local/bin/cc2translate"
rm -rf "$HOME/.local/share/cc2translate"
if [ "$OS" = "macos" ]; then
    rm -rf "$HOME/Applications/CC2Translate.app"
else
    rm -f "$HOME/.local/share/applications/cc2translate.desktop"
fi
echo -e "      ${GREEN}완료${NC}"

# 빌드 캐시 제거
echo -e "${YELLOW}[3/4]${NC} 빌드 캐시 제거..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
rm -rf "$SCRIPT_DIR/build" "$SCRIPT_DIR/dist" "$SCRIPT_DIR"/*.spec 2>/dev/null || true
echo -e "      ${GREEN}완료${NC}"

# macOS 권한 초기화
echo -e "${YELLOW}[4/4]${NC} 권한 기록 초기화..."
if [ "$OS" = "macos" ]; then
    tccutil reset Accessibility com.cc2translate.app 2>/dev/null || true
    echo -e "      ${GREEN}Accessibility 권한 초기화 완료${NC}"
else
    echo -e "      ${GREEN}해당 없음 (Linux)${NC}"
fi

echo ""
echo "==================================="
echo -e "  ${GREEN}제거 완료!${NC}"
echo "==================================="
