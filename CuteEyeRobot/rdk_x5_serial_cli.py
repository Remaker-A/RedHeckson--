#!/usr/bin/env python3

import argparse
import glob
import sys
import time

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    serial = None
    list_ports = None

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

NAME_TO_ID = {name: expr_id for expr_id, name in EXPRESSIONS.items()}
STATUS_TEXT = {
    0x00: "ok",
    0xE1: "bad_packet",
    0xE2: "bad_command",
    0xE3: "bad_param",
}


def build_packet(command: int, value: int) -> bytes:
    checksum = command ^ value
    return bytes((PACKET_HEAD, command, value, checksum, PACKET_TAIL))


def parse_expression(value: str) -> int:
    if value.isdigit():
        expression_id = int(value)
    else:
        expression_id = NAME_TO_ID.get(value.lower(), -1)

    if expression_id not in EXPRESSIONS:
        raise argparse.ArgumentTypeError(
            f"Unknown expression '{value}'. Use --list-expressions to inspect IDs."
        )
    return expression_id


def discover_ports() -> list[str]:
    devices: set[str] = set()
    if list_ports is not None:
        devices.update(port.device for port in list_ports.comports())
    devices.update(glob.glob("/dev/tty[A-Za-z]*"))
    devices.update(glob.glob("/dev/ttyS*"))
    devices.update(glob.glob("/dev/ttyUSB*"))
    devices.update(glob.glob("/dev/ttyACM*"))
    return sorted(devices)


def list_serial_ports() -> None:
    ports = discover_ports()
    if not ports:
        print("No serial ports found.")
        return

    print("Available serial ports:")
    for device in ports:
        print(f"  {device}")


def list_expressions() -> None:
    print("Available expressions:")
    for expression_id, name in EXPRESSIONS.items():
        print(f"  {expression_id:>2}  {name}")


def ensure_pyserial() -> bool:
    if serial is not None:
        return True

    print("pyserial is not installed. Please run: pip install pyserial")
    return False


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


def transmit_packet(port: str, baudrate: int, payload: bytes, timeout: float) -> tuple[bool, str]:
    if not ensure_pyserial():
        return False, "pyserial is not installed."

    with serial.Serial(port, baudrate=baudrate, timeout=timeout) as ser:
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        time.sleep(0.2)
        ser.write(payload)
        ser.flush()
        ack = ser.read(5)

    return decode_ack(ack)


def send_packet(port: str, baudrate: int, payload: bytes, timeout: float) -> int:
    print(f"Opening {port} @ {baudrate}...")
    print("TX:", payload.hex(" ").upper())

    try:
        ok, message = transmit_packet(port, baudrate, payload, timeout)
    except serial.SerialException as exc:
        print(f"Serial error: {exc}")
        return 1

    print(message)
    return 0 if ok else 1


def run_interactive() -> int:
    if not ensure_pyserial():
        return 1

    print("List of enabled UART:")
    list_serial_ports()

    port = input("请输入需要测试的串口设备名: ").strip()
    if not port:
        print("No serial port selected.")
        return 1

    baudrate_text = input(
        "请输入波特率(9600,19200,38400,57600,115200,921600): "
    ).strip()
    try:
        baudrate = int(baudrate_text)
    except ValueError:
        print("Invalid baudrate.")
        return 1

    print("输入表情名/ID 发送表情，输入 auto 切回自动模式，输入 list 查看表情，输入 quit 退出。")

    while True:
        raw = input("emoji> ").strip()
        if not raw:
            continue

        command = raw.lower()
        if command in {"quit", "exit", "q"}:
            return 0
        if command == "list":
            list_expressions()
            continue
        if command == "auto":
            payload = build_packet(CMD_SET_AUTO_MODE, 0x00)
            send_packet(port, baudrate, payload, timeout=1.0)
            continue

        try:
            expression_id = parse_expression(raw)
        except argparse.ArgumentTypeError as exc:
            print(exc)
            continue

        payload = build_packet(CMD_SET_EXPRESSION, expression_id)
        send_packet(port, baudrate, payload, timeout=1.0)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="RDK X5 serial CLI for CuteEyeRobot expressions"
    )
    parser.add_argument("--port", help="Serial device, for example /dev/ttyS3")
    parser.add_argument("--baudrate", type=int, default=115200, help="Serial baudrate")
    parser.add_argument(
        "--timeout", type=float, default=1.0, help="Read timeout in seconds"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Start prompt mode similar to the RDK X5 serial demo",
    )
    parser.add_argument(
        "--list-ports", action="store_true", help="List available serial ports"
    )
    parser.add_argument(
        "--list-expressions", action="store_true", help="List supported expression IDs"
    )

    subparsers = parser.add_subparsers(dest="command")

    expression_parser = subparsers.add_parser(
        "expression", help="Switch to a fixed expression"
    )
    expression_parser.add_argument(
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

    if args.list_expressions:
        list_expressions()
        return 0

    if args.interactive:
        return run_interactive()

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
