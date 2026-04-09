"""
face_greeting.py - 人脸识别智能迎宾

功能:
  - 主人靠近 → 机器人显示开心表情 (HAPPY)
  - 陌生人出现 → 保持普通表情 (NORMAL)

RDK X5 部署:
  pip install face_recognition opencv-python numpy pyserial
  python face_greeting.py --port /dev/ttyUSB0 --camera 0 --headless

依赖:
  pip install face_recognition opencv-python numpy pyserial
"""
import argparse
import os
import sys
import time
import queue
import threading
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from robot_protocol import (
    SerialWorker, EXPRESSIONS, CMD_SET_EXPRESSION,
    build_packet,
)

FRAME_WIDTH = 640
FRAME_HEIGHT = 480
TOLERANCE = 0.45

DB_PATH = Path(__file__).parent.parent / "face_recognition_demo" / "face_db.json"

try:
    import face_recognition as fr
except ImportError:
    print("请先安装: pip install face_recognition opencv-python numpy")
    sys.exit(1)


class FaceDB:
    def __init__(self):
        self._data: dict[str, list[np.ndarray]] = {}
        self._lock = threading.Lock()
        self._load()

    def _load(self):
        if not DB_PATH.exists():
            print(f"人脸库文件不存在: {DB_PATH}")
            return
        raw = __import__('json').loads(DB_PATH.read_text(encoding="utf-8"))
        for name, encs in raw.get("persons", {}).items():
            self._data[name] = [np.array(e) for e in encs]
        print(f"人脸库: {len(self._data)} 人，{sum(len(v) for v in self._data.values())} 条编码")

    def all_encodings(self):
        with self._lock:
            encs, names = [], []
            for name, enc_list in self._data.items():
                for enc in enc_list:
                    encs.append(enc)
                    names.append(name)
            return encs, names

    def __len__(self):
        with self._lock:
            return len(self._data)


class FaceEngine:
    def __init__(self, db: FaceDB):
        self.db = db

    def encode_frame(self, rgb):
        locations = fr.face_locations(rgb, model="hog")
        encodings = fr.face_encodings(rgb, locations)
        return list(zip(locations, encodings))

    def recognize(self, encoding):
        known_encs, known_names = self.db.all_encodings()
        if not known_encs:
            return None, 1.0
        distances = fr.face_distance(known_encs, encoding)
        best_idx = int(np.argmin(distances))
        best_dist = float(distances[best_idx])
        if best_dist < TOLERANCE:
            return known_names[best_idx], best_dist
        return None, best_dist


class RobotFaceController:
    def __init__(self, port: str):
        self.port = port
        self.log_q: queue.Queue = queue.Queue()
        self.worker: SerialWorker | None = None
        self.current_expr = "NORMAL"
        self._running = True

    def connect(self) -> bool:
        try:
            self.worker = SerialWorker(self.port, self.log_q)
            self.worker.start()
            time.sleep(2)
            self._send_expression("NORMAL")
            threading.Thread(target=self._log_listener, daemon=True).start()
            return True
        except Exception as e:
            print(f"连接机器人失败: {e}")
            return False

    def disconnect(self):
        self._running = False
        if self.worker:
            self.worker.stop()
            self.worker.join(timeout=2)

    def _send_expression(self, name: str) -> bool:
        if self.worker is None:
            return False
        if name in EXPRESSIONS:
            val = EXPRESSIONS[name]
            self.worker.send_raw(build_packet(CMD_SET_EXPRESSION, val))
            return True
        return False

    def set_happy(self) -> bool:
        if self.current_expr != "HAPPY":
            result = self._send_expression("HAPPY")
            if result:
                self.current_expr = "HAPPY"
                print(f"[表情] HAPPY")
            return result
        return True

    def set_normal(self) -> bool:
        if self.current_expr != "NORMAL":
            result = self._send_expression("NORMAL")
            if result:
                self.current_expr = "NORMAL"
                print(f"[表情] NORMAL")
            return result
        return True

    def is_connected(self) -> bool:
        return self.worker is not None

    def _log_listener(self):
        while self._running:
            try:
                level, msg = self.log_q.get(timeout=0.5)
                prefix = {"ok": "✓", "err": "✗", "info": "ℹ", "tx": "→"}.get(level, "?")
                print(f"[{prefix}] {msg}")
            except queue.Empty:
                pass


