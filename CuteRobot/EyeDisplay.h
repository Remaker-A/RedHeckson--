#pragma once
/**
 * EyeDisplay.h — 眼睛/屏幕表情层
 *
 * 职责：
 *   - 管理自动动画状态机（Logo → 眨眼 → 扫视 → 表情循环）
 *   - 管理手动表情动画（每种表情带闪烁/移动帧序列）
 *   - 提供 setExpression() / setAutoMode() 接口供外部调用
 *   - 完全封装屏幕驱动，外部无需包含 Adafruit_SSD1306
 */

#include <Arduino.h>
#include <Adafruit_SSD1306.h>
#include "RobotState.h"

namespace EyeDisplay {

  /** 初始化屏幕，显示 Logo；需在 setup() 中调用 */
  void begin(Adafruit_SSD1306& display);

  /** 放入 loop() 中轮询 */
  void update(unsigned long now);

  /** 切换到指定手动表情（进入 M_MANUAL 模式） */
  void setExpression(ExpressionId id, unsigned long now);

  /** 切回自动模式 */
  void setAutoMode(unsigned long now);

  /** 当前是否处于自动模式 */
  bool isAutoMode();

} // namespace EyeDisplay
