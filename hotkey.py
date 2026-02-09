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

    def _is_c_key(self, key):
        if not hasattr(key, 'char') or key.char is None:
            return False
        # macOS에서 Cmd+C를 누르면 char가 '\x03' (ETX)으로 전달됨
        if IS_MACOS:
            return key.char in ('c', '\x03')
        return key.char == 'c'

    def _on_press(self, key):
        try:
            if IS_MACOS:
                if key in (keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r):
                    self.modifier_pressed = True
                    return
            else:
                if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
                    self.modifier_pressed = True
                    return

            # press 시점에서 감지 (release에서 하면 modifier 해제 순서 문제 발생)
            if self._is_c_key(key) and self.modifier_pressed:
                current_time = time.time()
                if current_time - self.last_copy_time < 0.5:
                    self.last_copy_time = 0
                    self.on_double_copy()
                else:
                    self.last_copy_time = current_time
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
        except Exception:
            pass
