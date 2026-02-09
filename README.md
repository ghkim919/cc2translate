# CC2Translate

복사 단축키 두 번으로 텍스트를 번역하는 GUI 프로그램입니다.
- **Linux**: Ctrl+C 두 번
- **macOS**: Cmd+C 두 번

Claude Max 결제하느라 DeepL 결제할 돈이 없어서 돌려막기로 쓰려고 만들었습니다.

## 지원 모델

| Provider | 모델 | 특징 |
|----------|------|------|
| **Claude** | Haiku | 빠름 |
| **Claude** | Sonnet | 균형 |
| **Claude** | Opus | 고품질 |
| **Gemini** | Flash | 빠름 |
| **Gemini** | Pro | 균형 |

## 요구사항

- Python 3.8+
- Linux (X11) 또는 macOS
- **Claude Code** 또는 **Gemini CLI** (사용할 모델에 따라)

### Claude Code 설치

```bash
npm install -g @anthropic-ai/claude-code
```

또는 https://claude.ai/code 에서 설치 방법을 확인하세요.

> Claude Code를 사용하려면 [Claude Max/Pro 구독](https://claude.ai) 또는 API 키가 필요합니다.

### Gemini CLI 설치 (선택)

```bash
npm install -g @google/gemini-cli
```

또는 https://github.com/google-gemini/gemini-cli 에서 설치 방법을 확인하세요.

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

**Linux**: 앱 메뉴에서 "CC2Translate" 검색
**macOS**: Spotlight에서 "CC2Translate" 검색 또는 `~/Applications/CC2Translate.app` 실행

### 번역하기
1. 아무 텍스트를 드래그해서 선택
2. **복사 단축키 두 번** 빠르게 누르기 (Linux: Ctrl+C, macOS: Cmd+C)
3. 자동으로 번역 창이 열리고 번역 시작

### 기능
- **자동 언어 감지**: 한국어, 영어, 일본어, 중국어 등 자동 인식
- **모델 선택**: Claude (Haiku/Sonnet/Opus), Gemini (Flash/Pro)
- **시스템 트레이**: 창을 닫아도 백그라운드에서 실행

## 제거

**Linux**:
```bash
./uninstall.sh
```

**macOS**:
```bash
rm ~/.local/bin/cc2translate
rm -rf ~/Applications/CC2Translate.app
```

## 라이센스

MIT License
