"""번역 백엔드 - Claude/Gemini CLI를 이용한 번역 처리"""

import json
import os
import re
import subprocess

from constants import GEMINI_MODELS


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
    """CLI를 이용한 번역 실행. 성공 시 번역 텍스트 반환, 실패 시 TranslationError 발생."""
    prompt = build_prompt(text, src_lang, tgt_lang)
    is_gemini = model in GEMINI_MODELS.values()

    if is_gemini:
        cmd = ['gemini', '-p', prompt]
    else:
        cmd = ['claude', '-p', prompt, '--model', model]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, env=_get_env())
    except subprocess.TimeoutExpired:
        raise TranslationError("번역 시간 초과 (60초)")
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
