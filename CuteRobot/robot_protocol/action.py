"""
动作序列数据结构 - 关键帧 + 动作序列
"""

from .constants import SERVO1_MIN, SERVO1_MAX, SERVO2_MIN, SERVO2_MAX
from .protocol import encode_servo
from .constants import CMD_SET_EXPRESSION, EXPRESSIONS


class Keyframe:
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
        self.expr = expr
        self.easing = easing

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


def lerp_angle(a: int, b: int, t: float, easing: str) -> float:
    if easing == "ease_in":
        t = t * t
    elif easing == "ease_out":
        t = t * (2 - t)
    elif easing == "ease_in_out":
        t = 2 * t * t if t < 0.5 else -1 + (4 - 2 * t) * t
    return a + (b - a) * t


class ActionSequence:
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
        if not self.frames:
            return
        self.frames = [f for f in self.frames if f.t_ms >= keep_from_ms]
        if self.frames:
            self.frames[0].t_ms = 0

    def trim_end(self, keep_until_ms: int):
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

    def build_playback_packets(self, interval_ms=20):
        from .protocol import build_packet, encode_servo
        from .constants import CMD_SET_SERVO

        packets: list[tuple[int, bytes]] = []
        if len(self.frames) < 1:
            return packets

        for i, kf in enumerate(self.frames):
            if kf.expr and kf.expr in EXPRESSIONS:
                packets.append(
                    (kf.t_ms, build_packet(CMD_SET_EXPRESSION, EXPRESSIONS[kf.expr]))
                )

            if i < len(self.frames) - 1:
                kf_next = self.frames[i + 1]
                seg_dur = kf_next.t_ms - kf.t_ms
                steps = max(1, seg_dur // interval_ms)
                for s in range(steps):
                    t = s / steps
                    tilt = lerp_angle(kf.tilt, kf_next.tilt, t, kf_next.easing)
                    pan = lerp_angle(kf.pan, kf_next.pan, t, kf_next.easing)
                    abs_t = kf.t_ms + s * interval_ms
                    val = encode_servo(int(tilt), int(pan))
                    packets.append((abs_t, build_packet(CMD_SET_SERVO, val)))

        last = self.frames[-1]
        packets.append(
            (last.t_ms, build_packet(CMD_SET_SERVO, encode_servo(last.tilt, last.pan)))
        )

        packets.sort(key=lambda p: p[0])
        return packets
