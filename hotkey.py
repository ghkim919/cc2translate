"""글로벌 핫키 리스너 - Ctrl+C / Cmd+C 두 번 감지"""

import time

from pynput import keyboard

from constants import IS_MACOS


class HotkeyListener:
    """복사 단축키 더블 프레스를 감지하여 콜백을 호출하는 리스너"""

    def __init__(self, on_double_copy):
        self.on_double_copy = on_double_copy
        self.last_copy_time = 0
        self.modifier_pressed = False
        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self.listener.daemon = True

    def start(self):
        self.listener.start()

    def stop(self):
        self.listener.stop()

    def _on_press(self, key):
        try:
            if IS_MACOS:
                if key in (keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r):
                    self.modifier_pressed = True
            else:
                if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
                    self.modifier_pressed = True
        except Exception:
            pass

    def _on_release(self, key):
        try:
            if IS_MACOS:
                if key in (keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r):
                    self.modifier_pressed = False
            else:
                if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
                    self.modifier_pressed = False

            if hasattr(key, 'char') and key.char == 'c' and self.modifier_pressed:
                current_time = time.time()
                if current_time - self.last_copy_time < 0.5:
                    self.last_copy_time = 0
                    self.on_double_copy()
                else:
                    self.last_copy_time = current_time
        except Exception:
            pass
