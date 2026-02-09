#!/usr/bin/env python3
"""CC2Translate - Ctrl+C (macOS: Cmd+C) 두 번으로 번역하는 GUI 프로그램"""

import sys

from PyQt5.QtWidgets import QApplication
from PyQt5.QtNetwork import QLocalServer, QLocalSocket

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


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

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
