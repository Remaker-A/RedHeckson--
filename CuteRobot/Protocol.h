#pragma once
/**
 * Protocol.h — 串口协议层
 *
 * 职责：
 *   - 接收 5 字节定长数据包 [AA CMD VAL CSUM 55]
 *   - 校验帧头/帧尾/校验和
 *   - 解析完整包后调用注册的回调
 *   - 发送 ACK 应答
 *
 * 与业务逻辑完全解耦：不直接操作屏幕或舵机。
 */

#include <Arduino.h>
#include "RobotState.h"

// ─── 协议回调类型 ─────────────────────────────────────────────
// 调用者实现这两个函数并通过 Protocol::setCallbacks() 注册

/** 上位机要求切换表情 */
typedef void (*OnSetExpressionFn)(ExpressionId id);

/** 上位机要求切换整体机器人状态（含舵机） */
typedef void (*OnSetRobotStateFn)(RobotStateId id);

/** 上位机要求切换自动模式 */
typedef void (*OnSetAutoModeFn)();

/** 上位机要求直接设置舵机角度 */
typedef void (*OnSetServoFn)(uint8_t tiltIndex, uint8_t panIndex);

// ─── Protocol 命名空间 ───────────────────────────────────────
namespace Protocol {

  /** 注册业务回调，必须在 begin() 之前调用 */
  void setCallbacks(
    OnSetExpressionFn  onExpression,
    OnSetRobotStateFn  onRobotState,
    OnSetAutoModeFn    onAutoMode,
    OnSetServoFn       onServo = nullptr
  );

  /** 初始化串口 */
  void begin();

  /** 放入 loop() 中轮询 */
  void update(unsigned long now);

  /** 主动发送 ACK（业务层也可调用） */
  void sendAck(uint8_t command, uint8_t status);

} // namespace Protocol
