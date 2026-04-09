"""
robot_protocol - CuteRobot 串口协议库

用法:
    from robot_protocol import SerialWorker, ActionSequence, encode_servo

    worker = SerialWorker("COM6", log_q)
    worker.start()

    worker.send_raw(encode_servo(90, 90))  # 发送舵机角度
    worker.stop()
"""

from .constants import (
    BAUD_RATE,
    PACKET_HEAD,
    PACKET_TAIL,
    CMD_SET_EXPRESSION,
    CMD_SET_AUTO_MODE,
    CMD_SET_SERVO,
    CMD_SET_ROBOT_STATE,
    ACK_OK,
    ACK_BAD_PACKET,
    ACK_BAD_COMMAND,
    ACK_BAD_PARAM,
    SERVO1_MIN,
    SERVO1_MID,
    SERVO1_MAX,
    SERVO2_MIN,
    SERVO2_MID,
    SERVO2_MAX,
    EXPRESSIONS,
    ACK_LABEL,
    ROBOT_STATES,
    STATE_EMOJI,
    EASINGS,
)
from .protocol import build_packet, encode_servo, decode_servo, parse_ack
from .serial_worker import SerialWorker
from .playback import PlaybackEngine
from .action import ActionSequence, Keyframe, lerp_angle

__all__ = [
    "BAUD_RATE",
    "PACKET_HEAD",
    "PACKET_TAIL",
    "CMD_SET_EXPRESSION",
    "CMD_SET_AUTO_MODE",
    "CMD_SET_SERVO",
    "CMD_SET_ROBOT_STATE",
    "ACK_OK",
    "ACK_BAD_PACKET",
    "ACK_BAD_COMMAND",
    "ACK_BAD_PARAM",
    "SERVO1_MIN",
    "SERVO1_MID",
    "SERVO1_MAX",
    "SERVO2_MIN",
    "SERVO2_MID",
    "SERVO2_MAX",
    "EXPRESSIONS",
    "ACK_LABEL",
    "ROBOT_STATES",
    "STATE_EMOJI",
    "EASINGS",
    "build_packet",
    "encode_servo",
    "decode_servo",
    "parse_ack",
    "SerialWorker",
    "PlaybackEngine",
    "ActionSequence",
    "Keyframe",
    "lerp_angle",
]
