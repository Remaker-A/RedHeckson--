"""
动作回放引擎 - 独立线程播放动作序列
"""

import threading
import time


class PlaybackEngine(threading.Thread):
    def __init__(self, packets: list, worker, done_cb):
        super().__init__(daemon=True)
        self.packets = packets
        self.worker = worker
        self.done_cb = done_cb
        self._stop_event = threading.Event()
        self.progress = 0.0

    def stop(self):
        self._stop_event.set()

    def run(self):
        if not self.packets:
            self.done_cb()
            return
        t_start = time.monotonic() * 1000
        total = self.packets[-1][0] or 1
        idx = 0

        while idx < len(self.packets) and not self._stop_event.is_set():
            now_ms = time.monotonic() * 1000 - t_start
            while idx < len(self.packets) and self.packets[idx][0] <= now_ms:
                self.worker.send_raw(self.packets[idx][1])
                idx += 1
            self.progress = min(1.0, now_ms / total)
            time.sleep(0.005)

        self.progress = 1.0
        if not self._stop_event.is_set():
            self.done_cb()
