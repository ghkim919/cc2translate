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

# 공통 경로 (Linux/macOS 동일)
INSTALL_DIR="$HOME/.local/share/cc2translate"
BIN_DIR="$HOME/.local/bin"
APP_DIR="$HOME/Applications"

# Python 확인
echo -e "${YELLOW}[1/5]${NC} Python 확인 중..."
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

# 빌드 의존성 설치
echo -e "${YELLOW}[2/5]${NC} 빌드 의존성 설치 중..."
DEPS="PyQt5 pynput pyinstaller requests"
if [ "$OS" = "macos" ]; then
    DEPS="$DEPS pyobjc-framework-ApplicationServices pyobjc-framework-Quartz"
fi
pip3 install --user -q $DEPS 2>/dev/null || {
    pip3 install -q $DEPS 2>/dev/null || {
        pip install --user -q $DEPS
    }
}
echo -e "      ${GREEN}의존성 설치 완료${NC}"

# 바이너리 빌드
echo -e "${YELLOW}[3/5]${NC} 바이너리 빌드 중... (1-2분 소요)"
cd "$SCRIPT_DIR"

# 버전 정보 생성 (git commit hash)
git rev-parse HEAD > version.txt

if [ "$OS" = "macos" ]; then
    # macOS: 정식 .app 번들 생성 (Input Monitoring 권한 부여 가능)
    python3 -m PyInstaller \
        --windowed \
        --name CC2Translate \
        --osx-bundle-identifier com.cc2translate.app \
        --add-data "version.txt:." \
        --clean \
        --noconfirm \
        main.py 2>/dev/null || {
        echo -e "${YELLOW}상세 로그로 재시도...${NC}"
        python3 -m PyInstaller --windowed --name CC2Translate --osx-bundle-identifier com.cc2translate.app --add-data "version.txt:." main.py
    }
else
    # Linux
    python3 -m PyInstaller \
        --onefile \
        --windowed \
        --name cc2translate \
        --add-data "version.txt:." \
        --clean \
        --noconfirm \
        main.py 2>/dev/null || {
        echo -e "${YELLOW}상세 로그로 재시도...${NC}"
        python3 -m PyInstaller --onefile --windowed --name cc2translate --add-data "version.txt:." main.py
    }
fi
echo -e "      ${GREEN}바이너리 빌드 완료${NC}"

# 프로그램 설치
echo -e "${YELLOW}[4/5]${NC} 프로그램 설치 중..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"

if [ "$OS" = "macos" ]; then
    # macOS: PyInstaller가 생성한 정식 .app 번들 설치
    APP_BUNDLE="$SCRIPT_DIR/dist/CC2Translate.app"

    # ~/Applications에 복사
    mkdir -p "$APP_DIR"
    rm -rf "$APP_DIR/CC2Translate.app"
    cp -R "$APP_BUNDLE" "$APP_DIR/"

    # CLI에서도 실행 가능하도록 심볼릭 링크
    ln -sf "$APP_DIR/CC2Translate.app/Contents/MacOS/CC2Translate" "$BIN_DIR/cc2translate"
else
    cp "$SCRIPT_DIR/dist/cc2translate" "$BIN_DIR/"
fi
chmod +x "$BIN_DIR/cc2translate"
echo -e "      ${GREEN}프로그램 설치 완료${NC}"

# 앱 등록
echo -e "${YELLOW}[5/5]${NC} 앱 등록 중..."
if [ "$OS" = "macos" ]; then
    echo -e "      ${GREEN}앱 번들 설치 완료: $APP_DIR/CC2Translate.app${NC}"
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

# 소스 repo 경로를 config.json에 저장
CONFIG_FILE="$INSTALL_DIR/config.json"
if [ -f "$CONFIG_FILE" ]; then
    # 기존 config가 있으면 repo_path만 업데이트
    python3 -c "
import json
try:
    with open('$CONFIG_FILE', 'r') as f:
        config = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    config = {}
config['repo_path'] = '$SCRIPT_DIR'
with open('$CONFIG_FILE', 'w') as f:
    json.dump(config, f, indent=2)
"
else
    mkdir -p "$INSTALL_DIR"
    echo "{\"repo_path\": \"$SCRIPT_DIR\"}" > "$CONFIG_FILE"
fi

# 빌드 파일 정리
rm -rf "$SCRIPT_DIR/build" "$SCRIPT_DIR/dist" "$SCRIPT_DIR"/*.spec "$SCRIPT_DIR/version.txt" 2>/dev/null

# PATH 확인
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo ""
    echo -e "${YELLOW}주의:${NC} $BIN_DIR 가 PATH에 없습니다."
    if [ "$OS" = "macos" ]; then
        echo "다음 줄을 ~/.zshrc에 추가하세요:"
    else
        echo "다음 줄을 ~/.bashrc 또는 ~/.zshrc에 추가하세요:"
    fi
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
    echo "  - 창을 닫으면 시스템 트레이로 최소화"
    echo ""
    echo -e "${YELLOW}[macOS 권한 설정]${NC}"
    echo "  최초 실행 시 시스템 설정 > 개인정보 보호 및 보안 > 손쉬운 사용에서"
    echo "  CC2Translate을 허용해주세요."
else
    echo "  - 텍스트를 드래그하고 Ctrl+C 두 번 누르면 자동 번역"
    echo "  - 창을 닫으면 시스템 트레이로 최소화"
fi
echo ""
