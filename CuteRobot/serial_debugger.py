#!/usr/bin/env python3
"""
CuteRobot 上位机控制器
协议格式: [0xAA] [CMD] [VAL] [CMD^VAL] [0x55]  (5字节定长)

依赖: pip install pyserial
"""

import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports
import threading
import queue
import time
import struct

# ─── 协议常量（与 RobotState.h 保持一致）─────────────────────
PACKET_HEAD = 0xAA
PACKET_TAIL = 0x55

CMD_SET_EXPRESSION  = 0x01
CMD_SET_AUTO_MODE   = 0x02
CMD_SET_SERVO       = 0x03   # 预留
CMD_SET_ROBOT_STATE = 0x04

ACK_OK          = 0x00
ACK_BAD_PACKET  = 0xE1
ACK_BAD_COMMAND = 0xE2
ACK_BAD_PARAM   = 0xE3

ACK_STATUS = {
    ACK_OK:          "OK",
    ACK_BAD_PACKET:  "错误: 包校验失败",
    ACK_BAD_COMMAND: "错误: 未知命令",
    ACK_BAD_PARAM:   "错误: 参数越界",
}

# ExpressionId  (与 RobotState.h 中的枚举数值严格对应)
EXPRESSIONS = {
    "E_ANGRY":      1,
    "E_BLINK":      4,
    "E_EXCITED":    8,
    "E_HAPPY":      11,
    "E_LOOK_DOWN":  12,
    "E_LOOK_LEFT":  13,
    "E_LOOK_RIGHT": 14,
    "E_LOOK_UP":    15,
    "E_NORMAL":     16,
    "E_SAD":        17,
    "E_SLEEPY":     19,
    "E_SURPRISED":  20,
    "E_WORRIED":    23,
    "E_LOGO":       28,
}

# RobotStateId  (与 RobotState.h 中的枚举数值严格对应)
ROBOT_STATES = {
    "RS_IDLE":      0,
    "RS_HAPPY":     1,
    "RS_SAD":       2,
    "RS_ANGRY":     3,
    "RS_SLEEPY":    4,
    "RS_SURPRISED": 5,
    "RS_EXCITED":   6,
    "RS_WORRIED":   7,
}

# 表情 emoji 映射（纯显示用，不影响协议）
EXPR_EMOJI = {
    "E_ANGRY":      "😠", "E_BLINK":     "😑", "E_EXCITED":   "🤩",
    "E_HAPPY":      "😊", "E_LOOK_DOWN": "👇", "E_LOOK_LEFT": "👈",
    "E_LOOK_RIGHT": "👉", "E_LOOK_UP":   "👆", "E_NORMAL":    "😐",
    "E_SAD":        "😢", "E_SLEEPY":    "😴", "E_SURPRISED": "😲",
    "E_WORRIED":    "😟", "E_LOGO":      "🤖",
}

STATE_EMOJI = {
    "RS_IDLE":      "⏸", "RS_HAPPY":     "😊", "RS_SAD":       "😢",
    "RS_ANGRY":     "😠", "RS_SLEEPY":    "😴", "RS_SURPRISED": "😲",
    "RS_EXCITED":   "🤩", "RS_WORRIED":   "😟",
}

BAUD_RATE = 115200


# ─── 协议工具 ─────────────────────────────────────────────────

def build_packet(cmd: int, val: int = 0x00) -> bytes:
    csum = cmd ^ val
    return struct.pack("5B", PACKET_HEAD, cmd, val, csum, PACKET_TAIL)


def parse_ack(data: bytes):
    """尝试从 data 中解析第一个完整 ACK 包，返回 (cmd, status) 或 None"""
    for i in range(len(data) - 4):
        if data[i] == PACKET_HEAD and data[i + 4] == PACKET_TAIL:
            cmd  = data[i + 1]
            sta  = data[i + 2]
            csum = data[i + 3]
            if (cmd ^ sta) == csum:
                return cmd, sta
    return None


# ─── 串口线程 ─────────────────────────────────────────────────

