"""메인 윈도우 UI - TranslatorWindow 클래스"""

import os
import threading

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QComboBox, QLabel, QPushButton, QSplitter, QSlider,
    QSystemTrayIcon, QMenu, QAction, QDialog, QDialogButtonBox,
    QListWidget, QListWidgetItem, QLineEdit, QMessageBox,
)
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QTimer
from PyQt5.QtGui import QFont

from constants import LANGUAGES, ALL_MODELS, GEMINI_API_MODELS, DEEPL_API_MODELS, IS_MACOS
from translator import translate, TranslationError
from hotkey import HotkeyListener
import history
import updater


class EnvGuideDialog(QDialog):
    """API 키 환경변수 설정 안내 다이얼로그"""
    def __init__(self, key_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle("API 키 설정 안내")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        guide = QLabel(
            f"<b>{key_name}</b> 환경변수가 설정되지 않았습니다.<br><br>"
            f"셸 설정 파일(~/.zshrc 또는 ~/.bashrc)에 다음을 추가하세요:<br><br>"
            f"<code>export {key_name}=\"your-api-key\"</code><br><br>"
            f"추가 후 터미널을 재시작하거나 <code>source ~/.zshrc</code>를 실행하세요."
        )
        guide.setTextFormat(Qt.RichText)
        guide.setWordWrap(True)
        guide.setStyleSheet("padding: 10px;")
        guide.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(guide)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)


class SignalEmitter(QObject):
    """스레드 간 시그널 전달용"""
    show_window = pyqtSignal()
    translation_done = pyqtSignal(str)
    translation_error = pyqtSignal(str)
    update_available = pyqtSignal(str)  # remote_sha
    update_progress = pyqtSignal(str)   # progress message
    update_done = pyqtSignal()
    update_error = pyqtSignal(str)      # error message


class TranslatorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.signal_emitter = SignalEmitter()
        self.signal_emitter.show_window.connect(self.show_and_activate)
        self.signal_emitter.translation_done.connect(self._on_translation_done)
        self.signal_emitter.translation_error.connect(self._on_translation_error)
        self.signal_emitter.update_available.connect(self._on_update_available)
        self.signal_emitter.update_progress.connect(self._on_update_progress)
        self.signal_emitter.update_done.connect(self._on_update_done)
        self.signal_emitter.update_error.connect(self._on_update_error)

        self.shortcut_text = "Cmd+C" if IS_MACOS else "Ctrl+C"
        self._updating = False
        self._suppress_auto_translate = False

        self._init_ui()
        self._setup_hotkey()
        self._setup_tray()
        self._setup_auto_translate()
        self._check_for_update()

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

        self.history_btn = QPushButton("기록")
        self.history_btn.clicked.connect(self._toggle_history)
        self.history_btn.setStyleSheet("""
            QPushButton {
                background-color: #e0e0e0; color: #333;
                border: none; border-radius: 3px; padding: 5px 15px;
            }
            QPushButton:hover { background-color: #d0d0d0; }
        """)
        toolbar.addWidget(self.history_btn)

        self.settings_btn = QPushButton("설정")
        self.settings_btn.clicked.connect(self._show_settings)
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #e0e0e0; color: #333;
                border: none; border-radius: 3px; padding: 5px 15px;
            }
            QPushButton:hover { background-color: #d0d0d0; }
        """)
        toolbar.addWidget(self.settings_btn)

    def _init_text_area(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(5, 5, 5, 5)

        self.outer_splitter = QSplitter(Qt.Horizontal)

        # 히스토리 패널
        self._init_history_panel()
        self.outer_splitter.addWidget(self.history_panel)

        # 번역 영역
        splitter = QSplitter(Qt.Horizontal)

        self.src_text = QTextEdit()
        self.src_text.setPlaceholderText(f"원본 텍스트 입력 (1초 후 자동 번역 / {self.shortcut_text} 두 번으로 클립보드에서 가져오기)")
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

        self.outer_splitter.addWidget(splitter)
        self.history_panel.hide()
        self.outer_splitter.setSizes([0, 900])
        main_layout.addWidget(self.outer_splitter, 1)

        # 글자 크기 슬라이더 (하단 컴팩트)
        slider_layout = QHBoxLayout()
        slider_layout.setContentsMargins(5, 0, 5, 0)
        slider_layout.setSpacing(4)

        small_label = QLabel("A")
        small_label.setFont(QFont("Sans", 7))
        small_label.setStyleSheet("color: #888;")
        slider_layout.addWidget(small_label)

        self.font_slider = QSlider(Qt.Horizontal)
        self.font_slider.setRange(8, 24)
        self.font_slider.setValue(11)
        self.font_slider.setMaximumWidth(120)
        self.font_slider.setFixedHeight(16)
        self.font_slider.valueChanged.connect(self._on_font_size_changed)
        slider_layout.addWidget(self.font_slider)

        big_label = QLabel("A")
        big_label.setFont(QFont("Sans", 11))
        big_label.setStyleSheet("color: #888;")
        slider_layout.addWidget(big_label)

        self.font_size_label = QLabel("11pt")
        self.font_size_label.setStyleSheet("color: #888; font-size: 10px;")
        slider_layout.addWidget(self.font_size_label)

        slider_layout.addStretch()
        main_layout.addLayout(slider_layout)

    def _init_history_panel(self):
        self.history_panel = QWidget()
        layout = QVBoxLayout(self.history_panel)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        header = QLabel("번역 기록")
        header.setFont(QFont("Sans", 12, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        self.history_search = QLineEdit()
        self.history_search.setPlaceholderText("검색...")
        self.history_search.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ccc; border-radius: 3px; padding: 5px;
            }
        """)
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(300)
        self._search_timer.timeout.connect(self._on_history_search)
        self.history_search.textChanged.connect(lambda: self._search_timer.start())
        layout.addWidget(self.history_search)

        self.history_list = QListWidget()
        self.history_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc; border-radius: 3px;
            }
            QListWidget::item {
                padding: 6px; border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #d0e4f7;
            }
        """)
        self.history_list.itemClicked.connect(self._on_history_item_clicked)
        self.history_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.history_list.customContextMenuRequested.connect(self._on_history_context_menu)
        layout.addWidget(self.history_list)

        clear_all_btn = QPushButton("전체 삭제")
        clear_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #d9534f; color: white;
                border: none; border-radius: 3px; padding: 5px 15px;
            }
            QPushButton:hover { background-color: #c9302c; }
        """)
        clear_all_btn.clicked.connect(self._delete_all_history)
        layout.addWidget(clear_all_btn)

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

    # ── 자동 번역 (debounce) ──────────────────────────────

    def _setup_auto_translate(self):
        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(1000)
        self._debounce_timer.timeout.connect(self._on_auto_translate)
        self.src_text.textChanged.connect(self._on_src_text_changed)

    def _on_src_text_changed(self):
        if self._suppress_auto_translate:
            return
        self._debounce_timer.start()

    def _on_auto_translate(self):
        if self._suppress_auto_translate:
            return
        if not self.translate_btn.isEnabled():
            return
        text = self.src_text.toPlainText().strip()
        if not text:
            return
        self._detect_language(text)
        self.do_translate()

    # ── 번역 ───────────────────────────────────────────────

    def show_and_activate(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text:
            self._suppress_auto_translate = True
            self.src_text.setText(text)
            self._suppress_auto_translate = False
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

        if not self._check_api_key(model):
            return

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
        self._suppress_auto_translate = True
        self.tgt_text.setText(translation)
        self._suppress_auto_translate = False
        self.translate_btn.setEnabled(True)
        self.statusBar().showMessage("번역 완료")

        src_text = self.src_text.toPlainText().strip()
        if src_text and translation:
            history.add_entry(
                src_text,
                translation,
                self.src_lang_combo.currentText(),
                self.tgt_lang_combo.currentText(),
                self.model_combo.currentText(),
            )
            if self.history_panel.isVisible():
                self._load_history()

    def _on_translation_error(self, error):
        self.tgt_text.setText(f"오류: {error}")
        self.translate_btn.setEnabled(True)
        self.statusBar().showMessage("번역 실패")

    # ── 설정 ──────────────────────────────────────────────

    def _show_settings(self):
        gemini_status = "설정됨" if os.environ.get("GEMINI_API_KEY") else "미설정"
        deepl_status = "설정됨" if os.environ.get("DEEPL_API_KEY") else "미설정"
        dialog = EnvGuideDialog("GEMINI_API_KEY / DEEPL_API_KEY", self)
        dialog.setWindowTitle("API 키 상태")
        dialog.findChild(QLabel).setText(
            f"<b>API 키 상태</b><br><br>"
            f"GEMINI_API_KEY: {gemini_status}<br>"
            f"DEEPL_API_KEY: {deepl_status}<br><br>"
            f"셸 설정 파일(~/.zshrc 또는 ~/.bashrc)에서 환경변수를 설정하세요:<br><br>"
            f"<code>export GEMINI_API_KEY=\"your-key\"</code><br>"
            f"<code>export DEEPL_API_KEY=\"your-key\"</code><br><br>"
            f"설정 후 앱을 재시작하세요."
        )
        dialog.exec_()

    def _check_api_key(self, model):
        """API 모델 선택 시 환경변수에 키가 없으면 안내 다이얼로그를 표시."""
        if model in GEMINI_API_MODELS.values() and not os.environ.get("GEMINI_API_KEY"):
            self.statusBar().showMessage("GEMINI_API_KEY 환경변수가 필요합니다")
            EnvGuideDialog("GEMINI_API_KEY", self).exec_()
            return False
        if model in DEEPL_API_MODELS.values() and not os.environ.get("DEEPL_API_KEY"):
            self.statusBar().showMessage("DEEPL_API_KEY 환경변수가 필요합니다")
            EnvGuideDialog("DEEPL_API_KEY", self).exec_()
            return False
        return True

    # ── 히스토리 ─────────────────────────────────────────────

    def _toggle_history(self):
        if self.history_panel.isVisible():
            self.history_panel.hide()
            self.outer_splitter.setSizes([0, 900])
        else:
            self._load_history()
            self.history_panel.show()
            self.outer_splitter.setSizes([250, 650])

    def _load_history(self):
        search = self.history_search.text().strip()
        entries = history.get_entries(search)
        self.history_list.clear()
        for entry in entries:
            preview = entry["src_text"][:60].replace("\n", " ")
            if len(entry["src_text"]) > 60:
                preview += "…"
            time_str = self._format_time(entry["created_at"])
            label = f"{preview}\n{entry['model']} | {entry['tgt_lang']} | {time_str}"
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, entry)
            self.history_list.addItem(item)

    def _on_history_item_clicked(self, item):
        entry = item.data(Qt.UserRole)
        self._suppress_auto_translate = True
        self.src_text.setText(entry["src_text"])
        self._suppress_auto_translate = False
        self.tgt_text.setText(entry["tgt_text"])
        # 모델/언어 복원
        idx = self.model_combo.findText(entry["model"])
        if idx >= 0:
            self.model_combo.setCurrentIndex(idx)
        idx = self.src_lang_combo.findText(entry["src_lang"])
        if idx >= 0:
            self.src_lang_combo.setCurrentIndex(idx)
        idx = self.tgt_lang_combo.findText(entry["tgt_lang"])
        if idx >= 0:
            self.tgt_lang_combo.setCurrentIndex(idx)
        self.statusBar().showMessage("기록에서 복원됨")

    def _on_history_search(self):
        self._load_history()

    def _on_history_context_menu(self, pos):
        item = self.history_list.itemAt(pos)
        if not item:
            return
        menu = QMenu(self)
        delete_action = menu.addAction("삭제")
        action = menu.exec_(self.history_list.mapToGlobal(pos))
        if action == delete_action:
            entry = item.data(Qt.UserRole)
            history.delete_entry(entry["id"])
            self._load_history()

    def _delete_all_history(self):
        history.delete_all()
        self.history_list.clear()
        self.statusBar().showMessage("모든 기록이 삭제되었습니다")

    @staticmethod
    def _format_time(timestamp):
        from datetime import datetime
        try:
            dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%m/%d %H:%M")
        except (ValueError, TypeError):
            return timestamp or ""

    # ── 자동 업데이트 ────────────────────────────────────────

    def _check_for_update(self):
        """백그라운드에서 업데이트를 확인한다."""
        def _worker():
            has_update, remote_sha, _error = updater.check_for_update()
            if has_update and remote_sha:
                self.signal_emitter.update_available.emit(remote_sha)

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

    def _on_update_available(self, remote_sha):
        msg = QMessageBox(self)
        msg.setWindowTitle("업데이트")
        msg.setText("새로운 업데이트가 있습니다.\n업데이트를 설치하시겠습니까?")
        update_btn = msg.addButton("업데이트", QMessageBox.AcceptRole)
        msg.addButton("나중에", QMessageBox.RejectRole)
        skip_btn = msg.addButton("이 버전 건너뛰기", QMessageBox.DestructiveRole)

        msg.exec_()
        clicked = msg.clickedButton()

        if clicked == update_btn:
            self._start_update()
        elif clicked == skip_btn:
            updater.skip_version(remote_sha)

    def _start_update(self):
        self._updating = True
        updater.run_update(
            on_progress=lambda msg: self.signal_emitter.update_progress.emit(msg),
            on_done=lambda: self.signal_emitter.update_done.emit(),
            on_error=lambda err: self.signal_emitter.update_error.emit(err),
        )

    def _on_update_progress(self, message):
        self.statusBar().showMessage(message)

    def _on_update_done(self):
        self._updating = False
        msg = QMessageBox(self)
        msg.setWindowTitle("업데이트 완료")
        msg.setText("업데이트가 완료되었습니다.\n앱을 재시작하시겠습니까?")
        restart_btn = msg.addButton("재시작", QMessageBox.AcceptRole)
        msg.addButton("나중에", QMessageBox.RejectRole)

        msg.exec_()
        if msg.clickedButton() == restart_btn:
            self._restart_app()
        else:
            self.statusBar().showMessage("업데이트 완료 - 다음 실행 시 적용됩니다")

    def _on_update_error(self, error):
        self._updating = False
        QMessageBox.warning(self, "업데이트 실패", error)
        self.statusBar().showMessage(f"준비됨 - {self.shortcut_text} 두 번으로 번역")

    def _restart_app(self):
        import subprocess
        cmd = updater.get_restart_command()
        subprocess.Popen(cmd)
        self._quit_app(force=True)

    # ── 글자 크기 ──────────────────────────────────────────

    def _on_font_size_changed(self, value):
        font = QFont("Sans", value)
        self.src_text.setFont(font)
        self.tgt_text.setFont(font)
        self.font_size_label.setText(f"{value}pt")

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
        if self._updating:
            QMessageBox.information(
                self, "업데이트 중",
                "업데이트가 진행 중입니다. 완료될 때까지 기다려주세요."
            )
            event.ignore()
            return

        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "CC2Translate",
            f"프로그램이 트레이에서 실행 중입니다. {self.shortcut_text} 두 번으로 번역할 수 있습니다.",
            QSystemTrayIcon.Information,
            2000
        )

    def _quit_app(self, force=False):
        if self._updating and not force:
            QMessageBox.information(
                self, "업데이트 중",
                "업데이트가 진행 중입니다. 완료될 때까지 기다려주세요."
            )
            return
        self.hotkey_listener.stop()
        self.tray_icon.hide()
        QApplication.quit()
