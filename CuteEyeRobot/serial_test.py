import argparse
import sys
import time
import tkinter as tk
from tkinter import messagebox, ttk

import serial
from serial.tools import list_ports

PACKET_HEAD = 0xAA
PACKET_TAIL = 0x55
CMD_SET_EXPRESSION = 0x01
CMD_SET_AUTO_MODE = 0x02

EXPRESSIONS = {
    0: "alert",
    1: "angry",
    2: "blink_down",
    3: "blink_up",
    4: "blink",
    5: "bored",
    6: "despair",
    7: "disoriented",
    8: "excited",
    9: "focused",
    10: "furious",
    11: "happy",
    12: "look_down",
    13: "look_left",
    14: "look_right",
    15: "look_up",
    16: "normal",
    17: "sad",
    18: "scared",
    19: "sleepy",
    20: "surprised",
    21: "wink_left",
    22: "wink_right",
    23: "worried",
    24: "battery_full",
    25: "battery_low",
    26: "battery",
    27: "left_signal",
    28: "logo",
    29: "mode",
    30: "right_signal",
    31: "warning",
}

NAME_TO_ID = {name: idx for idx, name in EXPRESSIONS.items()}
STATUS_TEXT = {
    0x00: "ok",
    0xE1: "bad_packet",
    0xE2: "bad_command",
    0xE3: "bad_param",
}
UNO_SUPPORTED_IDS = {
    1,   # angry
    4,   # blink
    8,   # excited
    11,  # happy
    12,  # look_down
    13,  # look_left
    14,  # look_right
    15,  # look_up
    16,  # normal
    17,  # sad
    19,  # sleepy
    20,  # surprised
    23,  # worried
    28,  # logo
}


def build_packet(command: int, value: int) -> bytes:
    checksum = command ^ value
    return bytes((PACKET_HEAD, command, value, checksum, PACKET_TAIL))


def parse_expression(value: str) -> int:
    if value.isdigit():
        expr_id = int(value)
    else:
        expr_id = NAME_TO_ID.get(value.lower(), -1)

    if expr_id not in EXPRESSIONS:
        raise argparse.ArgumentTypeError(
            f"Unknown expression '{value}'. Use --list to see valid IDs."
        )
    return expr_id


def get_serial_ports() -> list[tuple[str, str]]:
    ports = []
    for port in list_ports.comports():
        ports.append((port.device, port.description))
    ports.sort(key=lambda item: item[0])
    return ports


def list_serial_ports() -> None:
    ports = get_serial_ports()
    if not ports:
        print("No serial ports found.")
        return

    print("Available serial ports:")
    for device, description in ports:
        print(f"  {device:<10} {description}")


def list_expressions() -> None:
    print("Available expressions:")
    for expr_id, name in EXPRESSIONS.items():
        print(f"  {expr_id:>2}  {name}")


def decode_ack(ack: bytes) -> tuple[bool, str]:
    if not ack:
        return False, "No ACK received."

    if len(ack) != 5:
        return False, f"Incomplete ACK: expected 5 bytes, got {len(ack)} bytes."

    if ack[0] != PACKET_HEAD or ack[4] != PACKET_TAIL:
        return False, "Malformed ACK frame."

    expected_checksum = ack[1] ^ ack[2]
    if ack[3] != expected_checksum:
        return False, "ACK checksum mismatch."

    status = ack[2]
    status_name = STATUS_TEXT.get(status, "unknown")
    return status == 0x00, f"ACK status: 0x{status:02X} ({status_name})"


def transmit_packet(
    port: str,
    baudrate: int,
    payload: bytes,
    timeout: float,
) -> tuple[bool, str, bytes | None]:
    with serial.Serial(port, baudrate=baudrate, timeout=timeout) as ser:
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        time.sleep(0.2)
        ser.write(payload)
        ser.flush()
        ack = ser.read(5)

    ok, message = decode_ack(ack)
    return ok, message, ack or None


def send_packet(port: str, baudrate: int, payload: bytes, timeout: float) -> int:
    print(f"Opening {port} @ {baudrate}...")
    print("TX:", payload.hex(" ").upper())

    try:
        ok, message, ack = transmit_packet(port, baudrate, payload, timeout)
    except serial.SerialException as exc:
        print(f"Serial error: {exc}")
        return 1

    if ack:
        print("RX:", ack.hex(" ").upper())
    print(message)
    return 0 if ok else 1


class SerialControlApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("CuteEyeRobot Serial Control")
        self.root.geometry("980x720")
        self.root.minsize(900, 640)

        self.port_var = tk.StringVar()
        self.baudrate_var = tk.StringVar(value="115200")
        self.timeout_var = tk.StringVar(value="1.0")
        self.status_var = tk.StringVar(value="Ready")
        self.mode_var = tk.StringVar(value="uno")
        self.expression_buttons: dict[int, ttk.Button] = {}

        self._build_ui()
        self.refresh_ports(select_first=True)
        self.update_expression_buttons()

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(2, weight=1)
        self.root.rowconfigure(3, weight=1)

        top = ttk.Frame(self.root, padding=12)
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(1, weight=1)

        ttk.Label(top, text="Serial Port").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.port_combo = ttk.Combobox(
            top,
            textvariable=self.port_var,
            state="readonly",
            width=24,
        )
        self.port_combo.grid(row=0, column=1, sticky="ew", padx=(0, 8))

        ttk.Button(top, text="Refresh", command=self.refresh_ports).grid(
            row=0, column=2, padx=(0, 12)
        )

        ttk.Label(top, text="Baud").grid(row=0, column=3, sticky="w", padx=(0, 8))
        ttk.Entry(top, textvariable=self.baudrate_var, width=10).grid(
            row=0, column=4, padx=(0, 12)
        )

        ttk.Label(top, text="Timeout").grid(row=0, column=5, sticky="w", padx=(0, 8))
        ttk.Entry(top, textvariable=self.timeout_var, width=8).grid(row=0, column=6)

        action_bar = ttk.Frame(self.root, padding=(12, 0, 12, 12))
        action_bar.grid(row=1, column=0, sticky="ew")
        action_bar.columnconfigure(4, weight=1)

        ttk.Button(action_bar, text="Auto Mode", command=self.send_auto_mode).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Button(action_bar, text="List Ports To Log", command=self.log_ports).grid(
            row=0, column=1, sticky="w", padx=(8, 0)
        )
        ttk.Label(action_bar, text="Firmware").grid(row=0, column=2, sticky="w", padx=(16, 8))
        firmware_combo = ttk.Combobox(
            action_bar,
            textvariable=self.mode_var,
            state="readonly",
            width=12,
            values=("uno", "full"),
        )
        firmware_combo.grid(row=0, column=3, sticky="w")
        firmware_combo.bind("<<ComboboxSelected>>", lambda _event: self.update_expression_buttons())

        expression_frame = ttk.LabelFrame(
            self.root, text="Expressions", padding=12
        )
        expression_frame.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 12))

        for column in range(4):
            expression_frame.columnconfigure(column, weight=1)

        for idx, name in EXPRESSIONS.items():
            label = f"{idx:02d} {name}"
            button = ttk.Button(
                expression_frame,
                text=label,
                command=lambda expr_id=idx: self.send_expression(expr_id),
            )
            self.expression_buttons[idx] = button
            row = idx // 4
            column = idx % 4
            button.grid(row=row, column=column, sticky="ew", padx=4, pady=4)

        log_frame = ttk.LabelFrame(self.root, text="Log", padding=12)
        log_frame.grid(row=3, column=0, sticky="nsew", padx=12, pady=(0, 12))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log_text = tk.Text(log_frame, height=14, wrap="word")
        self.log_text.grid(row=0, column=0, sticky="nsew")
        self.log_text.configure(state="disabled")

        log_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        log_scroll.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=log_scroll.set)

        status_bar = ttk.Label(
            self.root,
            textvariable=self.status_var,
            anchor="w",
            padding=(12, 6),
        )
        status_bar.grid(row=4, column=0, sticky="ew")

    def append_log(self, message: str) -> None:
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"[{timestamp}] {message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def refresh_ports(self, select_first: bool = False) -> None:
        ports = get_serial_ports()
        values = [device for device, _ in ports]
        self.port_combo["values"] = values

        current = self.port_var.get()
        if current in values:
            self.port_combo.set(current)
        elif values and select_first:
            self.port_combo.set(values[0])
        elif not values:
            self.port_var.set("")

        if ports:
            self.status_var.set(f"Found {len(ports)} serial port(s)")
        else:
            self.status_var.set("No serial ports found")

    def log_ports(self) -> None:
        ports = get_serial_ports()
        if not ports:
            self.append_log("No serial ports found.")
            return

        for device, description in ports:
            self.append_log(f"{device}: {description}")

    def is_expression_supported(self, expression_id: int) -> bool:
        if self.mode_var.get() == "full":
            return True
        return expression_id in UNO_SUPPORTED_IDS

    def update_expression_buttons(self) -> None:
        supported_count = 0
        for expression_id, button in self.expression_buttons.items():
            if self.is_expression_supported(expression_id):
                button.state(["!disabled"])
                supported_count += 1
            else:
                button.state(["disabled"])

        mode_name = self.mode_var.get().upper()
        self.status_var.set(
            f"{mode_name} mode selected, {supported_count} expression(s) enabled"
        )
        self.append_log(
            f"Firmware profile set to {self.mode_var.get()} ({supported_count} supported IDs)"
        )

    def _read_connection_settings(self) -> tuple[str, int, float] | None:
        port = self.port_var.get().strip()
        if not port:
            messagebox.showwarning("Missing Port", "Please choose a serial port first.")
            return None

        try:
            baudrate = int(self.baudrate_var.get().strip())
        except ValueError:
            messagebox.showwarning("Invalid Baudrate", "Baudrate must be an integer.")
            return None

        try:
            timeout = float(self.timeout_var.get().strip())
        except ValueError:
            messagebox.showwarning("Invalid Timeout", "Timeout must be a number.")
            return None

        return port, baudrate, timeout

    def _send_payload(self, payload: bytes, action_name: str) -> None:
        settings = self._read_connection_settings()
        if settings is None:
            return

        port, baudrate, timeout = settings
        self.append_log(f"{action_name} -> TX {payload.hex(' ').upper()}")

        try:
            ok, message, ack = transmit_packet(port, baudrate, payload, timeout)
        except serial.SerialException as exc:
            error_message = f"Serial error: {exc}"
            self.status_var.set(error_message)
            self.append_log(error_message)
            messagebox.showerror("Serial Error", error_message)
            return

        if ack:
            self.append_log(f"{action_name} <- RX {ack.hex(' ').upper()}")

        self.append_log(message)
        self.status_var.set(message)

    def send_expression(self, expression_id: int) -> None:
        if not self.is_expression_supported(expression_id):
            message = (
                f"Expression {expression_id} ({EXPRESSIONS[expression_id]}) is not "
                f"enabled for {self.mode_var.get()} firmware."
            )
            self.status_var.set(message)
            self.append_log(message)
            return

        name = EXPRESSIONS[expression_id]
        payload = build_packet(CMD_SET_EXPRESSION, expression_id)
        self._send_payload(payload, f"expression {expression_id} ({name})")

    def send_auto_mode(self) -> None:
        payload = build_packet(CMD_SET_AUTO_MODE, 0x00)
        self._send_payload(payload, "auto mode")


