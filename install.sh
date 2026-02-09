#!/bin/bash
# CC2Translate 설치 스크립트

set -e

echo "==================================="
echo "  CC2Translate 설치"
echo "==================================="
echo ""

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 현재 디렉토리
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$HOME/.local/share/cc2translate"
BIN_DIR="$HOME/.local/bin"

# Python 확인
echo -e "${YELLOW}[1/5]${NC} Python 확인 중..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}오류: Python3가 설치되어 있지 않습니다.${NC}"
    echo "다음 명령어로 설치하세요: sudo apt install python3 python3-pip"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo -e "      ${GREEN}$PYTHON_VERSION 확인됨${NC}"

# Claude CLI 확인
echo -e "${YELLOW}[2/5]${NC} Claude CLI 확인 중..."
if ! command -v claude &> /dev/null; then
    echo -e "${RED}오류: Claude CLI가 설치되어 있지 않습니다.${NC}"
    echo "https://claude.ai/code 에서 설치 방법을 확인하세요."
    exit 1
fi
CLAUDE_VERSION=$(claude --version 2>/dev/null || echo "버전 확인 불가")
echo -e "      ${GREEN}Claude CLI $CLAUDE_VERSION 확인됨${NC}"

# 의존성 설치
echo -e "${YELLOW}[3/5]${NC} 의존성 패키지 설치 중..."
pip3 install --user -q PyQt5 pynput 2>/dev/null || {
    echo -e "${YELLOW}      pip로 설치 시도 중...${NC}"
    pip install --user -q PyQt5 pynput
}
echo -e "      ${GREEN}의존성 설치 완료${NC}"

# 프로그램 설치
echo -e "${YELLOW}[4/5]${NC} 프로그램 설치 중..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"
cp "$SCRIPT_DIR/cc2translate.py" "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/cc2translate.py"

# 실행 스크립트 생성
cat > "$BIN_DIR/cc2translate" << 'EOF'
#!/bin/bash
python3 "$HOME/.local/share/cc2translate/cc2translate.py" "$@"
EOF
chmod +x "$BIN_DIR/cc2translate"
echo -e "      ${GREEN}프로그램 설치 완료${NC}"

# 데스크톱 엔트리 생성
echo -e "${YELLOW}[5/5]${NC} 앱 메뉴 등록 중..."
mkdir -p "$HOME/.local/share/applications"
cat > "$HOME/.local/share/applications/cc2translate.desktop" << EOF
[Desktop Entry]
Name=CC2Translate
Comment=Claude 기반 번역기 (Ctrl+C 두 번으로 번역)
Exec=$BIN_DIR/cc2translate
Icon=accessories-text-editor
Terminal=false
Type=Application
Categories=Utility;Office;
Keywords=translate;translation;claude;번역;
EOF
echo -e "      ${GREEN}앱 메뉴 등록 완료${NC}"

# PATH 확인
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo ""
    echo -e "${YELLOW}주의:${NC} $BIN_DIR 가 PATH에 없습니다."
    echo "다음 줄을 ~/.bashrc 또는 ~/.zshrc에 추가하세요:"
    echo ""
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
fi

echo ""
echo "==================================="
echo -e "  ${GREEN}설치 완료!${NC}"
echo "==================================="
echo ""
echo "실행 방법:"
echo "  1. 터미널: cc2translate"
echo "  2. 앱 메뉴에서 'CC2Translate' 검색"
echo ""
echo "사용법:"
echo "  - 텍스트를 드래그하고 Ctrl+C 두 번 누르면 자동 번역"
echo "  - 창을 닫으면 시스템 트레이로 최소화"
echo ""
