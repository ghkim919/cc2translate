# CC2Translate

복사 단축키 두 번으로 텍스트를 번역하는 GUI 프로그램입니다.
- **Linux**: Ctrl+C 두 번
- **macOS**: Cmd+C 두 번

Claude Max 결제하느라 DeepL 결제할 돈이 없어서 돌려막기로 쓰려고 만들었습니다. <br>
돈 있으면 DeepL 쓰세요... DeepL이 훨씬 좋습니다.

![example](example.gif)

## 지원 모델

### CLI 기반 (프로세스 호출)

| Provider | 모델 | 특징 |
|----------|------|------|
| **Claude** | Haiku | 빠름 |
| **Claude** | Sonnet | 균형 |
| **Claude** | Opus | 고품질 |
| **Gemini** | Flash | 빠름 |
| **Gemini** | Pro | 균형 |

### API 직접 호출 (빠름)

| Provider | 모델 | 비고 |
|----------|------|------|
| **Gemini API** | 2.5 Flash Lite | 무료 티어 사용 가능 |
| **Gemini API** | 2.0 Flash | |
| **Gemini API** | 2.5 Flash | |
| **Gemini API** | 2.5 Pro | |
| **DeepL API** | Free | 무료 50만자/월 |

API 모델은 프로세스 생성 오버헤드 없이 직접 호출하므로 CLI 대비 응답이 빠릅니다.

## 요구사항

- Python 3.8+
- Linux (X11) 또는 macOS
- **Claude Code** 또는 **Gemini CLI** (CLI 모델 사용 시)

- [Claude Code 설치](https://claude.ai/code)
- [Gemini CLI 설치](https://github.com/google-gemini/gemini-cli) (선택)

### API 키 설정 (API 모델 사용 시)

셸 설정 파일(`~/.zshrc` 또는 `~/.bashrc`)에 환경변수를 추가합니다:

```bash
export GEMINI_API_KEY="your-gemini-api-key"   # Google AI Studio에서 발급
export DEEPL_API_KEY="your-deepl-api-key"     # DeepL 계정에서 발급
```

사용할 모델의 키만 설정하면 됩니다. 앱 내 "설정" 버튼에서 현재 키 상태를 확인할 수 있습니다.

## 설치

```bash
git clone https://github.com/ghkim919/cc2translate.git
cd cc2translate
./install.sh
```

설치 스크립트가 자동으로 OS를 감지하고 적절하게 설치합니다.

## 사용법

### 실행
```bash
cc2translate
```

**Linux**: 앱 메뉴에서 "CC2Translate" 검색 <br>
**macOS**: Spotlight에서 "CC2Translate" 검색 또는 `~/Applications/CC2Translate.app` 실행

### 번역하기
1. 아무 텍스트를 드래그해서 선택
2. **복사 단축키 두 번** 빠르게 누르기 (Linux: Ctrl+C, macOS: Cmd+C)
3. 자동으로 번역 창이 열리고 번역 시작

### 기능
- **자동 언어 감지**: 한국어, 영어, 일본어, 중국어 등 자동 인식
- **모델 선택**: CLI (Claude/Gemini) 또는 API (Gemini API/DeepL API)
- **API 직접 호출**: 환경변수로 API 키 설정, CLI 대비 빠른 응답
- **시스템 트레이**: 창을 닫아도 백그라운드에서 실행

## 제거

```bash
./uninstall.sh
```

## 라이센스

MIT License
