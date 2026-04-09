/**
 * Protocol.cpp — 串口协议层实现
 *
 * 数据包格式（5字节定长）:
 *   [0] 0xAA  帧头
 *   [1] CMD   命令字节
 *   [2] VAL   参数字节
 *   [3] CSUM  校验和 = CMD ^ VAL
 *   [4] 0x55  帧尾
 */

#include "Protocol.h"

namespace Protocol {

// ─── 内部状态 ─────────────────────────────────────────────────
static uint8_t            s_buf[PACKET_LEN];
static uint8_t            s_idx = 0;

static OnSetExpressionFn  s_onExpression = nullptr;
static OnSetRobotStateFn  s_onRobotState  = nullptr;
static OnSetAutoModeFn    s_onAutoMode    = nullptr;
static OnSetServoFn       s_onServo      = nullptr;

// ─── 公开 API ─────────────────────────────────────────────────

void setCallbacks(
  OnSetExpressionFn  onExpression,
  OnSetRobotStateFn  onRobotState,
  OnSetAutoModeFn    onAutoMode,
  OnSetServoFn       onServo
) {
  s_onExpression = onExpression;
  s_onRobotState  = onRobotState;
  s_onAutoMode    = onAutoMode;
  s_onServo      = onServo;
}

void begin() {
  Serial.begin(SERIAL_BAUD);
}

void sendAck(uint8_t command, uint8_t status) {
  const uint8_t checksum    = command ^ status;
  const uint8_t response[5] = { PACKET_HEAD, command, status, checksum, PACKET_TAIL };
  Serial.write(response, sizeof(response));
}

// ─── 内部：处理一个完整数据包 ────────────────────────────────
static void handlePacket(unsigned long now) {
  const uint8_t command  = s_buf[1];
  const uint8_t value    = s_buf[2];
  const uint8_t checksum = s_buf[3];

  // 校验和检查
  if ((command ^ value) != checksum) {
    sendAck(command, ACK_BAD_PACKET);
    return;
  }

  switch (command) {

    case CMD_SET_EXPRESSION:
      if (s_onExpression) {
        s_onExpression(static_cast<ExpressionId>(value));
        sendAck(command, ACK_OK);
      } else {
        sendAck(command, ACK_BAD_COMMAND);
      }
      break;

    case CMD_SET_AUTO_MODE:
      if (s_onAutoMode) {
        s_onAutoMode();
        sendAck(command, ACK_OK);
      } else {
        sendAck(command, ACK_BAD_COMMAND);
      }
      break;

    case CMD_SET_ROBOT_STATE:
      if (s_onRobotState) {
        s_onRobotState(static_cast<RobotStateId>(value));
        sendAck(command, ACK_OK);
      } else {
        sendAck(command, ACK_BAD_COMMAND);
      }
      break;

    case CMD_SET_SERVO:
      if (s_onServo) {
        uint8_t tiltIndex = (value >> 4) & 0x0F;
        uint8_t panIndex = value & 0x0F;
        s_onServo(tiltIndex, panIndex);
        sendAck(command, ACK_OK);
      } else {
        sendAck(command, ACK_BAD_COMMAND);
      }
      break;

    default:
      sendAck(command, ACK_BAD_COMMAND);
      break;
  }
}

void update(unsigned long /*now*/) {
  while (Serial.available() > 0) {
    const uint8_t byte = static_cast<uint8_t>(Serial.read());

    // 等待帧头
    if (s_idx == 0) {
      if (byte == PACKET_HEAD) {
        s_buf[s_idx++] = byte;
      }
      continue;
    }

    s_buf[s_idx++] = byte;

    if (s_idx < PACKET_LEN) {
      continue;  // 包未收完，继续等待
    }

    // 包已满
    if (s_buf[PACKET_LEN - 1] == PACKET_TAIL) {
      handlePacket(millis());
    } else {
      sendAck(s_buf[1], ACK_BAD_PACKET);
    }
    s_idx = 0;
  }
}

} // namespace Protocol
