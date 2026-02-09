"""번역 백엔드 - Claude/Gemini CLI를 이용한 번역 처리"""

import subprocess

from constants import GEMINI_MODELS


class TranslationError(Exception):
    pass


def build_prompt(text, src_lang, tgt_lang):
    """번역 프롬프트 생성"""
    if src_lang == "auto":
        return f'Translate the following text to {tgt_lang}. Only output the translation, nothing else:\n\n{text}'
    else:
        return f'Translate the following {src_lang} text to {tgt_lang}. Only output the translation, nothing else:\n\n{text}'


def translate(text, src_lang, tgt_lang, model):
    """CLI를 이용한 번역 실행. 성공 시 번역 텍스트 반환, 실패 시 TranslationError 발생."""
    prompt = build_prompt(text, src_lang, tgt_lang)
    is_gemini = model in GEMINI_MODELS.values()

    if is_gemini:
        cmd = ['gemini', '-p', prompt]
    else:
        cmd = ['claude', '-p', prompt, '--model', model]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        raise TranslationError("번역 시간 초과 (60초)")
    except FileNotFoundError:
        cli_name = "Gemini" if is_gemini else "Claude"
        raise TranslationError(f"{cli_name} CLI가 설치되어 있지 않습니다")

    if result.returncode == 0:
        return result.stdout.strip()
    else:
        raise TranslationError(result.stderr.strip() or "번역 실패")
