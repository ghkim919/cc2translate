"""상수 정의 - OS 감지, 언어 목록, 모델 목록"""

import os
import platform

# OS 감지
IS_MACOS = platform.system() == "Darwin"
IS_LINUX = platform.system() == "Linux"

# 지원 언어 목록
LANGUAGES = {
    "자동 감지": "auto",
    "한국어": "Korean",
    "영어": "English",
    "일본어": "Japanese",
    "중국어 (간체)": "Simplified Chinese",
    "중국어 (번체)": "Traditional Chinese",
    "스페인어": "Spanish",
    "프랑스어": "French",
    "독일어": "German",
    "러시아어": "Russian",
    "포르투갈어": "Portuguese",
    "이탈리아어": "Italian",
    "베트남어": "Vietnamese",
    "태국어": "Thai",
    "인도네시아어": "Indonesian",
    "아랍어": "Arabic",
}

# Claude 모델
CLAUDE_MODELS = {
    "Claude Haiku (빠름)": "haiku",
    "Claude Sonnet (균형)": "sonnet",
    "Claude Opus (고품질)": "opus",
}

# Gemini 모델
GEMINI_MODELS = {
    "Gemini Flash (빠름)": "gemini-2.0-flash",
    "Gemini Pro (균형)": "gemini-1.5-pro",
}

# Gemini API 모델 (직접 호출 - 여기에 모델 추가만 하면 자동 동작)
GEMINI_API_MODELS = {
    "Gemini 2.5 Flash Lite API": "gemini-2.5-flash-lite",
    "Gemini 2.0 Flash API": "gemini-2.0-flash",
    "Gemini 2.5 Flash API": "gemini-2.5-flash",
    "Gemini 2.5 Pro API": "gemini-2.5-pro",
}

# DeepL API 모델 (직접 호출)
DEEPL_API_MODELS = {
    "DeepL API (빠름)": "deepl-free",
}

# 전체 모델 (UI 표시용)
ALL_MODELS = {**CLAUDE_MODELS, **GEMINI_MODELS, **GEMINI_API_MODELS, **DEEPL_API_MODELS}

# ── Timing ──
API_TIMEOUT = 30
CLI_TIMEOUT = 60
GITHUB_API_TIMEOUT = 10
DOUBLE_PRESS_INTERVAL = 0.5
AUTO_TRANSLATE_DEBOUNCE_MS = 1000
HISTORY_SEARCH_DEBOUNCE_MS = 300
SOCKET_CONNECT_TIMEOUT_MS = 500
HOTKEY_TRIGGER_DELAY = 0.1

# ── UI ──
WINDOW_SIZE = (900, 600)
WINDOW_MIN_SIZE = (600, 400)
DEFAULT_FONT_FAMILY = "Sans"
DEFAULT_FONT_SIZE = 11
FONT_SIZE_RANGE = (8, 24)
FONT_SLIDER_MAX_WIDTH = 120
SPLITTER_DEFAULT = [450, 450]
SPLITTER_HISTORY_OPEN = [250, 650]
SPLITTER_HISTORY_CLOSED = [0, 900]
HISTORY_PREVIEW_LENGTH = 60

# ── App ──
APP_ID = "cc2translate-single-instance"
GITHUB_REPO = "ghkim919/cc2translate"
APP_DATA_DIR = os.path.expanduser("~/.local/share/cc2translate")
HISTORY_DB_NAME = "history.db"
MAX_HISTORY_ENTRIES = 500

# ── macOS ──
MACOS_KEY_C = 8