def run_gui() -> int:
    root = tk.Tk()
    ttk.Style(root).theme_use("clam")
    app = SerialControlApp(root)
    app.append_log("GUI ready. Choose a port and click an expression.")
    root.mainloop()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="CuteEyeRobot serial protocol test tool"
    )
    parser.add_argument("--port", help="Serial port, for example COM5")
    parser.add_argument("--baudrate", type=int, default=115200, help="Serial baudrate")
    parser.add_argument(
        "--timeout", type=float, default=1.0, help="Read timeout in seconds"
    )
    parser.add_argument(
        "--list-ports", action="store_true", help="List available serial ports"
    )
    parser.add_argument(
        "--list", action="store_true", help="List supported expression IDs"
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Force command-line mode instead of starting the Tkinter GUI",
    )

    subparsers = parser.add_subparsers(dest="command")

    expr_parser = subparsers.add_parser("expression", help="Switch to a fixed expression")
    expr_parser.add_argument(
        "expression",
        type=parse_expression,
        help="Expression name or numeric ID",
    )

    subparsers.add_parser("auto", help="Return robot to auto animation mode")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.list_ports:
        list_serial_ports()
        return 0

    if args.list:
        list_expressions()
        return 0

    if not args.cli and not args.command:
        return run_gui()

    if not args.command:
        parser.print_help()
        return 0

    if not args.port:
        parser.error("--port is required when sending a command")

    if args.command == "expression":
        payload = build_packet(CMD_SET_EXPRESSION, args.expression)
        return send_packet(args.port, args.baudrate, payload, args.timeout)

    if args.command == "auto":
        payload = build_packet(CMD_SET_AUTO_MODE, 0x00)
        return send_packet(args.port, args.baudrate, payload, args.timeout)

    print(f"Unsupported command: {args.command}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
