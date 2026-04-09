/**
 * CuteEyeRobot.ino — 主文件（胶水层）
 *
 * 架构说明:
 *   ┌─────────────────────────────────────────────────────┐
 *   │                 上位机 (PC / 蓝牙模块)               │
 *   │   串口指令: [AA] [CMD] [VAL] [CSUM] [55]            │
 *   └────────────────────┬────────────────────────────────┘
 *                        │ UART
 *   ┌────────────────────▼────────────────────────────────┐
 *   │  Protocol.h   — 收包 / 校验 / ACK / 回调分发        │
 *   └──────┬────────────────────────┬───────────────────  ┘
 *          │                        │
 *   ┌──────▼──────────┐    ┌────────▼────────────────────┐
 *   │  EyeDisplay.h   │    │  ServoController.h           │
 *   │  OLED 表情动画   │    │  舵机1(俯仰) + 舵机2(偏航)   │
 *   └─────────────────┘    └─────────────────────────────┘
 *
 * 串口命令速查:
 *   CMD_SET_EXPRESSION (0x01) + ExpressionId  → 单独切换眼睛表情
 *   CMD_SET_AUTO_MODE  (0x02)                 → 眼睛进入自动模式
 *   CMD_SET_ROBOT_STATE(0x04) + RobotStateId  → 同时控制眼睛+舵机
 *
 * 示例帧（小机器人开心，RS_HAPPY=1）:
 *   AA 04 01 05 55
 *        ↑  ↑  ↑
 *   CMD  VAL CSUM=CMD^VAL
 */

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#include "RobotState.h"
#include "Protocol.h"
#include "EyeDisplay.h"
#include "ServoController.h"

// ─── 屏幕实例（主文件持有，传指针给 EyeDisplay）────────────────
static Adafruit_SSD1306 display(128, 64, &Wire, -1);

// ─── 协议回调实现 ─────────────────────────────────────────────

/** CMD_SET_EXPRESSION：只控制眼睛 */
static void onSetExpression(ExpressionId id) {
  EyeDisplay::setExpression(id, millis());
}

/**
 * CMD_SET_ROBOT_STATE：同时控制眼睛 + 舵机
 * 在这里定义"情绪 → 眼睛表情"的映射关系
 */
static void onSetRobotState(RobotStateId state) {
  unsigned long now = millis();
  ServoController::setState(state, now);

  switch (state) {
    case RS_IDLE:      EyeDisplay::setExpression(E_NORMAL,    now); break;
    case RS_HAPPY:     EyeDisplay::setExpression(E_HAPPY,     now); break;
    case RS_SAD:       EyeDisplay::setExpression(E_SAD,       now); break;
    case RS_ANGRY:     EyeDisplay::setExpression(E_ANGRY,     now); break;
    case RS_SLEEPY:    EyeDisplay::setExpression(E_SLEEPY,    now); break;
    case RS_SURPRISED: EyeDisplay::setExpression(E_SURPRISED, now); break;
    case RS_EXCITED:   EyeDisplay::setExpression(E_EXCITED,   now); break;
    case RS_WORRIED:   EyeDisplay::setExpression(E_WORRIED,   now); break;
  }
}

/** CMD_SET_AUTO_MODE：只控制眼睛，舵机归中 */
static void onSetAutoMode() {
  unsigned long now = millis();
  EyeDisplay::setAutoMode(now);
  ServoController::setState(RS_IDLE, now);
}

/** CMD_SET_SERVO：直接设置舵机角度（tiltIndex, panIndex 各 0-8） */
static void onSetServo(uint8_t tiltIndex, uint8_t panIndex) {
  uint8_t tilt = SERVO1_MIN + tiltIndex * (SERVO1_MAX - SERVO1_MIN) / 8;
  uint8_t pan = SERVO2_MIN + panIndex * (SERVO2_MAX - SERVO2_MIN) / 8;
  ServoController::setTarget(tilt, pan);
}

// ─── setup / loop ─────────────────────────────────────────────

void setup() {
  // 1. 注册回调（必须在 Protocol::begin() 之前）
  Protocol::setCallbacks(onSetExpression, onSetRobotState, onSetAutoMode, onSetServo);
  Protocol::begin();

  // 2. 初始化屏幕
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    while (true) { }  // 屏幕初始化失败则死机
  }
  EyeDisplay::begin(display);

  // 3. 初始化舵机（如不需要舵机可注释此行）
  ServoController::begin();
}

void loop() {
  unsigned long now = millis();

  Protocol::update(now);         // 收串口包 → 触发回调
  EyeDisplay::update(now);       // 推进眼睛动画帧
  ServoController::update(now);  // 推进舵机缓动/往复
}
