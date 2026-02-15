"""UI 스타일시트 중앙 관리"""

TOOLBAR = """
    QToolBar {
        background: #f5f5f5;
        border-bottom: 1px solid #ddd;
        padding: 5px;
        spacing: 10px;
    }
"""

BUTTON_DEFAULT = """
    QPushButton {
        background-color: #e0e0e0; color: #333;
        border: none; border-radius: 3px; padding: 5px 15px;
    }
    QPushButton:hover { background-color: #d0d0d0; }
"""

BUTTON_PRIMARY = """
    QPushButton {
        background-color: #4a90d9; color: white;
        border: none; border-radius: 3px; padding: 5px 15px;
    }
    QPushButton:hover { background-color: #357abd; }
    QPushButton:disabled { background-color: #cccccc; }
"""

BUTTON_SUCCESS = """
    QPushButton {
        background-color: #5cb85c; color: white;
        border: none; border-radius: 3px; padding: 5px 15px;
    }
    QPushButton:hover { background-color: #4cae4c; }
"""

BUTTON_DANGER = """
    QPushButton {
        background-color: #d9534f; color: white;
        border: none; border-radius: 3px; padding: 5px 15px;
    }
    QPushButton:hover { background-color: #c9302c; }
"""

TEXT_INPUT = """
    QTextEdit {
        border: 1px solid #ccc; border-radius: 5px; padding: 10px;
    }
"""

TEXT_OUTPUT = """
    QTextEdit {
        border: 1px solid #ccc; border-radius: 5px; padding: 10px;
        background-color: #fafafa;
    }
"""

LINE_EDIT = """
    QLineEdit {
        border: 1px solid #ccc; border-radius: 3px; padding: 5px;
    }
"""

HISTORY_LIST = """
    QListWidget {
        border: 1px solid #ccc; border-radius: 3px;
    }
    QListWidget::item {
        padding: 6px; border-bottom: 1px solid #eee;
    }
    QListWidget::item:selected {
        background-color: #d0e4f7;
    }
"""
