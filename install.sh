#!/bin/bash
# CC2Translate 설치 스크립트 (Linux / macOS)

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

# OS 감지
OS_TYPE="$(uname -s)"
case "$OS_TYPE" in
    Linux*)  OS="linux";;
    Darwin*) OS="macos";;
    *)       echo -e "${RED}지원하지 않는 OS입니다: $OS_TYPE${NC}"; exit 1;;
esac
echo -e "감지된 OS: ${GREEN}$OS_TYPE${NC}"
echo ""

# 현재 디렉토리
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ "$OS" = "macos" ]; then
    INSTALL_DIR="$HOME/Library/Application Support/cc2translate"
    BIN_DIR="/usr/local/bin"
    APP_DIR="$HOME/Applications"
else
    INSTALL_DIR="$HOME/.local/share/cc2translate"
    BIN_DIR="$HOME/.local/bin"
fi

# Python 확인
echo -e "${YELLOW}[1/6]${NC} Python 확인 중..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}오류: Python3가 설치되어 있지 않습니다.${NC}"
    if [ "$OS" = "macos" ]; then
        echo "다음 명령어로 설치하세요: brew install python3"
    else
        echo "다음 명령어로 설치하세요: sudo apt install python3 python3-pip"
    fi
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo -e "      ${GREEN}$PYTHON_VERSION 확인됨${NC}"

# Claude CLI 확인
echo -e "${YELLOW}[2/6]${NC} Claude CLI 확인 중..."
if ! command -v claude &> /dev/null; then
    echo -e "${RED}오류: Claude CLI가 설치되어 있지 않습니다.${NC}"
    echo ""
    echo "Claude Code를 먼저 설치하세요:"
    echo "  npm install -g @anthropic-ai/claude-code"
    echo ""
    echo "또는 https://claude.ai/code 에서 설치 방법을 확인하세요."
    exit 1
fi
CLAUDE_VERSION=$(claude --version 2>/dev/null || echo "버전 확인 불가")
echo -e "      ${GREEN}Claude CLI $CLAUDE_VERSION 확인됨${NC}"

# 빌드 의존성 설치
echo -e "${YELLOW}[3/6]${NC} 빌드 의존성 설치 중..."
pip3 install --user -q PyQt5 pynput pyinstaller 2>/dev/null || {
    pip3 install -q PyQt5 pynput pyinstaller 2>/dev/null || {
        pip install --user -q PyQt5 pynput pyinstaller
    }
}
echo -e "      ${GREEN}의존성 설치 완료${NC}"

# 바이너리 빌드
echo -e "${YELLOW}[4/6]${NC} 바이너리 빌드 중... (1-2분 소요)"
cd "$SCRIPT_DIR"

if [ "$OS" = "macos" ]; then
    # macOS: .app 번들 생성
    python3 -m PyInstaller \
        --onefile \
        --windowed \
        --name CC2Translate \
        --clean \
        --noconfirm \
        cc2translate.py 2>/dev/null || {
        echo -e "${YELLOW}상세 로그로 재시도...${NC}"
        python3 -m PyInstaller --onefile --windowed --name CC2Translate cc2translate.py
    }
else
    # Linux
    python3 -m PyInstaller \
        --onefile \
        --windowed \
        --name cc2translate \
        --clean \
        --noconfirm \
        cc2translate.py 2>/dev/null || {
        echo -e "${YELLOW}상세 로그로 재시도...${NC}"
        python3 -m PyInstaller --onefile --windowed --name cc2translate cc2translate.py
    }
fi
echo -e "      ${GREEN}바이너리 빌드 완료${NC}"

# 프로그램 설치
echo -e "${YELLOW}[5/6]${NC} 프로그램 설치 중..."
mkdir -p "$INSTALL_DIR"

if [ "$OS" = "macos" ]; then
    # macOS: /usr/local/bin에 설치 (sudo 필요할 수 있음)
    if [ -w "$BIN_DIR" ]; then
        cp "$SCRIPT_DIR/dist/CC2Translate" "$BIN_DIR/cc2translate"
    else
        echo -e "${YELLOW}      관리자 권한 필요...${NC}"
        sudo cp "$SCRIPT_DIR/dist/CC2Translate" "$BIN_DIR/cc2translate"
    fi
    chmod +x "$BIN_DIR/cc2translate"
else
    # Linux
    mkdir -p "$BIN_DIR"
    cp "$SCRIPT_DIR/dist/cc2translate" "$BIN_DIR/"
    chmod +x "$BIN_DIR/cc2translate"
fi
echo -e "      ${GREEN}프로그램 설치 완료${NC}"

# 앱 등록
echo -e "${YELLOW}[6/6]${NC} 앱 등록 중..."
if [ "$OS" = "macos" ]; then
    # macOS: Applications 폴더에 심볼릭 링크 또는 Automator 앱 생성
    mkdir -p "$APP_DIR"

    # 간단한 실행 스크립트로 .app 생성
    APP_BUNDLE="$APP_DIR/CC2Translate.app"
    mkdir -p "$APP_BUNDLE/Contents/MacOS"
    cat > "$APP_BUNDLE/Contents/MacOS/CC2Translate" << 'APPEOF'
#!/bin/bash
/usr/local/bin/cc2translate
APPEOF
    chmod +x "$APP_BUNDLE/Contents/MacOS/CC2Translate"

    cat > "$APP_BUNDLE/Contents/Info.plist" << 'PLISTEOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>CC2Translate</string>
    <key>CFBundleIdentifier</key>
    <string>com.cc2translate.app</string>
    <key>CFBundleName</key>
    <string>CC2Translate</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>LSUIElement</key>
    <true/>
</dict>
</plist>
PLISTEOF
    echo -e "      ${GREEN}앱 번들 생성 완료: $APP_BUNDLE${NC}"
else
    # Linux: .desktop 파일 생성
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
fi

# 빌드 파일 정리
rm -rf "$SCRIPT_DIR/build" "$SCRIPT_DIR/dist" "$SCRIPT_DIR"/*.spec 2>/dev/null

# PATH 확인 (Linux만)
if [ "$OS" = "linux" ] && [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
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
if [ "$OS" = "macos" ]; then
    echo "  2. Spotlight에서 'CC2Translate' 검색"
    echo "  3. ~/Applications/CC2Translate.app 실행"
else
    echo "  2. 앱 메뉴에서 'CC2Translate' 검색"
fi
echo ""
echo "사용법:"
if [ "$OS" = "macos" ]; then
    echo "  - 텍스트를 드래그하고 Cmd+C 두 번 누르면 자동 번역"
else
    echo "  - 텍스트를 드래그하고 Ctrl+C 두 번 누르면 자동 번역"
fi
echo "  - 창을 닫으면 시스템 트레이로 최소화"
echo ""
