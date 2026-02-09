#!/usr/bin/env python3
"""
CC2Translate - Ctrl+C (macOS: Cmd+C) 두 번으로 번역하는 GUI 프로그램
클립보드 내용을 Claude를 이용해 번역합니다.
"""

import sys
import subprocess
import threading
import time
import platform

# OS 감지
IS_MACOS = platform.system() == "Darwin"
IS_LINUX = platform.system() == "Linux"
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QComboBox, QLabel, QPushButton, QSplitter, QFrame,
    QSystemTrayIcon, QMenu, QAction, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtGui import QIcon, QFont
from pynput import keyboard


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

# Claude 모델 목록
MODELS = {
    "Haiku (빠름)": "haiku",
    "Sonnet (균형)": "sonnet",
    "Opus (고품질)": "opus",
}


class SignalEmitter(QObject):
    """스레드 간 시그널 전달용"""
    show_window = pyqtSignal()
    translation_done = pyqtSignal(str)
    translation_error = pyqtSignal(str)


class TranslatorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.signal_emitter = SignalEmitter()
        self.signal_emitter.show_window.connect(self.show_and_activate)
        self.signal_emitter.translation_done.connect(self.on_translation_done)
        self.signal_emitter.translation_error.connect(self.on_translation_error)

        self.init_ui()
        self.setup_hotkey_listener()
        self.setup_tray_icon()

        # 복사 단축키 더블 클릭 감지용
        self.last_copy_time = 0
        self.modifier_pressed = False

        # OS별 단축키 텍스트
        self.shortcut_text = "Cmd+C" if IS_MACOS else "Ctrl+C"

    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("CC2Translate - Claude 번역기")
        self.setGeometry(100, 100, 900, 600)
        self.setMinimumSize(600, 400)

        # 툴바 생성
        toolbar = self.addToolBar("설정")
        toolbar.setMovable(False)
        toolbar.setStyleSheet("""
            QToolBar {
                background: #f5f5f5;
                border-bottom: 1px solid #ddd;
                padding: 5px;
                spacing: 10px;
            }
        """)

        # 모델 선택
        model_label = QLabel(" 모델:")
        toolbar.addWidget(model_label)
        self.model_combo = QComboBox()
        self.model_combo.addItems(MODELS.keys())
        self.model_combo.setCurrentText("Haiku (빠름)")
        self.model_combo.setMinimumWidth(120)
        toolbar.addWidget(self.model_combo)

        toolbar.addSeparator()

        # 소스 언어
        src_label = QLabel(" 원본:")
        toolbar.addWidget(src_label)
        self.src_lang_combo = QComboBox()
        self.src_lang_combo.addItems(LANGUAGES.keys())
        self.src_lang_combo.setCurrentText("자동 감지")
        self.src_lang_combo.setMinimumWidth(100)
        toolbar.addWidget(self.src_lang_combo)

        # 화살표
        arrow_label = QLabel(" → ")
        arrow_label.setFont(QFont("Sans", 12, QFont.Bold))
        toolbar.addWidget(arrow_label)

        # 타겟 언어
        tgt_label = QLabel("번역:")
        toolbar.addWidget(tgt_label)
        self.tgt_lang_combo = QComboBox()
        tgt_langs = [k for k in LANGUAGES.keys() if k != "자동 감지"]
        self.tgt_lang_combo.addItems(tgt_langs)
        self.tgt_lang_combo.setCurrentText("한국어")
        self.tgt_lang_combo.setMinimumWidth(100)
        toolbar.addWidget(self.tgt_lang_combo)

        # 스페이서
        spacer = QWidget()
        spacer.setSizePolicy(spacer.sizePolicy().horizontalPolicy(), spacer.sizePolicy().verticalPolicy())
        spacer.setMinimumWidth(20)
        toolbar.addWidget(spacer)

        toolbar.addSeparator()

        # 버튼들
        self.clear_btn = QPushButton("지우기")
        self.clear_btn.clicked.connect(self.clear_texts)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #e0e0e0;
                color: #333;
                border: none;
                border-radius: 3px;
                padding: 5px 15px;
            }
            QPushButton:hover { background-color: #d0d0d0; }
        """)
        toolbar.addWidget(self.clear_btn)

        self.copy_btn = QPushButton("복사")
        self.copy_btn.clicked.connect(self.copy_result)
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #5cb85c;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 5px 15px;
            }
            QPushButton:hover { background-color: #4cae4c; }
        """)
        toolbar.addWidget(self.copy_btn)

        self.translate_btn = QPushButton("번역")
        self.translate_btn.clicked.connect(self.do_translate)
        self.translate_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a90d9;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 5px 15px;
            }
            QPushButton:hover { background-color: #357abd; }
            QPushButton:disabled { background-color: #cccccc; }
        """)
        toolbar.addWidget(self.translate_btn)

        # 메인 위젯 - 텍스트 영역만
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # 텍스트 영역 (스플리터 사용)
        splitter = QSplitter(Qt.Horizontal)

        # 원본 텍스트
        self.src_text = QTextEdit()
        self.src_text.setPlaceholderText(f"원본 텍스트 ({self.shortcut_text} 두 번으로 클립보드에서 가져오기)")
        self.src_text.setFont(QFont("Sans", 11))
        self.src_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 10px;
            }
        """)

        # 번역 텍스트
        self.tgt_text = QTextEdit()
        self.tgt_text.setPlaceholderText("번역 결과")
        self.tgt_text.setReadOnly(True)
        self.tgt_text.setFont(QFont("Sans", 11))
        self.tgt_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 10px;
                background-color: #fafafa;
            }
        """)

        splitter.addWidget(self.src_text)
        splitter.addWidget(self.tgt_text)
        splitter.setSizes([450, 450])
        main_layout.addWidget(splitter)

        # 상태바
        self.statusBar().showMessage(f"준비됨 - {self.shortcut_text} 두 번으로 번역")
        self.status_label = self.statusBar()  # 호환성을 위해

    def setup_tray_icon(self):
        """시스템 트레이 아이콘 설정"""
        self.tray_icon = QSystemTrayIcon(self)
        # 기본 아이콘 사용 (아이콘 파일이 없는 경우)
        self.tray_icon.setIcon(self.style().standardIcon(self.style().SP_ComputerIcon))

        tray_menu = QMenu()
        show_action = QAction("창 보이기", self)
        show_action.triggered.connect(self.show_and_activate)
        quit_action = QAction("종료", self)
        quit_action.triggered.connect(self.quit_app)

        tray_menu.addAction(show_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_activated)
        self.tray_icon.show()

    def tray_activated(self, reason):
        """트레이 아이콘 클릭 시"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_and_activate()

    def setup_hotkey_listener(self):
        """글로벌 핫키 리스너 설정 (Linux: Ctrl+C, macOS: Cmd+C)"""
        def on_press(key):
            try:
                # macOS: Command 키, Linux: Ctrl 키
                if IS_MACOS:
                    if key == keyboard.Key.cmd or key == keyboard.Key.cmd_l or key == keyboard.Key.cmd_r:
                        self.modifier_pressed = True
                else:
                    if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                        self.modifier_pressed = True
            except:
                pass

        def on_release(key):
            try:
                # macOS: Command 키, Linux: Ctrl 키
                if IS_MACOS:
                    if key == keyboard.Key.cmd or key == keyboard.Key.cmd_l or key == keyboard.Key.cmd_r:
                        self.modifier_pressed = False
                else:
                    if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                        self.modifier_pressed = False

                # 복사 단축키 감지 (c 키가 눌렸을 때 modifier가 눌려있는 상태)
                if hasattr(key, 'char') and key.char == 'c' and self.modifier_pressed:
                    current_time = time.time()
                    if current_time - self.last_copy_time < 0.5:  # 0.5초 내에 두 번
                        self.last_copy_time = 0
                        # 약간의 딜레이 후 창 표시 (클립보드에 복사될 시간)
                        threading.Timer(0.1, self.trigger_show_window).start()
                    else:
                        self.last_copy_time = current_time
            except:
                pass

        self.listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        self.listener.daemon = True
        self.listener.start()

    def trigger_show_window(self):
        """메인 스레드에서 창 표시"""
        self.signal_emitter.show_window.emit()

    def show_and_activate(self):
        """창 표시 및 활성화 + 자동 번역"""
        # 클립보드 내용 가져오기
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text:
            self.src_text.setText(text)
            self.detect_language(text)

        self.show()
        self.activateWindow()
        self.raise_()

        # 텍스트가 있으면 자동으로 번역 시작
        if text:
            self.do_translate()

    def detect_language(self, text):
        """텍스트 언어 감지 (간단한 휴리스틱)"""
        # 한글이 포함되어 있으면 한국어
        if any('\uac00' <= c <= '\ud7a3' for c in text):
            self.src_lang_combo.setCurrentText("한국어")
            # 한국어면 타겟을 영어로
            self.tgt_lang_combo.setCurrentText("영어")
        # 일본어 히라가나/가타카나가 있으면 일본어
        elif any('\u3040' <= c <= '\u30ff' for c in text):
            self.src_lang_combo.setCurrentText("일본어")
            self.tgt_lang_combo.setCurrentText("한국어")
        # 중국어 간체/번체 (CJK Unified Ideographs만 있고 히라가나/한글 없으면)
        elif any('\u4e00' <= c <= '\u9fff' for c in text):
            self.src_lang_combo.setCurrentText("중국어 (간체)")
            self.tgt_lang_combo.setCurrentText("한국어")
        # 그 외는 영어로 가정
        else:
            self.src_lang_combo.setCurrentText("영어")
            self.tgt_lang_combo.setCurrentText("한국어")

    def do_translate(self):
        """번역 실행"""
        src_text = self.src_text.toPlainText().strip()
        if not src_text:
            self.statusBar().showMessage("번역할 텍스트를 입력하세요")
            return

        src_lang = LANGUAGES[self.src_lang_combo.currentText()]
        tgt_lang = LANGUAGES[self.tgt_lang_combo.currentText()]
        model = MODELS[self.model_combo.currentText()]

        self.translate_btn.setEnabled(False)
        self.statusBar().showMessage(f"번역 중... ({self.model_combo.currentText()})")
        self.tgt_text.clear()

        # 백그라운드에서 번역 실행
        thread = threading.Thread(
            target=self.run_translation,
            args=(src_text, src_lang, tgt_lang, model)
        )
        thread.daemon = True
        thread.start()

    def run_translation(self, text, src_lang, tgt_lang, model):
        """Claude를 이용한 번역 (백그라운드 스레드)"""
        try:
            if src_lang == "auto":
                prompt = f'Translate the following text to {tgt_lang}. Only output the translation, nothing else:\n\n{text}'
            else:
                prompt = f'Translate the following {src_lang} text to {tgt_lang}. Only output the translation, nothing else:\n\n{text}'

            result = subprocess.run(
                ['claude', '-p', prompt, '--model', model],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                translation = result.stdout.strip()
                self.signal_emitter.translation_done.emit(translation)
            else:
                error = result.stderr.strip() or "번역 실패"
                self.signal_emitter.translation_error.emit(error)

        except subprocess.TimeoutExpired:
            self.signal_emitter.translation_error.emit("번역 시간 초과 (60초)")
        except Exception as e:
            self.signal_emitter.translation_error.emit(str(e))

    def on_translation_done(self, translation):
        """번역 완료"""
        self.tgt_text.setText(translation)
        self.translate_btn.setEnabled(True)
        self.statusBar().showMessage("번역 완료")

    def on_translation_error(self, error):
        """번역 에러"""
        self.tgt_text.setText(f"오류: {error}")
        self.translate_btn.setEnabled(True)
        self.statusBar().showMessage("번역 실패")

    def clear_texts(self):
        """텍스트 지우기"""
        self.src_text.clear()
        self.tgt_text.clear()
        self.statusBar().showMessage("준비됨")

    def copy_result(self):
        """번역 결과 복사"""
        result = self.tgt_text.toPlainText()
        if result:
            clipboard = QApplication.clipboard()
            clipboard.setText(result)
            self.statusBar().showMessage("결과가 클립보드에 복사되었습니다")
        else:
            self.statusBar().showMessage("복사할 내용이 없습니다")

    def closeEvent(self, event):
        """창 닫기 시 트레이로 최소화"""
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "CC2Translate",
            f"프로그램이 트레이에서 실행 중입니다. {self.shortcut_text} 두 번으로 번역할 수 있습니다.",
            QSystemTrayIcon.Information,
            2000
        )

    def quit_app(self):
        """프로그램 완전 종료"""
        self.listener.stop()
        self.tray_icon.hide()
        QApplication.quit()


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # 트레이에서 계속 실행

    window = TranslatorWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
