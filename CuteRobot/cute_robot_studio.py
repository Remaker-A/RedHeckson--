#!/usr/bin/env python3
"""
CuteRobot Studio — 上位机 + 示教器 + 动作编辑器
=================================================

依赖：pip install pyserial

协议（与固件 RobotState.h / Protocol.h 严格对应）：
  包格式  : [0xAA][CMD][VAL][CMD^VAL][0x55]  5字节定长
  CMD 0x01: SET_EXPRESSION  VAL=ExpressionId
  CMD 0x02: SET_AUTO_MODE   VAL 忽略
  CMD 0x03: SET_SERVO       VAL=[tilt_idx(4bit) | pan_idx(4bit)]  ← 本文件新增
  CMD 0x04: SET_ROBOT_STATE VAL=RobotStateId

固件侧需要在 Protocol.cpp 的 handlePacket() 里增加对 CMD 0x03 的处理：
  case CMD_SET_SERVO: {
      uint8_t ti = (value >> 4) & 0x0F;   // 0–8
      uint8_t pi = value & 0x0F;           // 0–8
      uint8_t tilt = SERVO1_MIN + ti * (SERVO1_MAX - SERVO1_MIN) / 8;
      uint8_t pan  = SERVO2_MIN + pi * (SERVO2_MAX - SERVO2_MIN) / 8;
      ServoController::setTarget(tilt, pan);
      sendAck(command, ACK_OK);
      break;
  }
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import serial
import serial.tools.list_ports
import threading
import queue
import time
import json
import math
import struct
import os

# ═══════════════════════════════════════════════════════════════
# 协议常量
# ═══════════════════════════════════════════════════════════════
PACKET_HEAD = 0xAA
PACKET_TAIL = 0x55
BAUD_RATE = 115200

CMD_SET_EXPRESSION = 0x01
CMD_SET_AUTO_MODE = 0x02
CMD_SET_SERVO = 0x03
CMD_SET_ROBOT_STATE = 0x04

ACK_OK = 0x00
ACK_BAD_PACKET = 0xE1
ACK_BAD_COMMAND = 0xE2
ACK_BAD_PARAM = 0xE3

ACK_LABEL = {
    ACK_OK: "OK",
    ACK_BAD_PACKET: "BAD_PACKET",
    ACK_BAD_COMMAND: "BAD_CMD",
    ACK_BAD_PARAM: "BAD_PARAM",
}

# 舵机物理限位（与 ServoController.h 一致）
SERVO1_MIN, SERVO1_MID, SERVO1_MAX = 50, 90, 130  # tilt 俯仰
SERVO2_MIN, SERVO2_MID, SERVO2_MAX = 45, 90, 135  # pan  偏航

EXPRESSIONS = {
    "NORMAL": 16,
    "HAPPY": 11,
    "SAD": 17,
    "ANGRY": 1,
    "EXCITED": 8,
    "SURPRISED": 20,
    "SLEEPY": 19,
    "WORRIED": 23,
    "BLINK": 4,
    "LOGO": 28,
    "LOOK_LEFT": 13,
    "LOOK_RIGHT": 14,
    "LOOK_UP": 15,
    "LOOK_DOWN": 12,
}
EXPR_EMOJI = {
    "NORMAL": "😐",
    "HAPPY": "😊",
    "SAD": "😢",
    "ANGRY": "😠",
    "EXCITED": "🤩",
    "SURPRISED": "😲",
    "SLEEPY": "😴",
    "WORRIED": "😟",
    "BLINK": "😑",
    "LOGO": "🤖",
    "LOOK_LEFT": "👈",
    "LOOK_RIGHT": "👉",
    "LOOK_UP": "👆",
    "LOOK_DOWN": "👇",
}

ROBOT_STATES = {
    "IDLE": 0,
    "HAPPY": 1,
    "SAD": 2,
    "ANGRY": 3,
    "SLEEPY": 4,
    "SURPRISED": 5,
    "EXCITED": 6,
    "WORRIED": 7,
}
STATE_EMOJI = {
    "IDLE": "⏸",
    "HAPPY": "😊",
    "SAD": "😢",
    "ANGRY": "😠",
    "SLEEPY": "😴",
    "SURPRISED": "😲",
    "EXCITED": "🤩",
    "WORRIED": "😟",
}

EASINGS = ["linear", "ease_in_out", "ease_in_cubic", "ease_out_elastic", "ease_in_back"]

# ═══════════════════════════════════════════════════════════════
# 协议工具
# ═══════════════════════════════════════════════════════════════


def build_packet(cmd: int, val: int = 0) -> bytes:
    return struct.pack(
        "5B", PACKET_HEAD, cmd, val & 0xFF, cmd ^ (val & 0xFF), PACKET_TAIL
    )


def encode_servo(tilt: int, pan: int) -> int:
    """将角度编码为 1 字节：高 4 位 tilt 索引(0-8)，低 4 位 pan 索引(0-8)"""
    ti = round((tilt - SERVO1_MIN) / (SERVO1_MAX - SERVO1_MIN) * 8)
    pi = round((pan - SERVO2_MIN) / (SERVO2_MAX - SERVO2_MIN) * 8)
    return (max(0, min(8, ti)) << 4) | max(0, min(8, pi))


def decode_servo(val: int):
    ti = (val >> 4) & 0xF
    pi = val & 0xF
    return (
        SERVO1_MIN + ti * (SERVO1_MAX - SERVO1_MIN) // 8,
        SERVO2_MIN + pi * (SERVO2_MAX - SERVO2_MIN) // 8,
    )


def parse_ack(buf: bytes):
    for i in range(len(buf) - 4):
        if buf[i] == PACKET_HEAD and buf[i + 4] == PACKET_TAIL:
            c, s, cs = buf[i + 1], buf[i + 2], buf[i + 3]
            if (c ^ s) == cs:
                return c, s
    return None


# ═══════════════════════════════════════════════════════════════
# 缓动函数
# ═══════════════════════════════════════════════════════════════


def _ease(name: str, t: float) -> float:
    t = max(0.0, min(1.0, t))
    if name == "linear":
        return t
    if name == "ease_in_out":
        return t * t * (3 - 2 * t)
    if name == "ease_in_cubic":
        return t * t * t
    if name == "ease_out_elastic":
        if t in (0.0, 1.0):
            return t
        c4 = 2 * math.pi / 3
        return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * c4) + 1
    if name == "ease_in_back":
        c1 = 1.70158
        return (c1 + 1) * t * t * t - c1 * t * t
    return t


def lerp_angle(a: int, b: int, t: float, easing: str) -> int:
    return round(a + (b - a) * _ease(easing, t))


# ═══════════════════════════════════════════════════════════════
# 动作序列（关键帧模型）
# ═══════════════════════════════════════════════════════════════


class Keyframe:
    """单个关键帧"""

    def __init__(
        self,
        t_ms: int,
        tilt: int,
        pan: int,
        expr: str | None = None,
        easing: str = "ease_in_out",
    ):
        self.t_ms = int(t_ms)
        self.tilt = max(SERVO1_MIN, min(SERVO1_MAX, int(tilt)))
        self.pan = max(SERVO2_MIN, min(SERVO2_MAX, int(pan)))
        self.expr = expr  # ExpressionId 名称或 None
        self.easing = easing  # 到达此帧时使用的缓动

    def to_dict(self):
        return {
            "t_ms": self.t_ms,
            "tilt": self.tilt,
            "pan": self.pan,
            "expr": self.expr,
            "easing": self.easing,
        }

    @staticmethod
    def from_dict(d):
        return Keyframe(
            d["t_ms"],
            d["tilt"],
            d["pan"],
            d.get("expr"),
            d.get("easing", "ease_in_out"),
        )


class ActionSequence:
    """一段命名动作序列，包含若干关键帧"""

    def __init__(self, name="新动作", loop=False):
        self.name = name
        self.loop = loop
        self.frames: list[Keyframe] = []

    def add_frame(self, kf: Keyframe):
        self.frames.append(kf)
        self.frames.sort(key=lambda f: f.t_ms)

    def remove_frame(self, idx: int):
        if 0 <= idx < len(self.frames):
            self.frames.pop(idx)

    def trim_start(self, keep_from_ms: int):
        """掐头: 删除所有时间 < keep_from_ms 的帧，并重置首帧时间戳为0"""
        if not self.frames:
            return
        self.frames = [f for f in self.frames if f.t_ms >= keep_from_ms]
        if self.frames:
            self.frames[0].t_ms = 0

    def trim_end(self, keep_until_ms: int):
        """去尾: 删除所有时间 > keep_until_ms 的帧"""
        if not self.frames:
            return
        self.frames = [f for f in self.frames if f.t_ms <= keep_until_ms]

    def duration_ms(self) -> int:
        return self.frames[-1].t_ms if self.frames else 0

    def to_dict(self):
        return {
            "name": self.name,
            "loop": self.loop,
            "frames": [f.to_dict() for f in self.frames],
        }

    @staticmethod
    def from_dict(d):
        seq = ActionSequence(d.get("name", "动作"), d.get("loop", False))
        for fd in d.get("frames", []):
            seq.add_frame(Keyframe.from_dict(fd))
        return seq

    def build_playback_packets(self, interval_ms=20) -> list[tuple[int, bytes]]:
        """
        将关键帧序列插值为 (abs_ms, packet_bytes) 列表。
        每个关键帧的表情指令在该帧时刻单独发出，
        舵机数据以 interval_ms 步长插值。
        """
        packets: list[tuple[int, bytes]] = []
        if len(self.frames) < 1:
            return packets

        for i, kf in enumerate(self.frames):
            # 表情指令：在关键帧时刻精确触发
            if kf.expr and kf.expr in EXPRESSIONS:
                packets.append(
                    (kf.t_ms, build_packet(CMD_SET_EXPRESSION, EXPRESSIONS[kf.expr]))
                )

            # 舵机插值段
            if i < len(self.frames) - 1:
                kf_next = self.frames[i + 1]
                seg_dur = kf_next.t_ms - kf.t_ms
                steps = max(1, seg_dur // interval_ms)
                for s in range(steps):
                    t = s / steps
                    tilt = lerp_angle(kf.tilt, kf_next.tilt, t, kf_next.easing)
                    pan = lerp_angle(kf.pan, kf_next.pan, t, kf_next.easing)
                    abs_t = kf.t_ms + s * interval_ms
                    val = encode_servo(tilt, pan)
                    packets.append((abs_t, build_packet(CMD_SET_SERVO, val)))

        # 最后一帧的舵机
        last = self.frames[-1]
        packets.append(
            (last.t_ms, build_packet(CMD_SET_SERVO, encode_servo(last.tilt, last.pan)))
        )

        packets.sort(key=lambda p: p[0])
        return packets


# ═══════════════════════════════════════════════════════════════
# 串口工作线程
# ═══════════════════════════════════════════════════════════════


class SerialWorker(threading.Thread):
    def __init__(self, port: str, log_q: queue.Queue):
        super().__init__(daemon=True)
        self.port = port
        self.log_q = log_q
        self.send_q: queue.Queue[bytes] = queue.Queue()
        self._ser = None
        self._stop_event = threading.Event()

    def send(self, cmd: int, val: int = 0):
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
                        desc = ACK_LABEL.get(s, f"0x{s:02X}")
                        level = "ok" if s == ACK_OK else "err"
                        self.log_q.put((level, f"ACK  cmd=0x{c:02X}  {desc}"))
                        rx_buf = rx_buf[5:]
                    else:
                        rx_buf.pop(0)
            time.sleep(0.008)

        self._ser.close()
        self.log_q.put(("info", "串口已关闭"))


# ═══════════════════════════════════════════════════════════════
# 回放引擎（独立线程，不阻塞 GUI）
# ═══════════════════════════════════════════════════════════════


class PlaybackEngine(threading.Thread):
    def __init__(self, packets: list[tuple[int, bytes]], worker: SerialWorker, done_cb):
        super().__init__(daemon=True)
        self.packets = packets
        self.worker = worker
        self.done_cb = done_cb  # 回放结束时调用（在子线程，用 after 桥接）
        self._stop_event = threading.Event()
        self.progress = 0.0  # 0.0–1.0

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
            # 发送所有到期的包
            while idx < len(self.packets) and self.packets[idx][0] <= now_ms:
                self.worker.send_raw(self.packets[idx][1])
                idx += 1
            self.progress = min(1.0, now_ms / total)
            time.sleep(0.005)

        self.progress = 1.0
        if not self._stop_event.is_set():
            self.done_cb()


# ═══════════════════════════════════════════════════════════════
# 调色板 & 主题
# ═══════════════════════════════════════════════════════════════

C = {
    "bg": "#0d0d12",
    "panel": "#14141c",
    "panel2": "#1c1c28",
    "border": "#2a2a3c",
    "accent": "#7b68ee",  # 紫
    "accent2": "#ff6b9d",  # 粉
    "green": "#50fa7b",
    "red": "#ff5555",
    "yellow": "#f1fa8c",
    "cyan": "#8be9fd",
    "orange": "#ffb86c",
    "text": "#e8e8f2",
    "muted": "#6272a4",
    "tx": "#8be9fd",
    "rx_ok": "#50fa7b",
    "rx_err": "#ff5555",
    "kf_dot": "#bd93f9",
    "kf_line": "#44475a",
    "tilt_bar": "#ff6b9d",
    "pan_bar": "#8be9fd",
}

FF = "Courier New"
MONO = (FF, 10)
MONO_B = (FF, 10, "bold")
SMALL = (FF, 9)
TITLE = (FF, 12, "bold")
BIG = (FF, 14, "bold")


# ═══════════════════════════════════════════════════════════════
# 通用小组件
# ═══════════════════════════════════════════════════════════════


def hr(parent, color=None):
    tk.Frame(parent, bg=color or C["border"], height=1).pack(fill="x", padx=6, pady=2)


def label(parent, text, font=MONO, fg=None, bg=None, **kw):
    return tk.Label(
        parent, text=text, font=font, fg=fg or C["text"], bg=bg or C["panel"], **kw
    )


def panel_frame(parent, title="", color=None) -> tk.Frame:
    outer = tk.Frame(parent, bg=color or C["border"], padx=1, pady=1)
    outer.pack(fill="x", padx=6, pady=4)
    if title:
        tk.Label(
            outer,
            text=f"  {title}  ",
            font=TITLE,
            fg=C["accent"],
            bg=C["border"],
            anchor="w",
        ).pack(fill="x")
    inner = tk.Frame(outer, bg=C["panel"], padx=10, pady=8)
    inner.pack(fill="both")
    return inner


def mk_btn(parent, text, cmd, fg=None, bg=None, width=None, font=None):
    kw = dict(
        text=text,
        command=cmd,
        font=font or MONO_B,
        fg=fg or C["accent"],
        bg=bg or C["panel"],
        activeforeground=fg or C["accent"],
        activebackground=C["panel2"],
        relief="flat",
        bd=0,
        cursor="hand2",
        padx=10,
        pady=5,
        highlightthickness=1,
        highlightbackground=C["border"],
    )
    if width:
        kw["width"] = width
    b = tk.Button(parent, **kw)
    b.bind("<Enter>", lambda e: b.configure(bg=C["panel2"]))
    b.bind("<Leave>", lambda e: b.configure(bg=bg or C["panel"]))
    return b


def mk_scale(parent, label_text, from_, to, init, fg, command=None, length=200):
    f = tk.Frame(parent, bg=C["panel"])
    f.pack(fill="x", pady=3)
    tk.Label(
        f, text=label_text, font=SMALL, fg=fg, bg=C["panel"], width=14, anchor="w"
    ).pack(side="left")
    val_var = tk.IntVar(value=init)
    val_lbl = tk.Label(
        f, textvariable=val_var, font=MONO_B, fg=fg, bg=C["panel"], width=4
    )
    val_lbl.pack(side="right")

    def on_change(v):
        val_var.set(int(float(v)))
        if command:
            command(int(float(v)))

    s = tk.Scale(
        f,
        from_=from_,
        to=to,
        orient="horizontal",
        bg=C["panel"],
        fg=fg,
        highlightthickness=0,
        troughcolor=C["panel2"],
        activebackground=fg,
        sliderrelief="flat",
        length=length,
        showvalue=False,
        command=on_change,
    )
    s.set(init)
    s.pack(side="left", fill="x", expand=True, padx=8)
    return s, val_var


# ═══════════════════════════════════════════════════════════════
# 时间轴画布组件
# ═══════════════════════════════════════════════════════════════


class TimelineCanvas(tk.Canvas):
    """
    可视化时间轴，展示关键帧位置与舵机角度曲线。
    点击关键帧菱形可选中，选中后可删除。
    """

    H = 120
    MARGIN_L = 50
    MARGIN_R = 20
    PADDING_T = 16
    PADDING_B = 16

    def __init__(self, parent, seq_getter, select_cb=None, trim_cb=None, **kw):
        super().__init__(
            parent, bg=C["panel2"], height=self.H, highlightthickness=0, **kw
        )
        self._seq_getter = seq_getter  # callable → ActionSequence
        self._select_cb = select_cb  # callable(idx) 选中关键帧
        self._trim_cb = trim_cb  # callable(trim_start_ms, trim_end_ms) 裁剪回调
        self._selected = None
        self._trim_start = None
        self._trim_end = None
        self._dragging = None
        self.redraw()

    def redraw(self):
        self.delete("all")
        seq = self._seq_getter()
        W = self.winfo_width()
        if W < 10:
            return

        draw_w = W - self.MARGIN_L - self.MARGIN_R
        total = seq.duration_ms() or 1000
        inner_h = self.H - self.PADDING_T - self.PADDING_B

        def tx(t_ms):
            return self.MARGIN_L + draw_w * t_ms / total

        def ty_tilt(deg):
            n = (deg - SERVO1_MIN) / (SERVO1_MAX - SERVO1_MIN)
            return self.PADDING_T + (1 - n) * inner_h

        def ty_pan(deg):
            n = (deg - SERVO2_MIN) / (SERVO2_MAX - SERVO2_MIN)
            return self.PADDING_T + (1 - n) * inner_h

        for frac in [0.25, 0.5, 0.75, 1.0]:
            x = self.MARGIN_L + draw_w * frac
            self.create_line(
                x,
                self.PADDING_T,
                x,
                self.H - self.PADDING_B,
                fill=C["border"],
                dash=(3, 4),
            )
            self.create_text(
                x,
                self.H - 6,
                text=f"{int(total * frac)}ms",
                fill=C["muted"],
                font=(FF, 7),
                anchor="s",
            )

        self.create_text(
            self.MARGIN_L - 4,
            self.PADDING_T + inner_h // 2,
            text="90°",
            fill=C["muted"],
            font=(FF, 7),
            anchor="e",
        )

        frames = seq.frames
        for i in range(len(frames) - 1):
            f0, f1 = frames[i], frames[i + 1]
            pts_t, pts_p = [], []
            seg = f1.t_ms - f0.t_ms
            for s in range(21):
                t = s / 20
                tlt = lerp_angle(f0.tilt, f1.tilt, t, f1.easing)
                pn = lerp_angle(f0.pan, f1.pan, t, f1.easing)
                x = tx(f0.t_ms + seg * t)
                pts_t += [x, ty_tilt(tlt)]
                pts_p += [x, ty_pan(pn)]
            if len(pts_t) >= 4:
                self.create_line(*pts_t, fill=C["tilt_bar"], width=1.5, smooth=False)
                self.create_line(*pts_p, fill=C["pan_bar"], width=1.5, smooth=False)

        for i, kf in enumerate(frames):
            x = tx(kf.t_ms)
            yt = ty_tilt(kf.tilt)
            yp = ty_pan(kf.pan)
            sel = i == self._selected
            clr = C["yellow"] if sel else C["kf_dot"]
            r = 6 if sel else 4
            self.create_polygon(
                x, yt - r, x + r, yt, x, yt + r, x - r, yt, fill=clr, outline=""
            )
            self.create_polygon(
                x, yp - r, x + r, yp, x, yp + r, x - r, yp, fill=clr, outline=""
            )
            self.create_line(x, yt, x, yp, fill=C["kf_line"], dash=(2, 2))
            if kf.expr:
                em = EXPR_EMOJI.get(kf.expr.replace("E_", ""), "")
                self.create_text(
                    x,
                    self.PADDING_T - 4,
                    text=em,
                    font=(FF, 9),
                    anchor="s",
                    fill=C["yellow"] if sel else C["text"],
                )

        px = self.MARGIN_L + draw_w * self._playhead
        self.create_line(px, 0, px, self.H, fill=C["accent2"], width=1.5)

        self.create_line(4, 12, 16, 12, fill=C["tilt_bar"], width=2)
        self.create_text(
            18, 12, text="俯仰", fill=C["tilt_bar"], font=(FF, 7), anchor="w"
        )
        self.create_line(4, 22, 16, 22, fill=C["pan_bar"], width=2)
        self.create_text(
            18, 22, text="偏航", fill=C["pan_bar"], font=(FF, 7), anchor="w"
        )

        if self._trim_start is not None:
            lx = tx(self._trim_start)
            self.create_polygon(lx, 4, lx + 8, 12, lx, 20, fill=C["red"], outline="")
            self.create_line(lx, 20, lx, self.H, fill=C["red"], width=1, dash=(2, 2))
        if self._trim_end is not None:
            rx = tx(self._trim_end)
            self.create_polygon(rx, 4, rx - 8, 12, rx, 20, fill=C["orange"], outline="")
            self.create_line(
                rx, 0, rx, self.H - 20, fill=C["orange"], width=1, dash=(2, 2)
            )

    def set_playhead(self, progress: float):
        self._playhead = progress
        self.redraw()

    def set_trim(self, trim_start_ms, trim_end_ms):
        self._trim_start = trim_start_ms
        self._trim_end = trim_end_ms
        self.redraw()

    def _on_click(self, event):
        hit = self._hit_trim_handle(event.x, event.y)
        if hit:
            self._dragging = hit
            return
        seq = self._seq_getter()
        W = self.winfo_width()
        if W < 10 or not seq.frames:
            return
        draw_w = W - self.MARGIN_L - self.MARGIN_R
        total = seq.duration_ms() or 1000
        x = event.x
        best_i, best_d = None, 1e9
        for i, kf in enumerate(seq.frames):
            kx = self.MARGIN_L + draw_w * kf.t_ms / total
            if abs(kx - x) < best_d:
                best_d = abs(kx - x)
                best_i = i
        if best_d < 16:
            self._selected = best_i
            if self._select_cb:
                self._select_cb(best_i)
        else:
            self._selected = None
        self.redraw()

    def _hit_trim_handle(self, x, y):
        HANDLE_W = 8
        if self._trim_start is not None:
            W = self.winfo_width()
            seq = self._seq_getter()
            if not seq.frames:
                return None
            draw_w = W - self.MARGIN_L - self.MARGIN_R
            total = seq.duration_ms() or 1000
            lx = self.MARGIN_L + draw_w * self._trim_start / total
            if abs(x - lx) < HANDLE_W and abs(y - self.H // 2) < 20:
                return "trim_l"
        if self._trim_end is not None:
            W = self.winfo_width()
            seq = self._seq_getter()
            if not seq.frames:
                return None
            draw_w = W - self.MARGIN_L - self.MARGIN_R
            total = seq.duration_ms() or 1000
            rx = self.MARGIN_L + draw_w * self._trim_end / total
            if abs(x - rx) < HANDLE_W and abs(y - self.H // 2) < 20:
                return "trim_r"
        return None

    def _on_drag(self, event):
        seq = self._seq_getter()
        W = self.winfo_width()
        if W < 10 or not seq.frames:
            return
        draw_w = W - self.MARGIN_L - self.MARGIN_R
        total = seq.duration_ms() or 1000

        if self._dragging == "trim_l":
            t_ms = max(0, min(total, (event.x - self.MARGIN_L) / draw_w * total))
            self._trim_start = t_ms
        elif self._dragging == "trim_r":
            t_ms = max(0, min(total, (event.x - self.MARGIN_L) / draw_w * total))
            self._trim_end = t_ms
        else:
            hit = self._hit_trim_handle(event.x, event.y)
            if hit:
                self._dragging = hit
        self.redraw()

    def _on_release(self, event):
        if self._dragging and self._trim_cb:
            self._trim_cb(self._trim_start, self._trim_end)
        self._dragging = None
        self.redraw()


# ═══════════════════════════════════════════════════════════════
# 主应用
# ═══════════════════════════════════════════════════════════════


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CuteRobot Studio")
        self.configure(bg=C["bg"])
        self.geometry("960x860")
        self.resizable(True, True)

        self._worker: SerialWorker | None = None
        self._playback: PlaybackEngine | None = None
        self._log_q: queue.Queue = queue.Queue()
        self._connected = False

        # 示教器实时状态
        self._tilt_live = tk.IntVar(value=SERVO1_MID)
        self._pan_live = tk.IntVar(value=SERVO2_MID)
        self._expr_live = tk.StringVar(value="NORMAL")

        # 动作序列库
        self._sequences: list[ActionSequence] = [self._make_demo_sequence()]
        self._cur_seq_idx = 0
        self._dirty = False

        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        self._build_ui()
        self._refresh_ports()
        self._poll_log()
        self._poll_playback()

    # ──────────────────────────────────────────────────────────
    # 界面构建
    # ──────────────────────────────────────────────────────────

    def _build_ui(self):
        # 顶栏
        self._build_topbar()

        # 主 Notebook
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=6, pady=4)
        self._nb = nb

        # Tab 1: 快捷控制
        t1 = tk.Frame(nb, bg=C["bg"])
        nb.add(t1, text="  🎮  快捷控制  ")
        self._build_tab_control(t1)

        # Tab 2: 示教器
        t2 = tk.Frame(nb, bg=C["bg"])
        nb.add(t2, text="  🕹  示教器  ")
        self._build_tab_teach(t2)

        # Tab 3: 动作编辑器
        t3 = tk.Frame(nb, bg=C["bg"])
        nb.add(t3, text="  🎬  动作编辑器  ")
        self._build_tab_editor(t3)

        # 底部日志（所有 tab 共享）
        self._build_logbar()

        self._style_notebook()

    def _build_topbar(self):
        bar = tk.Frame(self, bg=C["bg"], pady=8)
        bar.pack(fill="x", padx=12)

        tk.Label(
            bar,
            text="◈  CuteRobot Studio",
            font=(FF, 16, "bold"),
            fg=C["accent"],
            bg=C["bg"],
        ).pack(side="left")

        # 连接区
        conn = tk.Frame(bar, bg=C["bg"])
        conn.pack(side="right")

        self._dot = tk.Label(conn, text="●", font=(FF, 18), fg=C["red"], bg=C["bg"])
        self._dot.pack(side="right", padx=(0, 2))
        self._dot_lbl = tk.Label(
            conn, text="未连接", font=SMALL, fg=C["muted"], bg=C["bg"]
        )
        self._dot_lbl.pack(side="right", padx=(0, 8))

        self._port_var = tk.StringVar()
        self._port_cb = ttk.Combobox(
            conn, textvariable=self._port_var, width=14, font=MONO, state="readonly"
        )
        self._port_cb.pack(side="right", padx=4)

        mk_btn(conn, "⟳", self._refresh_ports, fg=C["muted"], width=2).pack(
            side="right"
        )
        self._btn_conn = mk_btn(
            conn, "连接", self._toggle_connect, fg=C["accent"], width=6
        )
        self._btn_conn.pack(side="right", padx=4)

        hr(self)

    # ── Tab 1: 快捷控制 ───────────────────────────────────────

    def _build_tab_control(self, parent):
        cols = tk.Frame(parent, bg=C["bg"])
        cols.pack(fill="both", expand=True, padx=4, pady=4)

        left = tk.Frame(cols, bg=C["bg"])
        right = tk.Frame(cols, bg=C["bg"])
        left.pack(side="left", fill="both", expand=True, padx=(0, 4))
        right.pack(side="left", fill="both", expand=True)

        # 机器人状态
        sp = panel_frame(left, "机器人整体状态  (眼睛 + 舵机)")
        g = tk.Frame(sp, bg=C["panel"])
        g.pack(fill="x")
        for i, (name, val) in enumerate(ROBOT_STATES.items()):
            em = STATE_EMOJI.get(name, "")
            b = mk_btn(
                g,
                f"{em}  {name}",
                lambda v=val, n=name: self._send_robot_state(v, n),
                fg=C["accent"],
            )
            b.grid(row=i // 2, column=i % 2, padx=4, pady=3, sticky="ew")
        g.columnconfigure(0, weight=1)
        g.columnconfigure(1, weight=1)

        auto_f = panel_frame(left, "")
        mk_btn(
            auto_f,
            "⟳  AUTO MODE  —  眼睛自动 + 舵机归中",
            self._send_auto_mode,
            fg=C["accent2"],
            width=40,
        ).pack(fill="x")

        # 表情控制
        ep = panel_frame(right, "单独控制眼睛表情")
        eg = tk.Frame(ep, bg=C["panel"])
        eg.pack(fill="x")
        items = list(EXPRESSIONS.items())
        for i, (name, val) in enumerate(items):
            em = EXPR_EMOJI.get(name, "")
            b = mk_btn(
                eg,
                f"{em} {name}",
                lambda v=val, n=name: self._send_expression(v, n),
                fg=C["cyan"],
            )
            b.grid(row=i // 2, column=i % 2, padx=3, pady=2, sticky="ew")
        eg.columnconfigure(0, weight=1)
        eg.columnconfigure(1, weight=1)

        # 手动发包
        mp = panel_frame(left, "手动发包")
        row = tk.Frame(mp, bg=C["panel"])
        row.pack(fill="x")
        tk.Label(row, text="CMD", font=SMALL, fg=C["muted"], bg=C["panel"]).pack(
            side="left"
        )
        self._man_cmd = tk.Entry(
            row,
            width=5,
            font=MONO,
            bg=C["bg"],
            fg=C["text"],
            insertbackground=C["text"],
            relief="flat",
        )
        self._man_cmd.insert(0, "04")
        self._man_cmd.pack(side="left", padx=4)
        tk.Label(row, text="VAL", font=SMALL, fg=C["muted"], bg=C["panel"]).pack(
            side="left"
        )
        self._man_val = tk.Entry(
            row,
            width=5,
            font=MONO,
            bg=C["bg"],
            fg=C["text"],
            insertbackground=C["text"],
            relief="flat",
        )
        self._man_val.insert(0, "01")
        self._man_val.pack(side="left", padx=4)
        self._man_prev = tk.Label(
            row, text="→  AA 04 01 05 55", font=MONO, fg=C["yellow"], bg=C["panel"]
        )
        self._man_prev.pack(side="left", padx=8)
        mk_btn(row, "发送", self._send_manual, fg=C["orange"]).pack(side="right")
        for w in (self._man_cmd, self._man_val):
            w.bind("<KeyRelease>", self._update_manual_preview)

    # ── Tab 2: 示教器 ─────────────────────────────────────────

    def _build_tab_teach(self, parent):
        # 说明
        info = tk.Frame(parent, bg=C["bg"])
        info.pack(fill="x", padx=10, pady=(8, 2))
        tk.Label(
            info,
            text="实时拖动滑条控制舵机，点击「📌 记录关键帧」将当前姿态 + 表情追加到当前动作序列。",
            font=SMALL,
            fg=C["muted"],
            bg=C["bg"],
            wraplength=900,
            justify="left",
        ).pack(anchor="w")

        body = tk.Frame(parent, bg=C["bg"])
        body.pack(fill="both", expand=True, padx=6, pady=4)

        left = tk.Frame(body, bg=C["bg"])
        right = tk.Frame(body, bg=C["bg"])
        left.pack(side="left", fill="both", expand=True, padx=(0, 6))
        right.pack(side="left", fill="y")
        right.pack_propagate(False)
        right.configure(width=280)

        # 舵机滑条
        sv_panel = panel_frame(left, "舵机实时控制")

        _, _ = mk_scale(
            sv_panel,
            "俯仰 Tilt  (°)",
            SERVO1_MIN,
            SERVO1_MAX,
            SERVO1_MID,
            C["tilt_bar"],
            command=self._on_tilt_change,
            length=280,
        )
        self._tilt_scale = sv_panel.winfo_children()[-1].winfo_children()[-2]

        _, _ = mk_scale(
            sv_panel,
            "偏航 Pan   (°)",
            SERVO2_MIN,
            SERVO2_MAX,
            SERVO2_MID,
            C["pan_bar"],
            command=self._on_pan_change,
            length=280,
        )
        self._pan_scale = sv_panel.winfo_children()[-1].winfo_children()[-2]

        # 姿态预览（ASCII 艺术）
        preview_f = panel_frame(left, "姿态预览")
        self._pose_canvas = tk.Canvas(
            preview_f, width=220, height=160, bg=C["panel2"], highlightthickness=0
        )
        self._pose_canvas.pack()
        self._draw_pose_preview(SERVO1_MID, SERVO2_MID)

        # 记录时间点
        t_row = tk.Frame(left.master or left, bg=C["bg"])  # reuse left
        t_panel = panel_frame(left, "录制控制")

        tr = tk.Frame(t_panel, bg=C["panel"])
        tr.pack(fill="x", pady=4)
        tk.Label(tr, text="时间点 (ms)", font=SMALL, fg=C["muted"], bg=C["panel"]).pack(
            side="left"
        )
        self._rec_time = tk.IntVar(value=0)
        self._rec_time_entry = tk.Entry(
            tr,
            textvariable=self._rec_time,
            width=8,
            font=MONO_B,
            bg=C["bg"],
            fg=C["yellow"],
            insertbackground=C["yellow"],
            relief="flat",
        )
        self._rec_time_entry.pack(side="left", padx=6)
        tk.Label(
            tr, text="(自动+500ms)", font=SMALL, fg=C["muted"], bg=C["panel"]
        ).pack(side="left")

        mk_btn(
            t_panel,
            "📌  记录当前关键帧",
            self._record_keyframe,
            fg=C["yellow"],
            width=30,
        ).pack(fill="x", pady=(6, 2))
        mk_btn(
            t_panel,
            "🔄  重置时间为 0",
            lambda: self._rec_time.set(0),
            fg=C["muted"],
            width=30,
        ).pack(fill="x", pady=2)

        # 右侧：表情选择 + 缓动选择
        ep = panel_frame(right, "录制时的表情")
        self._rec_expr_var = tk.StringVar(value="HAPPY")
        for name in EXPRESSIONS:
            em = EXPR_EMOJI.get(name, "")
            rb = tk.Radiobutton(
                ep,
                text=f"{em} {name}",
                variable=self._rec_expr_var,
                value=name,
                bg=C["panel"],
                fg=C["text"],
                selectcolor=C["panel2"],
                activebackground=C["panel"],
                font=SMALL,
            )
            rb.pack(anchor="w")
        tk.Radiobutton(
            ep,
            text="（不设置表情）",
            variable=self._rec_expr_var,
            value="",
            bg=C["panel"],
            fg=C["muted"],
            selectcolor=C["panel2"],
            activebackground=C["panel"],
            font=SMALL,
        ).pack(anchor="w")

        ease_p = panel_frame(right, "入场缓动曲线")
        self._rec_easing = tk.StringVar(value="ease_in_out")
        for e in EASINGS:
            tk.Radiobutton(
                ease_p,
                text=e,
                variable=self._rec_easing,
                value=e,
                bg=C["panel"],
                fg=C["cyan"],
                selectcolor=C["panel2"],
                activebackground=C["panel"],
                font=SMALL,
            ).pack(anchor="w")

    # ── Tab 3: 动作编辑器 ─────────────────────────────────────

    def _build_tab_editor(self, parent):
        top = tk.Frame(parent, bg=C["bg"])
        top.pack(fill="x", padx=8, pady=(6, 2))

        # 序列选择
        tk.Label(top, text="当前序列:", font=MONO, fg=C["muted"], bg=C["bg"]).pack(
            side="left"
        )
        self._seq_combo_var = tk.StringVar()
        self._seq_combo = ttk.Combobox(
            top, textvariable=self._seq_combo_var, width=22, font=MONO, state="readonly"
        )
        self._seq_combo.pack(side="left", padx=6)
        self._seq_combo.bind("<<ComboboxSelected>>", self._on_seq_select)

        mk_btn(top, "+ 新建", self._new_sequence, fg=C["green"]).pack(
            side="left", padx=4
        )
        mk_btn(top, "⊖ 删除", self._del_sequence, fg=C["red"]).pack(side="left", padx=2)
        mk_btn(top, "💾 保存 JSON", self._save_json, fg=C["yellow"]).pack(
            side="left", padx=4
        )
        mk_btn(top, "📂 加载 JSON", self._load_json, fg=C["orange"]).pack(
            side="left", padx=2
        )

        hr(parent)

        # 时间轴
        tl_f = panel_frame(parent, "时间轴  (点击菱形选中关键帧，拖拽三角裁剪)")
        self._timeline = TimelineCanvas(
            tl_f,
            self._cur_seq,
            select_cb=self._on_kf_select,
            trim_cb=self._on_trim_change,
        )
        self._timeline.pack(fill="x", pady=4)

        trim_row = tk.Frame(tl_f, bg=C["panel"])
        trim_row.pack(fill="x", pady=(4, 0))
        mk_btn(trim_row, "✂ 掐头", self._trim_head, fg=C["red"], width=10).pack(
            side="left", padx=4
        )
        mk_btn(trim_row, "去尾 ✂", self._trim_tail, fg=C["orange"], width=10).pack(
            side="left", padx=4
        )
        self._trim_lbl = tk.Label(
            trim_row, text="未裁剪", font=SMALL, fg=C["muted"], bg=C["panel"]
        )
        self._trim_lbl.pack(side="left", padx=10)

        # 关键帧列表 + 编辑
        mid = tk.Frame(parent, bg=C["bg"])
        mid.pack(fill="both", expand=True, padx=8, pady=4)

        list_f = panel_frame(mid, "关键帧列表")
        list_f.configure(width=420)

        cols = ("时间(ms)", "俯仰°", "偏航°", "表情", "缓动")
        self._kf_tree = ttk.Treeview(
            list_f, columns=cols, show="headings", height=8, selectmode="browse"
        )
        for c in cols:
            self._kf_tree.heading(c, text=c)
            self._kf_tree.column(c, width=80, anchor="center")
        self._kf_tree.pack(fill="both", expand=True)
        self._kf_tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self._style_treeview()

        del_row = tk.Frame(list_f, bg=C["panel"])
        del_row.pack(fill="x", pady=(4, 0))
        mk_btn(del_row, "🗑  删除选中关键帧", self._del_selected_kf, fg=C["red"]).pack(
            side="left"
        )

        # 回放控制
        pb_f = panel_frame(parent, "回放控制")
        pb_row = tk.Frame(pb_f, bg=C["panel"])
        pb_row.pack(fill="x")

        self._loop_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            pb_row,
            text="循环",
            variable=self._loop_var,
            bg=C["panel"],
            fg=C["text"],
            selectcolor=C["panel2"],
            activebackground=C["panel"],
            font=MONO,
        ).pack(side="left", padx=4)

        self._pb_btn = mk_btn(
            pb_row, "▶  播放", self._toggle_playback, fg=C["green"], width=12
        )
        self._pb_btn.pack(side="left", padx=8)

        self._pb_progress = ttk.Progressbar(pb_row, length=300, mode="determinate")
        self._pb_progress.pack(side="left", fill="x", expand=True, padx=8)

        self._pb_lbl = tk.Label(
            pb_row, text="0 / 0 ms", font=SMALL, fg=C["muted"], bg=C["panel"]
        )
        self._pb_lbl.pack(side="left")

        self._refresh_seq_combo()
        self._refresh_kf_list()

    # ── 底部日志 ──────────────────────────────────────────────

    def _build_logbar(self):
        hr(self)
        log_f = tk.Frame(self, bg=C["bg"])
        log_f.pack(fill="x", padx=8, pady=(2, 6))
        tk.Label(log_f, text="通信日志", font=TITLE, fg=C["accent"], bg=C["bg"]).pack(
            anchor="w"
        )

        frame = tk.Frame(log_f, bg=C["panel"])
        frame.pack(fill="x")
        self._log_text = tk.Text(
            frame,
            height=6,
            font=(FF, 8),
            bg="#08080f",
            fg=C["text"],
            relief="flat",
            bd=0,
            state="disabled",
            selectbackground=C["border"],
        )
        self._log_text.pack(side="left", fill="both", expand=True)
        sb = tk.Scrollbar(
            frame, command=self._log_text.yview, bg=C["border"], troughcolor=C["bg"]
        )
        sb.pack(side="right", fill="y")
        self._log_text.configure(yscrollcommand=sb.set)
        self._log_text.tag_config("tx", foreground=C["tx"])
        self._log_text.tag_config("ok", foreground=C["rx_ok"])
        self._log_text.tag_config("err", foreground=C["rx_err"])
        self._log_text.tag_config("info", foreground=C["muted"])

        mk_btn(log_f, "清空", self._clear_log, fg=C["muted"], width=6).pack(
            anchor="e", pady=2
        )

    # ──────────────────────────────────────────────────────────
    # 示教器逻辑
    # ──────────────────────────────────────────────────────────

    def _on_tilt_change(self, val: int):
        self._tilt_live.set(val)
        self._draw_pose_preview(val, self._pan_live.get())
        if self._connected and self._worker:
            pkt = build_packet(CMD_SET_SERVO, encode_servo(val, self._pan_live.get()))
            self._worker.send_raw(pkt)

    def _on_pan_change(self, val: int):
        self._pan_live.set(val)
        self._draw_pose_preview(self._tilt_live.get(), val)
        if self._connected and self._worker:
            pkt = build_packet(CMD_SET_SERVO, encode_servo(self._tilt_live.get(), val))
            self._worker.send_raw(pkt)

    def _draw_pose_preview(self, tilt: int, pan: int):
        """用简单几何图形展示脖子+头的姿态"""
        c = self._pose_canvas
        c.delete("all")
        W, H = 220, 160
        cx, base_y = W // 2, H - 20

        # 归一化
        t_n = (tilt - SERVO1_MIN) / (SERVO1_MAX - SERVO1_MIN)  # 0=低头 1=抬头
        p_n = (pan - SERVO2_MIN) / (SERVO2_MAX - SERVO2_MIN)  # 0=左 1=右

        neck_len = 40 + t_n * 30  # 脖子伸出长度
        head_x = cx + (p_n - 0.5) * 60  # 头的水平偏移
        head_y = base_y - neck_len

        # 躯干
        c.create_rectangle(
            cx - 28, base_y, cx + 28, H, fill=C["panel"], outline=C["border"], width=1
        )
        c.create_text(cx, base_y + 8, text="BODY", fill=C["muted"], font=(FF, 7))

        # 脖子
        c.create_line(cx, base_y, head_x, head_y, fill=C["accent"], width=3)

        # 头
        em = (
            EXPR_EMOJI.get(self._rec_expr_var.get(), "😐")
            if hasattr(self, "_rec_expr_var")
            else "😐"
        )
        c.create_oval(
            head_x - 20,
            head_y - 20,
            head_x + 20,
            head_y + 20,
            fill=C["panel2"],
            outline=C["accent"],
            width=2,
        )
        c.create_text(head_x, head_y, text=em, font=(FF, 14))

        # 角度标注
        c.create_text(
            4, 10, text=f"T:{tilt}°", fill=C["tilt_bar"], font=(FF, 8), anchor="w"
        )
        c.create_text(
            4, 22, text=f"P:{pan}°", fill=C["pan_bar"], font=(FF, 8), anchor="w"
        )

    def _record_keyframe(self):
        tilt = self._tilt_live.get()
        pan = self._pan_live.get()
        t_ms = self._rec_time.get()
        expr = self._rec_expr_var.get() or None
        easing = self._rec_easing.get()

        kf = Keyframe(t_ms, tilt, pan, expr, easing)
        self._cur_seq().add_frame(kf)
        self._mark_dirty()
        self._rec_time.set(t_ms + 500)  # 自动步进500ms
        self._refresh_kf_list()
        self._timeline.redraw()
        self._log(
            ("info", f"📌 记录关键帧 t={t_ms}ms  tilt={tilt}°  pan={pan}°  expr={expr}")
        )

    # ──────────────────────────────────────────────────────────
    # 动作编辑器逻辑
    # ──────────────────────────────────────────────────────────

    def _cur_seq(self) -> ActionSequence:
        if not self._sequences:
            s = ActionSequence("默认")
            self._sequences.append(s)
        i = max(0, min(self._cur_seq_idx, len(self._sequences) - 1))
        return self._sequences[i]

    def _refresh_seq_combo(self):
        names = [s.name for s in self._sequences]
        self._seq_combo["values"] = names
        if names:
            idx = max(0, min(self._cur_seq_idx, len(names) - 1))
            self._seq_combo.current(idx)

    def _on_seq_select(self, _=None):
        self._cur_seq_idx = self._seq_combo.current()
        self._refresh_kf_list()
        self._timeline.redraw()

    def _new_sequence(self):
        name = f"动作_{len(self._sequences) + 1}"
        self._sequences.append(ActionSequence(name))
        self._cur_seq_idx = len(self._sequences) - 1
        self._mark_dirty()
        self._refresh_seq_combo()
        self._refresh_kf_list()
        self._timeline.redraw()

    def _del_sequence(self):
        if len(self._sequences) <= 1:
            messagebox.showinfo("提示", "至少保留一个序列")
            return
        self._sequences.pop(self._cur_seq_idx)
        self._cur_seq_idx = max(0, self._cur_seq_idx - 1)
        self._mark_dirty()
        self._refresh_seq_combo()
        self._refresh_kf_list()
        self._timeline.redraw()

    def _refresh_kf_list(self):
        for row in self._kf_tree.get_children():
            self._kf_tree.delete(row)
        for i, kf in enumerate(self._cur_seq().frames):
            self._kf_tree.insert(
                "",
                "end",
                iid=str(i),
                values=(kf.t_ms, kf.tilt, kf.pan, kf.expr or "—", kf.easing),
            )

    def _on_kf_select(self, idx: int):
        self._kf_tree.selection_set(str(idx))

    def _on_tree_select(self, _=None):
        sel = self._kf_tree.selection()
        if sel:
            self._timeline._selected = int(sel[0])
            self._timeline.redraw()

    def _del_selected_kf(self):
        sel = self._kf_tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        self._cur_seq().remove_frame(idx)
        self._mark_dirty()
        self._refresh_kf_list()
        self._timeline.redraw()

    def _on_trim_change(self, trim_start_ms, trim_end_ms):
        pass

    def _trim_head(self):
        seq = self._cur_seq()
        if len(seq.frames) < 2:
            return
        mid = seq.frames[len(seq.frames) // 2].t_ms
        seq.trim_start(mid)
        self._mark_dirty()
        self._refresh_kf_list()
        self._timeline.set_trim(mid, None)
        self._trim_lbl.config(text=f"已掐头: {mid}ms")

    def _trim_tail(self):
        seq = self._cur_seq()
        if len(seq.frames) < 2:
            return
        mid = seq.frames[len(seq.frames) // 2].t_ms
        seq.trim_end(mid)
        self._mark_dirty()
        self._refresh_kf_list()
        self._timeline.set_trim(None, mid)
        self._trim_lbl.config(text=f"已去尾: 保留到{mid}ms")

    # ──────────────────────────────────────────────────────────
    # 回放
    # ──────────────────────────────────────────────────────────

    def _toggle_playback(self):
        if self._playback and self._playback.is_alive():
            self._stop_playback()
        else:
            self._start_playback()

    def _start_playback(self):
        if not self._require_connected():
            return
        seq = self._cur_seq()
        if len(seq.frames) < 2:
            messagebox.showinfo("提示", "序列中至少需要两个关键帧才能回放")
            return
        packets = seq.build_playback_packets(interval_ms=20)
        self._playback = PlaybackEngine(
            packets, self._worker, done_cb=lambda: self.after(0, self._on_playback_done)
        )
        self._playback.start()
        self._pb_btn.configure(text="⏹  停止", fg=C["red"])
        total = seq.duration_ms()
        self._pb_lbl.configure(text=f"0 / {total} ms")
        self._log(("info", f"▶ 开始回放「{seq.name}」  {len(packets)} 帧  {total}ms"))

    def _stop_playback(self):
        if self._playback:
            self._playback.stop()
            self._playback = None
        self._pb_btn.configure(text="▶  播放", fg=C["green"])
        self._pb_progress["value"] = 0
        self._timeline.set_playhead(0.0)

    def _on_playback_done(self):
        seq = self._cur_seq()
        if self._loop_var.get() and self._connected:
            # 循环：重新开始
            self._start_playback()
        else:
            self._pb_btn.configure(text="▶  播放", fg=C["green"])
            self._pb_progress["value"] = 100
            self._timeline.set_playhead(1.0)
            self._log(("ok", f"✓ 回放完成「{seq.name}」"))

    def _poll_playback(self):
        if self._playback and self._playback.is_alive():
            p = self._playback.progress * 100
            self._pb_progress["value"] = p
            total = self._cur_seq().duration_ms()
            elapsed = int(self._playback.progress * total)
            self._pb_lbl.configure(text=f"{elapsed} / {total} ms")
            self._timeline.set_playhead(self._playback.progress)
        self.after(50, self._poll_playback)

    # ──────────────────────────────────────────────────────────
    # JSON 序列化
    # ──────────────────────────────────────────────────────────

    def _save_json(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON 动作文件", "*.json"), ("所有文件", "*.*")],
            title="保存动作序列",
        )
        if not path:
            return
        data = [s.to_dict() for s in self._sequences]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self._dirty = False
        self._log(("ok", f"💾 已保存 → {os.path.basename(path)}"))

    def _load_json(self):
        path = filedialog.askopenfilename(
            filetypes=[("JSON 动作文件", "*.json"), ("所有文件", "*.*")],
            title="加载动作序列",
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._sequences = [ActionSequence.from_dict(d) for d in data]
            self._cur_seq_idx = 0
            self._dirty = False
            self._refresh_seq_combo()
            self._refresh_kf_list()
            self._timeline.redraw()
            self._log(
                (
                    "ok",
                    f"📂 已加载 ← {os.path.basename(path)}  "
                    f"({len(self._sequences)} 个序列)",
                )
            )
        except Exception as e:
            messagebox.showerror("加载失败", str(e))

    def _on_closing(self):
        if self._dirty:
            result = messagebox.askyesnocancel(
                "退出确认",
                "有未保存的动作修改，确定不保存直接退出吗？\n\n[是] 不保存直接退出\n[否] 取消，继续编辑\n[取消] 保存后退出",
            )
            if result is None:
                return
            if result is False:
                return
        self._stop_playback()
        if self._worker:
            self._worker.stop()
        self.destroy()

    def _mark_dirty(self):
        self._dirty = True

    # ──────────────────────────────────────────────────────────
    # 串口控制
    # ──────────────────────────────────────────────────────────

    def _refresh_ports(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self._port_cb["values"] = ports
        if ports and not self._port_var.get():
            self._port_var.set(ports[0])

    def _toggle_connect(self):
        if self._connected:
            self._stop_playback()
            if self._worker:
                self._worker.stop()
                self._worker.join(timeout=1.0)
                self._worker = None
            self._connected = False
            self._btn_conn.configure(text="连接", fg=C["accent"])
            self._dot.configure(fg=C["red"])
            self._dot_lbl.configure(text="未连接")
        else:
            port = self._port_var.get()
            if not port:
                messagebox.showerror("错误", "请先选择串口")
                return
            self._worker = SerialWorker(port, self._log_q)
            self._worker.start()
            self._connected = True
            self._btn_conn.configure(text="断开", fg=C["red"])
            self._dot.configure(fg=C["green"])
            self._dot_lbl.configure(text=port)

    def _require_connected(self) -> bool:
        if not self._connected or not self._worker:
            messagebox.showwarning("未连接", "请先连接串口")
            return False
        return True

    # ──────────────────────────────────────────────────────────
    # 发包动作
    # ──────────────────────────────────────────────────────────

    def _send_expression(self, val: int, name: str):
        if not self._require_connected():
            return
        self._worker.send(CMD_SET_EXPRESSION, val)
        self._log(("info", f"→ EXPR  {name}({val})"))

    def _send_robot_state(self, val: int, name: str):
        if not self._require_connected():
            return
        self._worker.send(CMD_SET_ROBOT_STATE, val)
        self._log(("info", f"→ STATE  {name}({val})"))

    def _send_auto_mode(self):
        if not self._require_connected():
            return
        self._worker.send(CMD_SET_AUTO_MODE, 0)
        self._log(("info", "→ AUTO_MODE"))

    def _send_manual(self):
        if not self._require_connected():
            return
        try:
            cmd = int(self._man_cmd.get().strip(), 16)
            val = int(self._man_val.get().strip(), 16)
            assert 0 <= cmd <= 0xFF and 0 <= val <= 0xFF
        except Exception:
            messagebox.showerror("格式错误", "CMD/VAL 请输入 00–FF 的十六进制")
            return
        self._worker.send(cmd, val)

    def _update_manual_preview(self, _=None):
        try:
            cmd = int(self._man_cmd.get().strip(), 16)
            val = int(self._man_val.get().strip(), 16)
            pkt = build_packet(cmd, val)
            self._man_prev.configure(text=f"→  {pkt.hex(' ').upper()}", fg=C["yellow"])
        except Exception:
            self._man_prev.configure(text="→  (格式有误)", fg=C["red"])

    # ──────────────────────────────────────────────────────────
    # 日志
    # ──────────────────────────────────────────────────────────

    def _poll_log(self):
        try:
            while True:
                self._log(self._log_q.get_nowait())
        except queue.Empty:
            pass
        self.after(60, self._poll_log)

    def _log(self, item):
        level, text = item
        ts = time.strftime("%H:%M:%S")
        line = f"[{ts}]  {text}\n"
        self._log_text.configure(state="normal")
        self._log_text.insert("end", line, level)
        self._log_text.see("end")
        self._log_text.configure(state="disabled")

    def _clear_log(self):
        self._log_text.configure(state="normal")
        self._log_text.delete("1.0", "end")
        self._log_text.configure(state="disabled")

    # ──────────────────────────────────────────────────────────
    # 样式
    # ──────────────────────────────────────────────────────────

    def _style_notebook(self):
        s = ttk.Style()
        s.theme_use("default")
        s.configure("TNotebook", background=C["bg"], borderwidth=0, tabmargins=0)
        s.configure(
            "TNotebook.Tab",
            background=C["panel"],
            foreground=C["muted"],
            font=(FF, 10),
            padding=(14, 6),
        )
        s.map(
            "TNotebook.Tab",
            background=[("selected", C["panel2"])],
            foreground=[("selected", C["accent"])],
        )
        s.configure(
            "TCombobox",
            fieldbackground=C["bg"],
            background=C["panel"],
            foreground=C["text"],
            selectbackground=C["accent"],
            arrowcolor=C["accent"],
        )

    def _style_treeview(self):
        s = ttk.Style()
        s.configure(
            "Treeview",
            background=C["panel"],
            foreground=C["text"],
            fieldbackground=C["panel"],
            rowheight=22,
            font=SMALL,
        )
        s.configure(
            "Treeview.Heading",
            background=C["panel2"],
            foreground=C["accent"],
            font=MONO_B,
        )
        s.map(
            "Treeview",
            background=[("selected", C["accent"])],
            foreground=[("selected", C["bg"])],
        )

    # ──────────────────────────────────────────────────────────
    # 内置演示序列
    # ──────────────────────────────────────────────────────────

    def _make_demo_sequence(self) -> ActionSequence:
        """怯生生探头 → 发现主人 → 兴奋全展"""
        seq = ActionSequence("怯生生探头演示")
        for t, tilt, pan, expr, ease in [
            (0, 90, 90, "WORRIED", "linear"),
            (600, 68, 90, None, "ease_in_cubic"),
            (1400, 65, 90, "SURPRISED", "linear"),
            (1800, 65, 78, None, "ease_in_out"),
            (2100, 65, 90, None, "ease_in_out"),
            (2200, 50, 90, "HAPPY", "ease_out_elastic"),
            (3000, 50, 60, "EXCITED", "ease_out_elastic"),
            (3600, 50, 90, None, "ease_in_out"),
        ]:
            seq.add_frame(Keyframe(t, tilt, pan, expr, ease))
        return seq

    def destroy(self):
        self._stop_playback()
        if self._worker:
            self._worker.stop()
        super().destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()
