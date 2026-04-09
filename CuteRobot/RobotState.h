#pragma once
#include <stdint.h>

// ─── 屏幕尺寸 ────────────────────────────────────────────────
constexpr uint8_t  SCREEN_W      = 128;
constexpr uint8_t  SCREEN_H      = 64;
constexpr int8_t   EYE_OFFSET_Y  = 10;

// ─── 串口协议常量 ─────────────────────────────────────────────
constexpr unsigned long SERIAL_BAUD       = 115200;
constexpr uint8_t       PACKET_HEAD       = 0xAA;
constexpr uint8_t       PACKET_TAIL       = 0x55;
constexpr uint8_t       PACKET_LEN        = 5;   // AA CMD VAL CSUM 55

// 命令字节
constexpr uint8_t CMD_SET_EXPRESSION = 0x01;
constexpr uint8_t CMD_SET_AUTO_MODE  = 0x02;
constexpr uint8_t CMD_SET_SERVO      = 0x03;   // 预留：直接控舵机角度
constexpr uint8_t CMD_SET_ROBOT_STATE= 0x04;   // 预留：机器人整体状态

// ACK 状态码
constexpr uint8_t ACK_OK          = 0x00;
constexpr uint8_t ACK_BAD_PACKET  = 0xE1;
constexpr uint8_t ACK_BAD_COMMAND = 0xE2;
constexpr uint8_t ACK_BAD_PARAM   = 0xE3;

// ─── 表情 ID ──────────────────────────────────────────────────
enum ExpressionId : uint8_t {
  E_ALERT        = 0,
  E_ANGRY        = 1,
  E_BLINK_DOWN   = 2,
  E_BLINK_UP     = 3,
  E_BLINK        = 4,
  E_BORED        = 5,
  E_DESPAIR      = 6,
  E_DISORIENTED  = 7,
  E_EXCITED      = 8,
  E_FOCUSED      = 9,
  E_FURIOUS      = 10,
  E_HAPPY        = 11,
  E_LOOK_DOWN    = 12,
  E_LOOK_LEFT    = 13,
  E_LOOK_RIGHT   = 14,
  E_LOOK_UP      = 15,
  E_NORMAL       = 16,
  E_SAD          = 17,
  E_SCARED       = 18,
  E_SLEEPY       = 19,
  E_SURPRISED    = 20,
  E_WINK_LEFT    = 21,
  E_WINK_RIGHT   = 22,
  E_WORRIED      = 23,
  E_BATTERY_FULL = 24,
  E_BATTERY_LOW  = 25,
  E_BATTERY      = 26,
  E_LEFT_SIGNAL  = 27,
  E_LOGO         = 28,
  E_MODE         = 29,
  E_RIGHT_SIGNAL = 30,
  E_WARNING      = 31
};

// ─── 机器人整体情绪状态（供上位机用 CMD_SET_ROBOT_STATE 控制）─
enum RobotStateId : uint8_t {
  RS_IDLE     = 0,   // 待机：普通眼神 + 舵机居中
  RS_HAPPY    = 1,   // 开心：笑眼   + 舵机大幅摆动(兴奋)
  RS_SAD      = 2,   // 悲伤：哭眼   + 舵机轻微低垂
  RS_ANGRY    = 3,   // 愤怒：怒眼   + 舵机快速点头
  RS_SLEEPY   = 4,   // 困倦：睡眼   + 舵机缓慢垂头
  RS_SURPRISED= 5,   // 惊讶：大眼   + 舵机抬头仰望
  RS_EXCITED  = 6,   // 兴奋：兴奋眼 + 舵机高频摆动
  RS_WORRIED  = 7,   // 担心：愁眼   + 舵机左右扫视
};