class SerialWorker(threading.Thread):
    """后台线程：负责发送队列中的包，并接收 ACK"""

    def __init__(self, port: str, log_q: queue.Queue):
        super().__init__(daemon=True)
        self.port   = port
        self.log_q  = log_q          # 日志回调队列 → (level, text)
        self.send_q: queue.Queue = queue.Queue()
        self._ser: serial.Serial | None = None
        self._stop  = threading.Event()

    def send(self, cmd: int, val: int = 0):
        self.send_q.put((cmd, val))

    def stop(self):
        self._stop.set()

    def run(self):
        try:
            self._ser = serial.Serial(self.port, BAUD_RATE, timeout=0.1)
            # Arduino 复位后需要约 1.5s 才能接受串口命令
            time.sleep(1.6)
            self.log_q.put(("ok", f"已连接 {self.port} @ {BAUD_RATE}"))
        except serial.SerialException as e:
            self.log_q.put(("err", f"打开串口失败: {e}"))
            return

        rx_buf = bytearray()

        while not self._stop.is_set():
            # 发送
            try:
                cmd, val = self.send_q.get_nowait()
                pkt = build_packet(cmd, val)
                self._ser.write(pkt)
                self.log_q.put(("tx", f"TX  {pkt.hex(' ').upper()}"))
            except queue.Empty:
                pass

            # 接收
            waiting = self._ser.in_waiting
            if waiting:
                rx_buf += self._ser.read(waiting)
                while len(rx_buf) >= 5:
                    result = parse_ack(rx_buf)
                    if result:
                        cmd_r, sta_r = result
                        desc = ACK_STATUS.get(sta_r, f"0x{sta_r:02X}")
                        level = "ok" if sta_r == ACK_OK else "err"
                        self.log_q.put((level,
                            f"ACK cmd=0x{cmd_r:02X}  status={desc}"))
                        rx_buf = rx_buf[5:]   # 消费一个包
                    else:
                        rx_buf.pop(0)         # 丢弃非法首字节

            time.sleep(0.01)

        self._ser.close()
        self.log_q.put(("info", "串口已关闭"))


# ─── 主 GUI ───────────────────────────────────────────────────

