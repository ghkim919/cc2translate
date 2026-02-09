"""상수 정의 - OS 감지, 언어 목록, 모델 목록"""

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

# 전체 모델 (UI 표시용)
ALL_MODELS = {**CLAUDE_MODELS, **GEMINI_MODELS}
