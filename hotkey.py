"""글로벌 핫키 리스너 - Ctrl+C / Cmd+C 두 번 감지"""

import time

from constants import IS_MACOS

if IS_MACOS:
    import Quartz


class HotkeyListener:
    """복사 단축키 더블 프레스를 감지하여 콜백을 호출하는 리스너"""

    def __init__(self, on_double_copy):
        self.on_double_copy = on_double_copy
        self.last_copy_time = 0

    def start(self):
        if IS_MACOS:
            self._start_macos()
        else:
            self._start_linux()

    def stop(self):
        if IS_MACOS:
            self._stop_macos()
        else:
            self._stop_linux()

    # ── macOS: Quartz CGEventTap (메인 RunLoop에서 실행) ──

    def _start_macos(self):
        self._cmd_pressed = False
        mask = (
            Quartz.CGEventMaskBit(Quartz.kCGEventKeyDown) |
            Quartz.CGEventMaskBit(Quartz.kCGEventFlagsChanged)
        )
        self._tap = Quartz.CGEventTapCreate(
            Quartz.kCGSessionEventTap,
            Quartz.kCGHeadInsertEventTap,
            Quartz.kCGEventTapOptionListenOnly,
            mask,
            self._cg_event_callback,
            None
        )
        if self._tap is None:
            return

        source = Quartz.CFMachPortCreateRunLoopSource(None, self._tap, 0)
        Quartz.CFRunLoopAddSource(
            Quartz.CFRunLoopGetMain(),
            source,
            Quartz.kCFRunLoopCommonModes
        )
        Quartz.CGEventTapEnable(self._tap, True)

    def _cg_event_callback(self, proxy, event_type, event, refcon):
        try:
            if event_type == Quartz.kCGEventFlagsChanged:
                flags = Quartz.CGEventGetFlags(event)
                self._cmd_pressed = bool(flags & Quartz.kCGEventFlagMaskCommand)
            elif event_type == Quartz.kCGEventKeyDown and self._cmd_pressed:
                keycode = Quartz.CGEventGetIntegerValueField(
                    event, Quartz.kCGKeyboardEventKeycode
                )
                if keycode == 8:  # 'c' key
                    now = time.time()
                    if now - self.last_copy_time < 0.5:
                        self.last_copy_time = 0
                        self.on_double_copy()
                    else:
                        self.last_copy_time = now
        except Exception:
            pass
        return event

    def _stop_macos(self):
        if hasattr(self, '_tap') and self._tap:
            Quartz.CGEventTapEnable(self._tap, False)

    # ── Linux: pynput ──

    def _start_linux(self):
        from pynput import keyboard
        self._ctrl_pressed = False
        self._listener = keyboard.Listener(
            on_press=self._on_press_linux,
            on_release=self._on_release_linux
        )
        self._listener.daemon = True
        self._listener.start()

    def _on_press_linux(self, key):
        from pynput import keyboard
        try:
            if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
                self._ctrl_pressed = True
                return
            if hasattr(key, 'char') and key.char == 'c' and self._ctrl_pressed:
                now = time.time()
                if now - self.last_copy_time < 0.5:
                    self.last_copy_time = 0
                    self.on_double_copy()
                else:
                    self.last_copy_time = now
        except Exception:
            pass

    def _on_release_linux(self, key):
        from pynput import keyboard
        try:
            if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
                self._ctrl_pressed = False
        except Exception:
            pass

    def _stop_linux(self):
        if hasattr(self, '_listener'):
            self._listener.stop()
