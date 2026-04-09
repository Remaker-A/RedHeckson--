/**
 * ServoController.cpp — 舵机外设层实现
 *
 * 动画引擎：非阻塞缓动 + 往复（Sweep）模式
 *   每次 update() 按 EASE_STEP 度逼近目标角度；
 *   Sweep 模式下目标角度在 sweepMin / sweepMax 间来回切换。
 */

#include "ServoController.h"
#include <Servo.h>

namespace ServoController {

// ─── Servo 对象 ───────────────────────────────────────────────
static Servo s_tilt; // 舵机1：俯仰
static Servo s_pan;  // 舵机2：偏航

// ─── 单轴运动描述符 ───────────────────────────────────────────
struct AxisState {
  int32_t current_milliDeg; // 当前角度 * 1000
  int32_t target_milliDeg;  // 目标角度 * 1000
  int32_t easeSpeed_MDpMs;  // 每毫秒移动度数 * 1000
  bool sweep;               // 是否往复模式
  int32_t sweepMin_milliDeg;
  int32_t sweepMax_milliDeg;
  unsigned long lastTick;
};

static AxisState s_tiltAxis;
static AxisState s_panAxis;

// ─── 内部工具 ─────────────────────────────────────────────────
static void initAxis(AxisState &ax, uint8_t startAngle) {
  ax.current_milliDeg = (int32_t)startAngle * 1000;
  ax.target_milliDeg = (int32_t)startAngle * 1000;
  ax.easeSpeed_MDpMs = 100; // 默认 0.1°/ms (100 millidegrees)
  ax.sweep = false;
  ax.sweepMin_milliDeg = (int32_t)startAngle * 1000;
  ax.sweepMax_milliDeg = (int32_t)startAngle * 1000;
  ax.lastTick = millis();
}

static void setSweep(AxisState &ax, uint8_t minA, uint8_t maxA,
                     int32_t speedMD) {
  ax.sweep = true;
  ax.sweepMin_milliDeg = (int32_t)minA * 1000;
  ax.sweepMax_milliDeg = (int32_t)maxA * 1000;
  ax.easeSpeed_MDpMs = speedMD;

  int32_t mid = (ax.sweepMin_milliDeg + ax.sweepMax_milliDeg) / 2;
  ax.target_milliDeg =
      (ax.current_milliDeg < mid) ? ax.sweepMax_milliDeg : ax.sweepMin_milliDeg;
}

static void setStill(AxisState &ax, uint8_t angle, int32_t speedMD) {
  ax.sweep = false;
  ax.target_milliDeg = (int32_t)angle * 1000;
  ax.easeSpeed_MDpMs = speedMD;
}

/** 更新单轴，返回当前角度（四舍五入到整数度） */
static uint8_t tickAxis(AxisState &ax, unsigned long now) {
  unsigned long dt = now - ax.lastTick;
  ax.lastTick = now;

  int32_t step = ax.easeSpeed_MDpMs * (int32_t)dt;
  int32_t diff = ax.target_milliDeg - ax.current_milliDeg;
  int32_t abs_diff = (diff < 0) ? -diff : diff;

  if (abs_diff <= step) {
    ax.current_milliDeg = ax.target_milliDeg;
    // 往复：到达目标后翻转
    if (ax.sweep) {
      ax.target_milliDeg = (ax.target_milliDeg == ax.sweepMax_milliDeg)
                               ? ax.sweepMin_milliDeg
                               : ax.sweepMax_milliDeg;
    }
  } else {
    ax.current_milliDeg += (diff > 0) ? step : -step;
  }

  // 四舍五入到整数度 (加500再除以1000)
  return (uint8_t)((ax.current_milliDeg + 500) / 1000);
}

// ─── 公开 API ─────────────────────────────────────────────────

void begin() {
  s_tilt.attach(SERVO1_PIN);
  s_pan.attach(SERVO2_PIN);

  initAxis(s_tiltAxis, SERVO1_MID);
  initAxis(s_panAxis, SERVO2_MID);

  s_tilt.write(SERVO1_MID);
  s_pan.write(SERVO2_MID);
}

void setTarget(uint8_t tilt, uint8_t pan) {
  setStill(s_tiltAxis, tilt, 150); // 0.15 * 1000 = 150
  setStill(s_panAxis, pan, 150);
}

void setState(RobotStateId state, unsigned long now) {
  s_tiltAxis.lastTick = now;
  s_panAxis.lastTick = now;

  switch (state) {

  case RS_IDLE:
    // 归中，静止
    setStill(s_tiltAxis, SERVO1_MID, 80); // 0.08
    setStill(s_panAxis, SERVO2_MID, 80);
    break;

  case RS_HAPPY:
    // 开心/兴奋：脖子直立，左右大幅快速摆动
    setStill(s_tiltAxis, SERVO1_MID, 120);            // 0.12
    setSweep(s_panAxis, SERVO2_MIN, SERVO2_MAX, 300); // 0.30
    break;

  case RS_EXCITED:
    // 兴奋：俯仰+偏航同时高频往复
    setSweep(s_tiltAxis, SERVO1_MID - 15, SERVO1_MID + 15, 350); // 0.35
    setSweep(s_panAxis, SERVO2_MIN, SERVO2_MAX, 350);
    break;

  case RS_SAD:
    // 悲伤：缓慢垂头，偏航居中
    setStill(s_tiltAxis, SERVO1_MIN + 5, 40); // 0.04
    setStill(s_panAxis, SERVO2_MID, 40);
    break;

  case RS_ANGRY:
    // 愤怒：快速小幅点头（俯仰往复），偏航居中
    setSweep(s_tiltAxis, SERVO1_MID - 10, SERVO1_MID + 10, 280); // 0.28
    setStill(s_panAxis, SERVO2_MID, 100);                        // 0.10
    break;

  case RS_SLEEPY:
    // 困倦：极缓慢低垂 + 轻微摇头
    setStill(s_tiltAxis, SERVO1_MIN + 10, 20);                 // 0.02
    setSweep(s_panAxis, SERVO2_MID - 15, SERVO2_MID + 15, 30); // 0.03
    break;

  case RS_SURPRISED:
    // 惊讶：快速抬头 + 偏航轻微抖动
    setStill(s_tiltAxis, SERVO1_MAX, 300);                    // 0.30
    setSweep(s_panAxis, SERVO2_MID - 8, SERVO2_MID + 8, 200); // 0.20
    break;

  case RS_WORRIED:
    // 担心：缓慢左右扫视
    setStill(s_tiltAxis, SERVO1_MID, 80);                      // 0.08
    setSweep(s_panAxis, SERVO2_MIN + 15, SERVO2_MAX - 15, 60); // 0.06
    break;
  }
}

void update(unsigned long now) {
  uint8_t t = tickAxis(s_tiltAxis, now);
  uint8_t p = tickAxis(s_panAxis, now);
  s_tilt.write(t);
  s_pan.write(p);
}

} // namespace ServoController
