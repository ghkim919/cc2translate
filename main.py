#!/usr/bin/env python3
"""CC2Translate - Ctrl+C (macOS: Cmd+C) 두 번으로 번역하는 GUI 프로그램"""

import sys

from PyQt5.QtWidgets import QApplication
from PyQt5.QtNetwork import QLocalServer, QLocalSocket

from constants import IS_MACOS
from window import TranslatorWindow

APP_ID = "cc2translate-single-instance"


def is_already_running():
    """이미 실행 중인 인스턴스가 있는지 확인하고, 있으면 활성화 신호를 보냄"""
    socket = QLocalSocket()
    socket.connectToServer(APP_ID)
    if socket.waitForConnected(500):
        socket.close()
        return True
    return False


def check_accessibility():
    """macOS에서 Accessibility 권한이 없으면 시스템 다이얼로그를 띄우고 허용될 때까지 대기"""
    if not IS_MACOS:
        return
    from ApplicationServices import AXIsProcessTrustedWithOptions
    from CoreFoundation import kCFBooleanTrue, kCFBooleanFalse

    trusted = AXIsProcessTrustedWithOptions({
        "AXTrustedCheckOptionPrompt": kCFBooleanTrue
    })
    if trusted:
        return

    from PyQt5.QtWidgets import QMessageBox, QPushButton
    msg = QMessageBox()
    msg.setWindowTitle("CC2Translate")
    msg.setText(
        "손쉬운 사용(Accessibility) 권한이 필요합니다.\n"
        "시스템 설정에서 CC2Translate을 허용한 후\n"
        "아래 '권한 확인' 버튼을 눌러주세요."
    )
    retry_btn = msg.addButton("권한 확인", QMessageBox.AcceptRole)
    quit_btn = msg.addButton("종료", QMessageBox.RejectRole)

    while True:
        msg.exec_()
        if msg.clickedButton() == quit_btn:
            sys.exit(0)
        # 프롬프트 없이 현재 상태만 확인
        if AXIsProcessTrustedWithOptions({"AXTrustedCheckOptionPrompt": kCFBooleanFalse}):
            break
        msg.setText(
            "아직 권한이 감지되지 않았습니다.\n"
            "시스템 설정 > 손쉬운 사용에서 CC2Translate을 허용해주세요.\n\n"
            "허용 후 '권한 확인' 버튼을 눌러주세요."
        )


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    check_accessibility()

    if is_already_running():
        print("CC2Translate가 이미 실행 중입니다.")
        sys.exit(0)

    # 이전 비정상 종료로 남은 소켓 정리
    QLocalServer.removeServer(APP_ID)

    server = QLocalServer()
    server.listen(APP_ID)

    window = TranslatorWindow()

    # 다른 인스턴스가 접속하면 기존 창 활성화
    server.newConnection.connect(lambda: (
        server.nextPendingConnection().close(),
        window.show_and_activate(),
    ))

    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
