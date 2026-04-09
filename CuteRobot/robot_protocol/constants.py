"""
常量定义 - 与 Arduino 固件协议一致
"""

from enum import IntEnum

BAUD_RATE = 115200
PACKET_HEAD = 0xAA
PACKET_TAIL = 0x55

CMD_SET_EXPRESSION = 0x01
CMD_SET_AUTO_MODE = 0x02
CMD_SET_SERVO = 0x03
CMD_SET_ROBOT_STATE = 0x04

ACK_OK = 0x00
ACK_BAD_PACKET = 0xE1
ACK_BAD_COMMAND = 0xE2
ACK_BAD_PARAM = 0xE3

SERVO1_MIN = 50
SERVO1_MID = 90
SERVO1_MAX = 130

SERVO2_MIN = 45
SERVO2_MID = 90
SERVO2_MAX = 135

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

ACK_LABEL = {
    ACK_OK: "OK",
    ACK_BAD_PACKET: "BAD_PACKET",
    ACK_BAD_COMMAND: "BAD_CMD",
    ACK_BAD_PARAM: "BAD_PARAM",
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
    "IDLE": "😀",
    "HAPPY": "😊",
    "SAD": "😢",
    "ANGRY": "😠",
    "SLEEPY": "😴",
    "SURPRISED": "😲",
    "EXCITED": "🤩",
    "WORRIED": "😟",
}

EASINGS = [
    "linear",
    "ease_in",
    "ease_out",
    "ease_in_out",
]
