#!/bin/bash
# CC2Translate 제거 스크립트

echo "CC2Translate 제거 중..."

rm -rf "$HOME/.local/share/cc2translate"
rm -f "$HOME/.local/bin/cc2translate"
rm -f "$HOME/.local/share/applications/cc2translate.desktop"

echo "제거 완료!"
