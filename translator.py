"""번역 백엔드 - Claude/Gemini CLI 및 API를 이용한 번역 처리"""

import json
import os
import re
import subprocess

import requests

from constants import GEMINI_MODELS, GEMINI_API_MODELS, DEEPL_API_MODELS, API_TIMEOUT, CLI_TIMEOUT

# DeepL 언어 코드 매핑
DEEPL_LANG_MAP = {
    "Korean": "KO",
    "English": "EN",
    "Japanese": "JA",
    "Simplified Chinese": "ZH-HANS",
    "Traditional Chinese": "ZH-HANT",
    "Spanish": "ES",
    "French": "FR",
    "German": "DE",
    "Russian": "RU",
    "Portuguese": "PT",
    "Italian": "IT",
    "Indonesian": "ID",
    "Arabic": "AR",
}

def _get_api_key(key_name):
    """환경변수에서 API 키 조회"""
    return os.environ.get(key_name, "")


def _get_env():
    """macOS .app 번들에서도 CLI를 찾을 수 있도록 PATH를 보강"""
    env = os.environ.copy()
    extra_paths = [
        os.path.expanduser("~/.local/bin"),
        "/opt/homebrew/bin",
        "/usr/local/bin",
    ]
    env["PATH"] = os.pathsep.join(extra_paths) + os.pathsep + env.get("PATH", "")
    return env


class TranslationError(Exception):
    pass


def build_prompt(text, src_lang, tgt_lang):
    """번역 프롬프트 생성"""
    if src_lang == "auto":
        return f'Translate the following text to {tgt_lang}. Return ONLY a JSON object: {{"translation": "your translation here"}}\n\n{text}'
    else:
        return f'Translate the following {src_lang} text to {tgt_lang}. Return ONLY a JSON object: {{"translation": "your translation here"}}\n\n{text}'


def translate(text, src_lang, tgt_lang, model):
    """번역 실행. API 모델이면 API 호출, 아니면 CLI 호출."""
    if model in GEMINI_API_MODELS.values():
        return _translate_gemini_api(text, src_lang, tgt_lang, model)
    if model in DEEPL_API_MODELS.values():
        return _translate_deepl_api(text, src_lang, tgt_lang)
    return _translate_cli(text, src_lang, tgt_lang, model)


def _translate_gemini_api(text, src_lang, tgt_lang, model):
    """Gemini API 직접 호출 - model 파라미터로 어떤 모델이든 동적 호출"""
    api_key = _get_api_key("GEMINI_API_KEY")
    if not api_key:
        raise TranslationError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")

    prompt = build_prompt(text, src_lang, tgt_lang)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    headers = {"x-goog-api-key": api_key}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=API_TIMEOUT)
    except requests.Timeout:
        raise TranslationError(f"Gemini API 시간 초과 ({API_TIMEOUT}초)")
    except requests.ConnectionError:
        raise TranslationError("Gemini API 연결 실패. 네트워크를 확인하세요.")

    if resp.status_code != 200:
        error_msg = resp.json().get("error", {}).get("message", resp.text)
        raise TranslationError(f"Gemini API 오류: {error_msg}")

    try:
        data = resp.json()
        raw = data["candidates"][0]["content"]["parts"][0]["text"]
        return parse_translation(raw)
    except (KeyError, IndexError):
        raise TranslationError("Gemini API 응답을 파싱할 수 없습니다")


def _translate_deepl_api(text, src_lang, tgt_lang):
    """DeepL API 직접 호출"""
    api_key = _get_api_key("DEEPL_API_KEY")
    if not api_key:
        raise TranslationError("DEEPL_API_KEY 환경변수가 설정되지 않았습니다.")

    tgt_code = DEEPL_LANG_MAP.get(tgt_lang)
    if not tgt_code:
        raise TranslationError(f"DeepL에서 '{tgt_lang}' 언어를 지원하지 않습니다")

    url = "https://api-free.deepl.com/v2/translate"
    params = {
        "text": text,
        "target_lang": tgt_code,
    }
    if src_lang != "auto":
        src_code = DEEPL_LANG_MAP.get(src_lang)
        if src_code:
            # DeepL source_lang은 상위 코드만 사용 (EN, ZH 등)
            params["source_lang"] = src_code.split("-")[0]

    headers = {"Authorization": f"DeepL-Auth-Key {api_key}"}

    try:
        resp = requests.post(url, data=params, headers=headers, timeout=API_TIMEOUT)
    except requests.Timeout:
        raise TranslationError(f"DeepL API 시간 초과 ({API_TIMEOUT}초)")
    except requests.ConnectionError:
        raise TranslationError("DeepL API 연결 실패. 네트워크를 확인하세요.")

    if resp.status_code == 403:
        raise TranslationError("DeepL API 키가 유효하지 않습니다")
    if resp.status_code == 456:
        raise TranslationError("DeepL API 무료 할당량이 초과되었습니다")
    if resp.status_code != 200:
        raise TranslationError(f"DeepL API 오류 ({resp.status_code}): {resp.text}")

    try:
        data = resp.json()
        return data["translations"][0]["text"]
    except (KeyError, IndexError):
        raise TranslationError("DeepL API 응답을 파싱할 수 없습니다")


def _translate_cli(text, src_lang, tgt_lang, model):
    """CLI를 이용한 번역 실행"""
    prompt = build_prompt(text, src_lang, tgt_lang)
    is_gemini = model in GEMINI_MODELS.values()

    if is_gemini:
        cmd = ['gemini', '-p', prompt]
    else:
        cmd = ['claude', '-p', prompt, '--model', model]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=CLI_TIMEOUT, env=_get_env())
    except subprocess.TimeoutExpired:
        raise TranslationError(f"번역 시간 초과 ({CLI_TIMEOUT}초)")
    except FileNotFoundError:
        cli_name = "Gemini" if is_gemini else "Claude"
        raise TranslationError(f"{cli_name} CLI가 설치되어 있지 않습니다")

    if result.returncode == 0:
        return parse_translation(result.stdout)
    else:
        raise TranslationError(result.stderr.strip() or "번역 실패")


def parse_translation(raw_output):
    """JSON 응답에서 번역 텍스트를 추출. CLI 노이즈가 섞여도 JSON만 파싱."""
    match = re.search(r'\{[^{}]*"translation"\s*:\s*"', raw_output)
    if match:
        json_start = match.start()
        # JSON 끝 위치 찾기: 중첩 없는 단순 객체이므로 다음 } 탐색
        depth = 0
        for i in range(json_start, len(raw_output)):
            if raw_output[i] == '{':
                depth += 1
            elif raw_output[i] == '}':
                depth -= 1
                if depth == 0:
                    try:
                        data = json.loads(raw_output[json_start:i + 1])
                        return data["translation"]
                    except (json.JSONDecodeError, KeyError):
                        break
    # JSON 파싱 실패 시 원본 출력에서 노이즈 제거 후 반환
    return raw_output.strip()
