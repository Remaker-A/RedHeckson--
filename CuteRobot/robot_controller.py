"""
robot_controller.py - RDK X5 无屏幕控制中枢

功能:
  - 加载预设动作 JSON
  - 监听触发条件执行动作
  - 支持: GPIO按键 / HTTP API / 串口指令

用法:
  python robot_controller.py [--json actions.json] [--port /dev/ttyUSB0]
"""
import argparse
import json
import queue
import sys
import time
import threading
from pathlib import Path

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False

from robot_protocol import (
    SerialWorker, ActionSequence, Keyframe,
    build_packet, encode_servo,
    CMD_SET_SERVO, CMD_SET_EXPRESSION, EXPRESSIONS,
)


class RobotController:
    def __init__(self, port: str, action_file: str | None = None):
        self.port = port
        self.log_q: queue.Queue = queue.Queue()
        self.worker: SerialWorker | None = None
        self.current_sequence: ActionSequence | None = None
        self.is_playing = False
        self.action_file = action_file

    def connect(self):
        self.worker = SerialWorker(self.port, self.log_q)
        self.worker.start()
        time.sleep(2)

    def disconnect(self):
        if self.worker:
            self.worker.stop()
            self.worker.join(timeout=2)

    def play_sequence(self, seq: ActionSequence):
        if self.is_playing:
            return
        self.is_playing = True

        packets = seq.build_playback_packets(interval_ms=20)
        if not packets:
            self.is_playing = False
            return

        t_start = time.monotonic() * 1000
        total = packets[-1][0] or 1
        idx = 0

        while idx < len(packets) and self.is_playing:
            now_ms = time.monotonic() * 1000 - t_start
            while idx < len(packets) and packets[idx][0] <= now_ms:
                self.worker.send_raw(packets[idx][1])
                idx += 1
            time.sleep(0.005)

        self.is_playing = False

    def stop(self):
        self.is_playing = False

    def load_actions(self, filepath: str) -> list[ActionSequence]:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [ActionSequence.from_dict(d) for d in data]

    def log_listener(self):
        while True:
            try:
                level, msg = self.log_q.get(timeout=1)
                prefix = {"ok": "✓", "err": "✗", "info": "ℹ", "tx": "→", "rx": "←"}.get(level, "?")
                print(f"[{prefix}] {msg}")
            except queue.Empty:
                pass


def main():
    parser = argparse.ArgumentParser(description="Robot Controller")
    parser.add_argument("--port", default="/dev/ttyUSB0", help="Serial port")
    parser.add_argument("--json", default="actions.json", help="Action JSON file")
    parser.add_argument("--gpio", action="store_true", help="Enable GPIO triggers")
    parser.add_argument("--http", action="store_true", help="Enable HTTP API")
    parser.add_argument("--http-port", type=int, default=8080, help="HTTP port")
    args = parser.parse_args()

    ctrl = RobotController(args.port, args.json)

    print(f"Connecting to {args.port}...")
    ctrl.connect()
    print("Connected!")

    threading.Thread(target=ctrl.log_listener, daemon=True).start()

    if args.gpio and GPIO_AVAILABLE:
        setup_gpio(ctrl)

    if args.http:
        start_http_server(ctrl, args.http_port)

    if Path(args.json).exists():
        sequences = ctrl.load_actions(args.json)
        print(f"Loaded {len(sequences)} sequences:")
        for i, seq in enumerate(sequences):
            print(f"  [{i}] {seq.name} ({seq.duration_ms()}ms, {len(seq.frames)} frames)")

    print("\nRobot Controller Ready!")
    print("Commands:")
    print("  play <id>   - Play sequence by index")
    print("  stop        - Stop playback")
    print("  list        - List loaded sequences")
    print("  gpio <id>   - Trigger sequence via GPIO")
    print("  quit        - Exit")
    print()

    try:
        while True:
            cmd = input("> ").strip()
            if not cmd:
                continue

            parts = cmd.split()
            action = parts[0]

            if action == "quit":
                break
            elif action == "list":
                if 'sequences' in dir():
                    for i, seq in enumerate(sequences):
                        print(f"  [{i}] {seq.name}")
            elif action == "stop":
                ctrl.stop()
                print("Stopped")
            elif action == "play" and len(parts) > 1:
                idx = int(parts[1])
                if 'sequences' in dir() and 0 <= idx < len(sequences):
                    print(f"Playing: {sequences[idx].name}")
                    threading.Thread(target=ctrl.play_sequence, args=(sequences[idx],)).start()
            elif action == "gpio" and len(parts) > 1:
                idx = int(parts[1])
                if 'sequences' in dir() and 0 <= idx < len(sequences):
                    print(f"GPIO triggered: {sequences[idx].name}")
                    threading.Thread(target=ctrl.play_sequence, args=(sequences[idx],)).start()
            else:
                print("Unknown command")
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        ctrl.disconnect()


def setup_gpio(ctrl: RobotController):
    if not GPIO_AVAILABLE:
        print("GPIO not available (not on RPi?)")
        return

    GPIO.setmode(GPIO.BCM)
    TRIGGER_PINS = {17: 0, 27: 1, 22: 2}  # GPIO pin -> sequence index

    for pin in TRIGGER_PINS:
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def callback(channel):
        idx = TRIGGER_PINS.get(channel)
        if 'sequences' in dir() and idx is not None:
            print(f"GPIO {channel} triggered: playing sequence {idx}")
            threading.Thread(target=ctrl.play_sequence, args=(sequences[idx],)).start()

    for pin in TRIGGER_PINS:
        GPIO.add_event_detect(pin, GPIO.RISING, callback=callback)

    print(f"GPIO triggers enabled on pins: {list(TRIGGER_PINS.keys())}")


def start_http_server(ctrl: RobotController, port: int):
    try:
        from flask import Flask, jsonify
        app = Flask(__name__)

        @app.route("/play/<int:idx>", methods=["GET"])
        def play(idx):
            if 'sequences' in dir() and 0 <= idx < len(sequences):
                threading.Thread(target=ctrl.play_sequence, args=(sequences[idx],)).start()
                return jsonify({"status": "playing", "sequence": sequences[idx].name})
            return jsonify({"error": "invalid index"}), 400

        @app.route("/stop", methods=["GET"])
        def stop():
            ctrl.stop()
            return jsonify({"status": "stopped"})

        @app.route("/sequences", methods=["GET"])
        def list_sequences():
            if 'sequences' in dir():
                return jsonify([{"id": i, "name": s.name, "duration_ms": s.duration_ms()}
                                for i, s in enumerate(sequences)])
            return jsonify([])

        threading.Thread(target=lambda: app.run(host="0.0.0.0", port=port),
                       daemon=True).start()
        print(f"HTTP API enabled on port {port}")
    except ImportError:
        print("Flask not installed, HTTP API disabled. Install with: pip install flask")


if __name__ == "__main__":
    main()
