"""
协议编解码 - 封装 packet 构建、舵机角度编码
"""

import struct
from .constants import (
    PACKET_HEAD,
    PACKET_TAIL,
    CMD_SET_EXPRESSION,
    CMD_SET_AUTO_MODE,
    CMD_SET_SERVO,
    CMD_SET_ROBOT_STATE,
    SERVO1_MIN,
    SERVO1_MAX,
    SERVO2_MIN,
    SERVO2_MAX,
)


def build_packet(cmd: int, val: int = 0) -> bytes:
    return struct.pack(
        "5B",
        PACKET_HEAD,
        cmd,
        val & 0xFF,
        cmd ^ (val & 0xFF),
        PACKET_TAIL,
    )


def encode_servo(tilt: int, pan: int) -> int:
    ti = round((tilt - SERVO1_MIN) / (SERVO1_MAX - SERVO1_MIN) * 8)
    pi = round((pan - SERVO2_MIN) / (SERVO2_MAX - SERVO2_MIN) * 8)
    return (max(0, min(8, ti)) << 4) | max(0, min(8, pi))


def decode_servo(val: int) -> tuple[int, int]:
    ti = (val >> 4) & 0x0F
    pi = val & 0x0F
    return (
        SERVO1_MIN + ti * (SERVO1_MAX - SERVO1_MIN) // 8,
        SERVO2_MIN + pi * (SERVO2_MAX - SERVO2_MIN) // 8,
    )


def parse_ack(buf: bytes) -> tuple[int, int] | None:
    for i in range(len(buf) - 4):
        if buf[i] == PACKET_HEAD and buf[i + 4] == PACKET_TAIL:
            c, s, cs = buf[i + 1], buf[i + 2], buf[i + 3]
            if (c ^ s) == cs:
                return c, s
    return None