def open_camera(idx=0, headless=False):
    if headless:
        print("headless模式: 跳过摄像头初始化")
        return None
        
    backends = [cv2.CAP_V4L2, cv2.CAP_V4L, cv2.CAP_ANY, cv2.CAP_DSHOW]
    names = {cv2.CAP_V4L2: "V4L2", cv2.CAP_V4L: "V4L", cv2.CAP_ANY: "ANY", cv2.CAP_DSHOW: "DSHOW"}
    
    for backend in backends:
        cap = cv2.VideoCapture(idx, backend)
        if cap.isOpened():
            print(f"摄像头已打开 (backend: {names.get(backend, backend)})")
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
            return cap
        cap.release()
    raise RuntimeError("找不到可用摄像头")


def has_display() -> bool:
    return os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")


def main():
    parser = argparse.ArgumentParser(description="人脸识别智能迎宾 (RDK X5)")
    parser.add_argument("--port", default="/dev/ttyUSB0", help="机器人串口")
    parser.add_argument("--camera", type=int, default=0, help="摄像头索引")
    parser.add_argument("--tolerance", type=float, default=0.45, help="识别阈值 (0.0-1.0)")
    parser.add_argument("--happy-duration", type=int, default=5, help="保持开心秒数")
    parser.add_argument("--headless", action="store_true", help="无屏幕模式")
    parser.add_argument("--no-robot", action="store_true", help="不连接机器人")
    args = parser.parse_args()

    global TOLERANCE
    TOLERANCE = args.tolerance

    headless = args.headless or not has_display()

    print(f"""
╔════════════════════════════════════════╗
║  人脸识别智能迎宾 v1.2 (RDK X5)    ║
║  主人靠近 → 开心表情                ║
║  陌生人 → 普通表情                   ║
╠════════════════════════════════════════╣
║  阈值: {args.tolerance}  持续: {args.happy_duration}秒  模式: {'headless' if headless else 'display'}   ║
╚════════════════════════════════════════╝
    """)

    db = FaceDB()
    if len(db) == 0:
        print("警告: 人脸库为空")

    engine = FaceEngine(db)
    robot = RobotFaceController(args.port)
    robot_connected = False

    if not args.no_robot:
        robot_connected = robot.connect()
        if robot_connected:
            print("机器人已连接")
        else:
            print("机器人未连接，将仅检测人脸")

    cap = open_camera(args.camera, headless)
    
    if headless:
        print("运行中 (Ctrl+C 退出)...\n")
    else:
        print()

    tick = 0
    last_happy_time = 0
    last_log_time = 0
    HAPPY_DURATION = args.happy_duration
    LOG_INTERVAL = 1.0

    frame_count = 0

    try:
        while True:
            if cap is None:
                time.sleep(0.1)
                frame_count += 1
                if frame_count % 100 == 0:
                    print(".")
                continue
                
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.1)
                continue

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            frame_count += 1
            if frame_count % 6 != 0:
                if not headless:
                    cv2.imshow("Face Greeting", frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                continue

            faces = engine.encode_frame(rgb)

            any_owner = False
            for loc, enc in faces:
                name, dist = engine.recognize(enc)
                top, right, bottom, left = loc
                
                if name:
                    any_owner = True
                    if not headless:
                        cv2.rectangle(frame, (left, top), (right, bottom), (50, 220, 100), 2)
                        cv2.putText(frame, f"{name} ({dist:.2f})", (left, top - 10),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (50, 220, 100), 2)
                    if time.time() - last_log_time > LOG_INTERVAL:
                        print(f"检测到: {name} (距离: {dist:.3f})")
                else:
                    if not headless:
                        cv2.rectangle(frame, (left, top), (right, bottom), (40, 60, 220), 2)
                        cv2.putText(frame, f"陌生人 ({dist:.2f})", (left, top - 10),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (40, 60, 220), 2)

            if any_owner:
                robot.set_happy()
                last_happy_time = time.time()
                last_log_time = time.time()
            elif time.time() - last_happy_time > HAPPY_DURATION:
                robot.set_normal()

            if not headless:
                expr_color = (0, 255, 0) if robot.current_expr == "HAPPY" else (150, 150, 150)
                cv2.putText(frame, f"表情: {robot.current_expr}", 
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, expr_color, 2)
                cv2.putText(frame, f"已注册: {len(db)} 人", 
                            (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
                status = "● 已连接" if robot_connected else "○ 未连接"
                cv2.putText(frame, status, 
                            (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, 
                            (0, 255, 0) if robot_connected else (0, 0, 255), 1)
                cv2.imshow("Face Greeting", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

    except KeyboardInterrupt:
        print("\n收到退出信号")
    finally:
        if cap:
            cap.release()
        if not headless:
            cv2.destroyAllWindows()
        robot.disconnect()
        print("已退出")


if __name__ == "__main__":
    main()