class App(tk.Tk):
    # ── 调色板 ────────────────────────────────────────────────
    C_BG      = "#0f0f13"   # 深底
    C_PANEL   = "#1a1a22"   # 面板
    C_BORDER  = "#2e2e3e"   # 边框
    C_ACCENT  = "#7c6af7"   # 紫色强调
    C_ACCENT2 = "#f06292"   # 粉红辅助
    C_GREEN   = "#4caf50"
    C_RED     = "#ef5350"
    C_YELLOW  = "#ffd54f"
    C_TEXT    = "#e8e8f0"
    C_MUTED   = "#6b6b82"
    C_TX      = "#80cbc4"   # 发送日志色
    C_RX_OK   = "#a5d6a7"   # ACK OK 色
    C_RX_ERR  = "#ef9a9a"   # ACK ERR 色

    FONT_TITLE  = ("Courier New", 13, "bold")
    FONT_LABEL  = ("Courier New", 10)
    FONT_BTN    = ("Courier New", 10, "bold")
    FONT_LOG    = ("Courier New", 9)
    FONT_MONO   = ("Courier New", 11, "bold")

    def __init__(self):
        super().__init__()
        self.title("CuteRobot Controller June 2025")
        self.configure(bg=self.C_BG)
        self.resizable(False, False)

        self._worker: SerialWorker | None = None
        self._log_q: queue.Queue = queue.Queue()
        self._connected = False

        self._build_ui()
        self._refresh_ports()
        self._poll_log()

    # ── UI 构建 ───────────────────────────────────────────────

    def _build_ui(self):
        root = self

        # ── 顶栏 ─────────────────────────────────────────────
        top = tk.Frame(root, bg=self.C_BG, pady=10)
        top.pack(fill="x", padx=16)

        tk.Label(top, text="◈ CUTE ROBOT CONTROLLER",
                 font=("Courier New", 15, "bold"),
                 fg=self.C_ACCENT, bg=self.C_BG).pack(side="left")

        # 连接状态指示灯
        self._dot = tk.Label(top, text="●", font=("Courier New", 18),
                              fg=self.C_RED, bg=self.C_BG)
        self._dot.pack(side="right", padx=(0, 4))
        self._dot_label = tk.Label(top, text="未连接",
                                    font=self.FONT_LABEL,
                                    fg=self.C_MUTED, bg=self.C_BG)
        self._dot_label.pack(side="right")

        # ── 分隔线 ────────────────────────────────────────────
        self._hr(root)

        # ── 连接区 ────────────────────────────────────────────
        conn = self._panel(root, "串口连接")
        row = tk.Frame(conn, bg=self.C_PANEL)
        row.pack(fill="x", pady=4)

        tk.Label(row, text="端口", font=self.FONT_LABEL,
                 fg=self.C_MUTED, bg=self.C_PANEL, width=5).pack(side="left")

        self._port_var = tk.StringVar()
        self._port_cb = ttk.Combobox(row, textvariable=self._port_var,
                                      width=16, font=self.FONT_MONO,
                                      state="readonly")
        self._style_combobox()
        self._port_cb.pack(side="left", padx=6)

        self._btn_refresh = self._mk_btn(row, "⟳ 刷新",
                                          self._refresh_ports, self.C_MUTED)
        self._btn_refresh.pack(side="left", padx=4)

        self._btn_connect = self._mk_btn(row, "连接",
                                          self._toggle_connect, self.C_ACCENT)
        self._btn_connect.pack(side="left", padx=4)

        # ── 分隔线 ────────────────────────────────────────────
        self._hr(root)

        # ── 主体：左右两列 ────────────────────────────────────
        body = tk.Frame(root, bg=self.C_BG)
        body.pack(fill="both", padx=12, pady=4)

        left  = tk.Frame(body, bg=self.C_BG)
        right = tk.Frame(body, bg=self.C_BG)
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        right.pack(side="left", fill="both", expand=True)

        # ── 左列：机器人状态 ──────────────────────────────────
        sp = self._panel(left, "机器人状态  (眼睛 + 舵机)")
        self._build_state_buttons(sp)

        # 自动模式按钮单独一行
        auto_row = tk.Frame(sp, bg=self.C_PANEL)
        auto_row.pack(fill="x", pady=(10, 2))
        self._mk_btn(auto_row, "⟳  AUTO MODE  (眼睛自动 + 舵机归中)",
                     self._send_auto_mode, self.C_ACCENT2,
                     width=38).pack(fill="x")

        # ── 右列：单独表情 ────────────────────────────────────
        ep = self._panel(right, "单独控制眼睛表情")
        self._build_expr_buttons(ep)

        # ── 手动发包区 ────────────────────────────────────────
        self._hr(root)
        mp = self._panel(root, "手动发包  [AA] [CMD] [VAL] [CSUM] [55]")
        self._build_manual_panel(mp)

        # ── 日志区 ────────────────────────────────────────────
        self._hr(root)
        lp = self._panel(root, "通信日志")
        self._build_log(lp)

    def _build_state_buttons(self, parent):
        GRID = [
            ("RS_IDLE",      0, 0), ("RS_HAPPY",     0, 1),
            ("RS_SAD",       1, 0), ("RS_ANGRY",     1, 1),
            ("RS_SLEEPY",    2, 0), ("RS_SURPRISED", 2, 1),
            ("RS_EXCITED",   3, 0), ("RS_WORRIED",   3, 1),
        ]
        frame = tk.Frame(parent, bg=self.C_PANEL)
        frame.pack(fill="x")
        for name, r, c in GRID:
            val  = ROBOT_STATES[name]
            em   = STATE_EMOJI.get(name, "")
            label= f"{em}  {name}  [{val}]"
            btn  = self._mk_btn(frame, label,
                                lambda v=val, n=name: self._send_state(v, n),
                                self.C_ACCENT, width=24)
            btn.grid(row=r, column=c, padx=4, pady=3, sticky="ew")
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

    def _build_expr_buttons(self, parent):
        GRID = [
            ("E_NORMAL",    0, 0), ("E_HAPPY",     0, 1),
            ("E_SAD",       1, 0), ("E_ANGRY",     1, 1),
            ("E_EXCITED",   2, 0), ("E_SURPRISED", 2, 1),
            ("E_SLEEPY",    3, 0), ("E_WORRIED",   3, 1),
            ("E_BLINK",     4, 0), ("E_LOGO",      4, 1),
            ("E_LOOK_LEFT", 5, 0), ("E_LOOK_RIGHT",5, 1),
            ("E_LOOK_UP",   6, 0), ("E_LOOK_DOWN", 6, 1),
        ]
        frame = tk.Frame(parent, bg=self.C_PANEL)
        frame.pack(fill="x")
        for name, r, c in GRID:
            val  = EXPRESSIONS[name]
            em   = EXPR_EMOJI.get(name, "")
            label= f"{em} {name}  [{val}]"
            btn  = self._mk_btn(frame, label,
                                lambda v=val, n=name: self._send_expr(v, n),
                                "#3d5a80", width=22)
            btn.grid(row=r, column=c, padx=4, pady=2, sticky="ew")
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

    def _build_manual_panel(self, parent):
        row = tk.Frame(parent, bg=self.C_PANEL)
        row.pack(fill="x", pady=4)

        tk.Label(row, text="CMD (hex)", font=self.FONT_LABEL,
                 fg=self.C_MUTED, bg=self.C_PANEL).pack(side="left")
        self._man_cmd = tk.Entry(row, width=6, font=self.FONT_MONO,
                                  bg=self.C_BG, fg=self.C_TEXT,
                                  insertbackground=self.C_TEXT,
                                  relief="flat", bd=1)
        self._man_cmd.insert(0, "04")
        self._man_cmd.pack(side="left", padx=6)

        tk.Label(row, text="VAL (hex)", font=self.FONT_LABEL,
                 fg=self.C_MUTED, bg=self.C_PANEL).pack(side="left")
        self._man_val = tk.Entry(row, width=6, font=self.FONT_MONO,
                                  bg=self.C_BG, fg=self.C_TEXT,
                                  insertbackground=self.C_TEXT,
                                  relief="flat", bd=1)
        self._man_val.insert(0, "01")
        self._man_val.pack(side="left", padx=6)

        # 预览
        self._man_preview = tk.Label(row, text="→  AA 04 01 05 55",
                                      font=self.FONT_MONO,
                                      fg=self.C_YELLOW, bg=self.C_PANEL)
        self._man_preview.pack(side="left", padx=12)

        self._mk_btn(row, "发送", self._send_manual,
                     self.C_ACCENT2, width=8).pack(side="right")

        # 绑定实时预览
        for w in (self._man_cmd, self._man_val):
            w.bind("<KeyRelease>", self._update_preview)

    def _build_log(self, parent):
        frame = tk.Frame(parent, bg=self.C_PANEL)
        frame.pack(fill="both", expand=True)

        self._log_text = tk.Text(
            frame, height=9, font=self.FONT_LOG,
            bg="#090910", fg=self.C_TEXT,
            relief="flat", bd=0, state="disabled",
            selectbackground=self.C_BORDER,
        )
        self._log_text.pack(side="left", fill="both", expand=True)

        sb = tk.Scrollbar(frame, command=self._log_text.yview,
                          bg=self.C_BORDER, troughcolor=self.C_BG,
                          activebackground=self.C_ACCENT)
        sb.pack(side="right", fill="y")
        self._log_text.configure(yscrollcommand=sb.set)

        # 颜色标签
        self._log_text.tag_config("tx",   foreground=self.C_TX)
        self._log_text.tag_config("ok",   foreground=self.C_RX_OK)
        self._log_text.tag_config("err",  foreground=self.C_RX_ERR)
        self._log_text.tag_config("info", foreground=self.C_MUTED)

        clr = self._mk_btn(parent, "清空日志",
                            self._clear_log, self.C_MUTED, width=12)
        clr.pack(anchor="e", pady=(4, 0))

    # ── 辅助 Widget 工厂 ──────────────────────────────────────

    def _panel(self, parent, title: str) -> tk.Frame:
        outer = tk.Frame(parent, bg=self.C_PANEL,
                         highlightthickness=1,
                         highlightbackground=self.C_BORDER)
        outer.pack(fill="x", padx=4, pady=6)
        tk.Label(outer, text=f"  {title}",
                 font=self.FONT_TITLE, fg=self.C_ACCENT,
                 bg=self.C_BORDER, anchor="w"
                 ).pack(fill="x")
        inner = tk.Frame(outer, bg=self.C_PANEL, padx=10, pady=8)
        inner.pack(fill="x")
        return inner

    def _hr(self, parent):
        tk.Frame(parent, bg=self.C_BORDER, height=1).pack(fill="x", padx=8)

    def _mk_btn(self, parent, text, cmd, color, width=None) -> tk.Button:
        kw = dict(
            text=text, command=cmd,
            font=self.FONT_BTN,
            bg=self.C_PANEL, fg=color,
            activebackground=self.C_BORDER,
            activeforeground=color,
            relief="flat", bd=0,
            cursor="hand2",
            padx=8, pady=4,
            highlightthickness=1,
            highlightbackground=self.C_BORDER,
        )
        if width:
            kw["width"] = width
        b = tk.Button(parent, **kw)
        b.bind("<Enter>", lambda e, w=b, c=color: w.configure(bg=self.C_BORDER))
        b.bind("<Leave>", lambda e, w=b: w.configure(bg=self.C_PANEL))
        return b

    def _style_combobox(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TCombobox",
                         fieldbackground=self.C_BG,
                         background=self.C_PANEL,
                         foreground=self.C_TEXT,
                         selectbackground=self.C_ACCENT,
                         selectforeground=self.C_TEXT,
                         arrowcolor=self.C_ACCENT)

    # ── 串口控制 ──────────────────────────────────────────────

    def _refresh_ports(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self._port_cb["values"] = ports
        if ports and not self._port_var.get():
            self._port_var.set(ports[0])

    def _toggle_connect(self):
        if self._connected:
            self._disconnect()
        else:
            self._connect()

    def _connect(self):
        port = self._port_var.get()
        if not port:
            messagebox.showerror("错误", "请先选择串口")
            return
        self._worker = SerialWorker(port, self._log_q)
        self._worker.start()
        self._connected = True
        self._btn_connect.configure(text="断开", fg=self.C_RED)
        self._dot.configure(fg=self.C_GREEN)
        self._dot_label.configure(text=port)

    def _disconnect(self):
        if self._worker:
            self._worker.stop()
            self._worker = None
        self._connected = False
        self._btn_connect.configure(text="连接", fg=self.C_ACCENT)
        self._dot.configure(fg=self.C_RED)
        self._dot_label.configure(text="未连接")

    # ── 发包动作 ──────────────────────────────────────────────

    def _require_connected(self) -> bool:
        if not self._connected or not self._worker:
            messagebox.showwarning("未连接", "请先连接串口")
            return False
        return True

    def _send_state(self, val: int, name: str):
        if not self._require_connected():
            return
        self._worker.send(CMD_SET_ROBOT_STATE, val)
        self._log(("info", f"→ SET_ROBOT_STATE  {name} ({val})"))

    def _send_expr(self, val: int, name: str):
        if not self._require_connected():
            return
        self._worker.send(CMD_SET_EXPRESSION, val)
        self._log(("info", f"→ SET_EXPRESSION   {name} ({val})"))

    def _send_auto_mode(self):
        if not self._require_connected():
            return
        self._worker.send(CMD_SET_AUTO_MODE, 0x00)
        self._log(("info", "→ SET_AUTO_MODE"))

    def _send_manual(self):
        if not self._require_connected():
            return
        try:
            cmd = int(self._man_cmd.get().strip(), 16)
            val = int(self._man_val.get().strip(), 16)
            assert 0 <= cmd <= 0xFF and 0 <= val <= 0xFF
        except Exception:
            messagebox.showerror("格式错误", "CMD 和 VAL 请输入 0–FF 之间的十六进制数")
            return
        self._worker.send(cmd, val)

    # ── 日志 ──────────────────────────────────────────────────

    def _update_preview(self, _event=None):
        try:
            cmd = int(self._man_cmd.get().strip(), 16)
            val = int(self._man_val.get().strip(), 16)
            pkt = build_packet(cmd, val)
            self._man_preview.configure(
                text=f"→  {pkt.hex(' ').upper()}", fg=self.C_YELLOW)
        except Exception:
            self._man_preview.configure(text="→  (格式有误)", fg=self.C_RED)

    def _poll_log(self):
        try:
            while True:
                item = self._log_q.get_nowait()
                self._log(item)
        except queue.Empty:
            pass
        self.after(80, self._poll_log)

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

    def destroy(self):
        self._disconnect()
        super().destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()