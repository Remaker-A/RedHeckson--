"""
串口通信后台线程 - 处理收发
"""

import threading
import queue
import time
import serial
from .constants import BAUD_RATE
from .protocol import parse_ack


class SerialWorker(threading.Thread):
    def __init__(self, port: str, log_q: queue.Queue):
        super().__init__(daemon=True)
        self.port = port
        self.log_q = log_q
        self.send_q: queue.Queue[bytes] = queue.Queue()
        self._ser = None
        self._stop_event = threading.Event()

    def send(self, cmd: int, val: int = 0):
        from .protocol import build_packet

        self.send_q.put(build_packet(cmd, val))

    def send_raw(self, pkt: bytes):
        self.send_q.put(pkt)

    def stop(self):
        self._stop_event.set()

    def run(self):
        try:
            self._ser = serial.Serial(self.port, BAUD_RATE, timeout=0.05)
            time.sleep(1.6)
            self.log_q.put(("ok", f"已连接 {self.port} @ {BAUD_RATE}"))
        except serial.SerialException as e:
            self.log_q.put(("err", f"串口打开失败: {e}"))
            return

        rx_buf = bytearray()
        while not self._stop_event.is_set():
            try:
                pkt = self.send_q.get_nowait()
                self._ser.write(pkt)
                self.log_q.put(("tx", f"TX  {pkt.hex(' ').upper()}"))
            except queue.Empty:
                pass

            waiting = self._ser.in_waiting
            if waiting:
                rx_buf += self._ser.read(waiting)
                while len(rx_buf) >= 5:
                    r = parse_ack(bytes(rx_buf))
                    if r:
                        c, s = r
                        from .constants import ACK_LABEL

                        desc = ACK_LABEL.get(s, f"0x{s:02X}")
                        level = "ok" if s == 0 else "err"
                        self.log_q.put((level, f"ACK  cmd=0x{c:02X}  {desc}"))
                        rx_buf = rx_buf[5:]
                    else:
                        rx_buf.pop(0)
            time.sleep(0.008)

        self._ser.close()
        self.log_q.put(("info", "串口已关闭"))
