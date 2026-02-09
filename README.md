# CC2Translate

Ctrl+C 두 번으로 텍스트를 번역하는 GUI 프로그램입니다.

Claude Max 결제하느라 DeepL 결제할 돈이 없어서 돌려막기로 쓰려고 만들었습니다.

## 요구사항

- Python 3.8+
- Claude CLI ([설치 방법](https://claude.ai/code))
- Linux (X11)

## 설치

```bash
git clone https://github.com/ghkim919/cc2translate.git
cd cc2translate
./install.sh
```

## 사용법

### 실행
```bash
cc2translate
```
또는 앱 메뉴에서 "CC2Translate" 검색

### 번역하기
1. 아무 텍스트를 드래그해서 선택
2. **Ctrl+C 두 번** 빠르게 누르기
3. 자동으로 번역 창이 열리고 번역 시작

### 기능
- **자동 언어 감지**: 한국어, 영어, 일본어, 중국어 등 자동 인식
- **모델 선택**: Haiku(빠름), Sonnet(균형), Opus(고품질)
- **시스템 트레이**: 창을 닫아도 백그라운드에서 실행

## 제거

```bash
~/.local/share/cc2translate/uninstall.sh
```
또는
```bash
./uninstall.sh
```

## 파일 구조

```
cc2translate/
├── cc2translate.py    # 메인 프로그램
├── install.sh         # 설치 스크립트
├── uninstall.sh       # 제거 스크립트
├── requirements.txt   # Python 의존성
└── README.md          # 이 파일
```

## 라이센스

MIT License
