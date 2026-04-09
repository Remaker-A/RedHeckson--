/**
 * EyeDisplay.cpp — 眼睛/屏幕表情层实现
 */

#include "EyeDisplay.h"
#include <Irisoled.h>
#include <IrisoledAnimation.h>

namespace EyeDisplay {

// ─── 屏幕指针 ─────────────────────────────────────────────────
static Adafruit_SSD1306 *s_display = nullptr;

// ─── 自动模式：状态机 ─────────────────────────────────────────
enum AutoState { S_LOGO, S_BLINK, S_SCAN, S_EMO };
static AutoState s_autoState = S_LOGO;
static unsigned long s_nextChange = 0;

const uint16_t AUTO_DURATIONS[] PROGMEM = {1500, 5000, 6000, 7000};

// 眨眼动画
const unsigned char *const BLINK_F[] PROGMEM = {
    Irisoled::normal, Irisoled::blink, Irisoled::blink, Irisoled::blink,
    Irisoled::normal};
const uint16_t BLINK_D[] = {1000, 100, 100, 100, 800};
static IrisoledAnimation s_blinkA(BLINK_F, 5, true, BLINK_D, 200, true);

// 视线扫描动画
const unsigned char *const SCAN_F[] PROGMEM = {
    Irisoled::normal, Irisoled::blink, Irisoled::normal, Irisoled::blink,
    Irisoled::normal};
const uint16_t SCAN_D[] = {400, 400, 300, 300, 500};
static IrisoledAnimation s_scanA(SCAN_F, 5, true, SCAN_D, 200, true);

// 表情循环动画
const unsigned char *const EMO_F[] PROGMEM = {
    Irisoled::happy, Irisoled::excited, Irisoled::surprised,
    Irisoled::sad,   Irisoled::angry,   Irisoled::normal};
const uint16_t EMO_D[] = {600, 400, 400, 600, 500, 800};
static IrisoledAnimation s_emoA(EMO_F, 6, true, EMO_D, 200, true);

// ─── 手动模式：帧动画 ─────────────────────────────────────────
enum Mode { M_AUTO, M_MANUAL };
static Mode s_mode = M_AUTO;

static const unsigned char *s_manualBitmap = Irisoled::normal;
static const unsigned char *const *s_manualFrames = nullptr;
static const uint16_t *s_manualDelays = nullptr;
static uint8_t s_manualFrameCount = 0;
static uint8_t s_manualFrameIdx = 0;
static unsigned long s_manualNextFrame = 0;

// 每种情绪的帧序列 ─────────────────────────────────────────────
const unsigned char *const HAPPY_F[] PROGMEM = {
    Irisoled::happy, Irisoled::blink, Irisoled::happy, Irisoled::excited,
    Irisoled::happy};
const uint16_t HAPPY_D[] PROGMEM = {900, 120, 700, 260, 700};

const unsigned char *const SAD_F[] PROGMEM = {Irisoled::sad, Irisoled::blink,
                                              Irisoled::sad, Irisoled::blink,
                                              Irisoled::sad};
const uint16_t SAD_D[] PROGMEM = {1000, 120, 900, 320, 900};

const unsigned char *const SLEEPY_F[] PROGMEM = {
    Irisoled::sleepy, Irisoled::blink, Irisoled::blink, Irisoled::blink,
    Irisoled::sleepy};
const uint16_t SLEEPY_D[] PROGMEM = {1100, 220, 320, 240, 1100};

const unsigned char *const WORRIED_F[] PROGMEM = {
    Irisoled::worried, Irisoled::blink, Irisoled::worried, Irisoled::blink,
    Irisoled::worried};
const uint16_t WORRIED_D[] PROGMEM = {700, 260, 500, 260, 700};

const unsigned char *const ANGRY_F[] PROGMEM = {
    Irisoled::angry, Irisoled::blink, Irisoled::angry, Irisoled::blink,
    Irisoled::angry};
const uint16_t ANGRY_D[] PROGMEM = {700, 180, 450, 180, 700};

const unsigned char *const SURPRISED_F[] PROGMEM = {
    Irisoled::surprised, Irisoled::blink, Irisoled::surprised};
const uint16_t SURPRISED_D[] PROGMEM = {1200, 120, 900};

const unsigned char *const EXCITED_F[] PROGMEM = {
    Irisoled::excited, Irisoled::blink, Irisoled::excited, Irisoled::blink,
    Irisoled::excited};
const uint16_t EXCITED_D[] PROGMEM = {420, 150, 300, 150, 420};

// ─── 内部工具函数 ─────────────────────────────────────────────

static inline const unsigned char *
readFramePtr(const unsigned char *const frames[], uint8_t i) {
  return reinterpret_cast<const unsigned char *>(pgm_read_ptr(&frames[i]));
}

static inline uint16_t readDelay(const uint16_t delays[], uint8_t i) {
  return pgm_read_word(&delays[i]);
}

static const unsigned char *getExpressionBitmap(ExpressionId id) {
  switch (id) {
  case E_NORMAL:
    return Irisoled::normal;
  case E_HAPPY:
    return Irisoled::happy;
  case E_SAD:
    return Irisoled::sad;
  case E_ANGRY:
    return Irisoled::angry;
  case E_SURPRISED:
    return Irisoled::surprised;
  case E_EXCITED:
    return Irisoled::excited;
  case E_SLEEPY:
    return Irisoled::sleepy;
  case E_WORRIED:
    return Irisoled::worried;
  case E_BLINK:
    return Irisoled::blink;
  case E_LOOK_LEFT:
    return Irisoled::normal;
  case E_LOOK_RIGHT:
    return Irisoled::normal;
  case E_LOOK_UP:
    return Irisoled::normal;
  case E_LOOK_DOWN:
    return Irisoled::normal;
  case E_LOGO:
    return Irisoled::logo;
  default:
    return nullptr;
  }
}

static void drawBitmap(const unsigned char *bitmap) {
  if (!s_display || !bitmap)
    return;
  s_display->clearDisplay();
  s_display->drawBitmap(0, EYE_OFFSET_Y, bitmap, SCREEN_W, SCREEN_H, 1);
  s_display->display();
}

static void stopAllAnimations() {
  s_blinkA.stop();
  s_scanA.stop();
  s_emoA.stop();
}

static void enterAutoState(AutoState next, unsigned long now) {
  s_autoState = next;
  stopAllAnimations();
  const uint16_t dur = pgm_read_word(&AUTO_DURATIONS[next]);
  s_nextChange = now + dur;
  switch (next) {
  case S_BLINK:
    s_blinkA.reset();
    s_blinkA.start();
    break;
  case S_SCAN:
    s_scanA.reset();
    s_scanA.start();
    break;
  case S_EMO:
    s_emoA.reset();
    s_emoA.start();
    break;
  default:
    break;
  }
}

static void resetManualAnimation(const unsigned char *const frames[],
                                 const uint16_t delays[], uint8_t frameCount,
                                 unsigned long now) {
  s_manualFrames = frames;
  s_manualDelays = delays;
  s_manualFrameCount = frameCount;
  s_manualFrameIdx = 0;
  s_manualBitmap = readFramePtr(frames, 0);
  s_manualNextFrame = now + readDelay(delays, 0);
  drawBitmap(s_manualBitmap);
}

static void clearManualAnimation() {
  s_manualFrames = nullptr;
  s_manualDelays = nullptr;
  s_manualFrameCount = 0;
  s_manualFrameIdx = 0;
  s_manualNextFrame = 0;
}

/** 尝试为 expressionId 启动帧动画；无预设动画则返回 false */
static bool tryStartManualAnimation(ExpressionId id, unsigned long now) {
  switch (id) {
  case E_HAPPY:
    resetManualAnimation(HAPPY_F, HAPPY_D, 5, now);
    return true;
  case E_SAD:
    resetManualAnimation(SAD_F, SAD_D, 5, now);
    return true;
  case E_SLEEPY:
    resetManualAnimation(SLEEPY_F, SLEEPY_D, 5, now);
    return true;
  case E_WORRIED:
    resetManualAnimation(WORRIED_F, WORRIED_D, 5, now);
    return true;
  case E_ANGRY:
    resetManualAnimation(ANGRY_F, ANGRY_D, 5, now);
    return true;
  case E_SURPRISED:
    resetManualAnimation(SURPRISED_F, SURPRISED_D, 3, now);
    return true;
  case E_EXCITED:
    resetManualAnimation(EXCITED_F, EXCITED_D, 5, now);
    return true;
  default:
    clearManualAnimation();
    return false;
  }
}

static void tickManualMode(unsigned long now) {
  if (!s_manualFrames || s_manualFrameCount == 0)
    return;
  if ((long)(now - s_manualNextFrame) < 0)
    return;

  s_manualFrameIdx = (s_manualFrameIdx + 1) % s_manualFrameCount;
  s_manualBitmap = readFramePtr(s_manualFrames, s_manualFrameIdx);
  s_manualNextFrame = now + readDelay(s_manualDelays, s_manualFrameIdx);
  drawBitmap(s_manualBitmap);
}

// ─── 公开 API ─────────────────────────────────────────────────

void begin(Adafruit_SSD1306 &display) {
  s_display = &display;
  drawBitmap(Irisoled::logo);
  s_nextChange = millis() + pgm_read_word(&AUTO_DURATIONS[S_LOGO]);
}

void setExpression(ExpressionId id, unsigned long now) {
  s_mode = M_MANUAL;
  stopAllAnimations();
  if (!tryStartManualAnimation(id, now)) {
    s_manualBitmap = getExpressionBitmap(id);
    drawBitmap(s_manualBitmap);
  }
}

void setAutoMode(unsigned long now) {
  s_mode = M_AUTO;
  clearManualAnimation();
  enterAutoState(S_BLINK, now);
}

bool isAutoMode() { return s_mode == M_AUTO; }

void update(unsigned long now) {
  if (s_mode == M_AUTO) {
    // 状态机推进
    if ((long)(now - s_nextChange) >= 0) {
      switch (s_autoState) {
      case S_LOGO:
        enterAutoState(S_BLINK, now);
        break;
      case S_BLINK:
        enterAutoState(S_SCAN, now);
        break;
      case S_SCAN:
        enterAutoState(S_EMO, now);
        break;
      case S_EMO:
        enterAutoState(S_BLINK, now);
        break;
      }
    }
    // 动画帧更新
    switch (s_autoState) {
    case S_BLINK:
      s_blinkA.update(*s_display, 0, EYE_OFFSET_Y, SCREEN_W, SCREEN_H);
      break;
    case S_SCAN:
      s_scanA.update(*s_display, 0, EYE_OFFSET_Y, SCREEN_W, SCREEN_H);
      break;
    case S_EMO:
      s_emoA.update(*s_display, 0, EYE_OFFSET_Y, SCREEN_W, SCREEN_H);
      break;
    default:
      break;
    }
  } else {
    tickManualMode(now);
  }
}

} // namespace EyeDisplay
