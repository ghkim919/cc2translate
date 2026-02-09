"""메인 윈도우 UI - TranslatorWindow 클래스"""

import threading

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QTextEdit, QComboBox, QLabel, QPushButton, QSplitter,
    QSystemTrayIcon, QMenu, QAction,
)
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtGui import QFont

from constants import LANGUAGES, ALL_MODELS, IS_MACOS
from translator import translate, TranslationError
from hotkey import HotkeyListener


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
        self.signal_emitter.translation_done.connect(self._on_translation_done)
        self.signal_emitter.translation_error.connect(self._on_translation_error)

        self.shortcut_text = "Cmd+C" if IS_MACOS else "Ctrl+C"

        self._init_ui()
        self._setup_hotkey()
        self._setup_tray()

    # ── UI 초기화 ──────────────────────────────────────────

    def _init_ui(self):
        self.setWindowTitle("CC2Translate - Claude 번역기")
        self.setGeometry(100, 100, 900, 600)
        self.setMinimumSize(600, 400)

        self._init_toolbar()
        self._init_text_area()

        self.statusBar().showMessage(f"준비됨 - {self.shortcut_text} 두 번으로 번역")

    def _init_toolbar(self):
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
        toolbar.addWidget(QLabel(" 모델:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(ALL_MODELS.keys())
        self.model_combo.setCurrentText("Claude Haiku (빠름)")
        self.model_combo.setMinimumWidth(120)
        toolbar.addWidget(self.model_combo)

        toolbar.addSeparator()

        # 소스 언어
        toolbar.addWidget(QLabel(" 원본:"))
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
        toolbar.addWidget(QLabel("번역:"))
        self.tgt_lang_combo = QComboBox()
        tgt_langs = [k for k in LANGUAGES.keys() if k != "자동 감지"]
        self.tgt_lang_combo.addItems(tgt_langs)
        self.tgt_lang_combo.setCurrentText("한국어")
        self.tgt_lang_combo.setMinimumWidth(100)
        toolbar.addWidget(self.tgt_lang_combo)

        # 스페이서
        spacer = QWidget()
        spacer.setMinimumWidth(20)
        toolbar.addWidget(spacer)

        toolbar.addSeparator()

        # 버튼들
        self.clear_btn = QPushButton("지우기")
        self.clear_btn.clicked.connect(self._clear_texts)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #e0e0e0; color: #333;
                border: none; border-radius: 3px; padding: 5px 15px;
            }
            QPushButton:hover { background-color: #d0d0d0; }
        """)
        toolbar.addWidget(self.clear_btn)

        self.copy_btn = QPushButton("복사")
        self.copy_btn.clicked.connect(self._copy_result)
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #5cb85c; color: white;
                border: none; border-radius: 3px; padding: 5px 15px;
            }
            QPushButton:hover { background-color: #4cae4c; }
        """)
        toolbar.addWidget(self.copy_btn)

        self.translate_btn = QPushButton("번역")
        self.translate_btn.clicked.connect(self.do_translate)
        self.translate_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a90d9; color: white;
                border: none; border-radius: 3px; padding: 5px 15px;
            }
            QPushButton:hover { background-color: #357abd; }
            QPushButton:disabled { background-color: #cccccc; }
        """)
        toolbar.addWidget(self.translate_btn)

    def _init_text_area(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(5, 5, 5, 5)

        splitter = QSplitter(Qt.Horizontal)

        self.src_text = QTextEdit()
        self.src_text.setPlaceholderText(f"원본 텍스트 ({self.shortcut_text} 두 번으로 클립보드에서 가져오기)")
        self.src_text.setFont(QFont("Sans", 11))
        self.src_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ccc; border-radius: 5px; padding: 10px;
            }
        """)

        self.tgt_text = QTextEdit()
        self.tgt_text.setPlaceholderText("번역 결과")
        self.tgt_text.setReadOnly(True)
        self.tgt_text.setFont(QFont("Sans", 11))
        self.tgt_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ccc; border-radius: 5px; padding: 10px;
                background-color: #fafafa;
            }
        """)

        splitter.addWidget(self.src_text)
        splitter.addWidget(self.tgt_text)
        splitter.setSizes([450, 450])
        main_layout.addWidget(splitter)

    # ── 시스템 트레이 ──────────────────────────────────────

    def _setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(self.style().SP_ComputerIcon))

        tray_menu = QMenu()
        show_action = QAction("창 보이기", self)
        show_action.triggered.connect(self.show_and_activate)
        quit_action = QAction("종료", self)
        quit_action.triggered.connect(self._quit_app)

        tray_menu.addAction(show_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._tray_activated)
        self.tray_icon.show()

    def _tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_and_activate()

    # ── 핫키 ───────────────────────────────────────────────

    def _setup_hotkey(self):
        self.hotkey_listener = HotkeyListener(
            on_double_copy=lambda: threading.Timer(0.1, self._trigger_show).start()
        )
        self.hotkey_listener.start()

    def _trigger_show(self):
        self.signal_emitter.show_window.emit()

    # ── 번역 ───────────────────────────────────────────────

    def show_and_activate(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text:
            self.src_text.setText(text)
            self._detect_language(text)

        self.show()
        self.activateWindow()
        self.raise_()

        if text:
            self.do_translate()

    def _detect_language(self, text):
        """텍스트 언어 감지 (간단한 휴리스틱)"""
        if any('\uac00' <= c <= '\ud7a3' for c in text):
            self.src_lang_combo.setCurrentText("한국어")
            self.tgt_lang_combo.setCurrentText("영어")
        elif any('\u3040' <= c <= '\u30ff' for c in text):
            self.src_lang_combo.setCurrentText("일본어")
            self.tgt_lang_combo.setCurrentText("한국어")
        elif any('\u4e00' <= c <= '\u9fff' for c in text):
            self.src_lang_combo.setCurrentText("중국어 (간체)")
            self.tgt_lang_combo.setCurrentText("한국어")
        else:
            self.src_lang_combo.setCurrentText("영어")
            self.tgt_lang_combo.setCurrentText("한국어")

    def do_translate(self):
        src_text = self.src_text.toPlainText().strip()
        if not src_text:
            self.statusBar().showMessage("번역할 텍스트를 입력하세요")
            return

        src_lang = LANGUAGES[self.src_lang_combo.currentText()]
        tgt_lang = LANGUAGES[self.tgt_lang_combo.currentText()]
        model = ALL_MODELS[self.model_combo.currentText()]

        self.translate_btn.setEnabled(False)
        self.statusBar().showMessage(f"번역 중... ({self.model_combo.currentText()})")
        self.tgt_text.clear()

        thread = threading.Thread(
            target=self._run_translation,
            args=(src_text, src_lang, tgt_lang, model)
        )
        thread.daemon = True
        thread.start()

    def _run_translation(self, text, src_lang, tgt_lang, model):
        try:
            result = translate(text, src_lang, tgt_lang, model)
            self.signal_emitter.translation_done.emit(result)
        except TranslationError as e:
            self.signal_emitter.translation_error.emit(str(e))
        except Exception as e:
            self.signal_emitter.translation_error.emit(str(e))

    def _on_translation_done(self, translation):
        self.tgt_text.setText(translation)
        self.translate_btn.setEnabled(True)
        self.statusBar().showMessage("번역 완료")

    def _on_translation_error(self, error):
        self.tgt_text.setText(f"오류: {error}")
        self.translate_btn.setEnabled(True)
        self.statusBar().showMessage("번역 실패")

    # ── 기타 액션 ──────────────────────────────────────────

    def _clear_texts(self):
        self.src_text.clear()
        self.tgt_text.clear()
        self.statusBar().showMessage("준비됨")

    def _copy_result(self):
        result = self.tgt_text.toPlainText()
        if result:
            QApplication.clipboard().setText(result)
            self.statusBar().showMessage("결과가 클립보드에 복사되었습니다")
        else:
            self.statusBar().showMessage("복사할 내용이 없습니다")

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "CC2Translate",
            f"프로그램이 트레이에서 실행 중입니다. {self.shortcut_text} 두 번으로 번역할 수 있습니다.",
            QSystemTrayIcon.Information,
            2000
        )

    def _quit_app(self):
        self.hotkey_listener.stop()
        self.tray_icon.hide()
        QApplication.quit()
