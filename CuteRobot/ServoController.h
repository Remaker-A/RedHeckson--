#pragma once
/**
 * ServoController.h — 舵机外设层
 *
 * 硬件:
 *   舵机1 (SERVO1_PIN) — 控制脖子竖直探出 (俯仰 / Tilt)
 *   舵机2 (SERVO2_PIN) — 控制左右摇头     (偏航 / Pan)
 *
 * 职责:
 *   - 封装 Servo 库和角度映射
 *   - 提供 setState(RobotStateId) 接口：每种情绪状态映射到一组舵机动作
 *   - update() 内部执行非阻塞缓动/往复动画
 *   - 方便后续添加更多舵机/外设，只需在此文件扩展
 */

#include <Arduino.h>
#include "RobotState.h"

// ─── 引脚配置（按需修改） ─────────────────────────────────────
constexpr uint8_t SERVO1_PIN = 5;   // 俯仰舵机
constexpr uint8_t SERVO2_PIN = 6;  // 偏航舵机

// ─── 角度限位 ─────────────────────────────────────────────────
constexpr uint8_t SERVO1_MIN = 50;   // 低头极限
constexpr uint8_t SERVO1_MID = 90;   // 居中（直立）
constexpr uint8_t SERVO1_MAX = 130;  // 抬头极限

constexpr uint8_t SERVO2_MIN = 45;   // 左转极限
constexpr uint8_t SERVO2_MID = 90;   // 居中（正前方）
constexpr uint8_t SERVO2_MAX = 135;  // 右转极限

namespace ServoController {

  /** 初始化舵机，归位到中立位置 */
  void begin();

  /** 放入 loop() 中轮询（执行缓动/往复动画） */
  void update(unsigned long now);

  /**
   * 根据机器人整体状态设置舵机动作模式
   *
   * RS_IDLE      → 归中，静止
   * RS_HAPPY     → 左右大幅快速往复（兴奋摆动）
   * RS_SAD       → 缓慢垂头（俯仰低，偏航居中，不动）
   * RS_ANGRY     → 快速小幅点头（俯仰往复）
   * RS_SLEEPY    → 极缓慢低垂，轻微摆动
   * RS_SURPRISED → 快速抬头，偏航轻微摆动
   * RS_EXCITED   → 高频左右+俯仰组合往复
   * RS_WORRIED   → 缓慢左右扫视
   */
  void setState(RobotStateId state, unsigned long now);

  /** 直接设置两轴目标角度（供调试或其他模块调用） */
  void setTarget(uint8_t tilt, uint8_t pan);

} // namespace ServoController
