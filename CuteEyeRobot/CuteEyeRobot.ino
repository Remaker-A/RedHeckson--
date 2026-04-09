/**********
  CuteEyeRobot.ino - 精简版
  适配Arduino Uno (32KB)

  功能：眨眼 → 视线扫描 → 表情循环
  
  使用库: D:\projects\Irisoled\src
**********/

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Irisoled.h>
#include <IrisoledAnimation.h>

Adafruit_SSD1306 display(128, 64, &Wire, -1);
constexpr uint8_t SCREEN_W = 128;
constexpr uint8_t SCREEN_H = 64;
constexpr int8_t EYE_OFFSET_Y = 10;
constexpr unsigned long SERIAL_BAUD = 115200;
constexpr uint8_t PACKET_HEAD = 0xAA;
constexpr uint8_t PACKET_TAIL = 0x55;
constexpr uint8_t CMD_SET_EXPRESSION = 0x01;
constexpr uint8_t CMD_SET_AUTO_MODE = 0x02;
constexpr uint8_t ACK_OK = 0x00;
constexpr uint8_t ACK_BAD_PACKET = 0xE1;
constexpr uint8_t ACK_BAD_COMMAND = 0xE2;
constexpr uint8_t ACK_BAD_PARAM = 0xE3;
constexpr uint8_t FULL_BITMAP_SET = 0; // 0 for UNO size, 1 for larger boards

// 眨眼 (PROGMEM版)
const unsigned char* const BLINK_F[] PROGMEM = {
  Irisoled::normal, Irisoled::blink_down, Irisoled::blink, Irisoled::blink_down, Irisoled::normal
};
const uint16_t BLINK_D[] = { 1000, 100, 100, 100, 800 };

// 视线扫描 (PROGMEM版)
const unsigned char* const SCAN_F[] PROGMEM = {
  Irisoled::look_left, Irisoled::look_right, 
  Irisoled::look_up, Irisoled::look_down, Irisoled::normal
};
const uint16_t SCAN_D[] = { 400, 400, 300, 300, 500 };

// 表情循环 (PROGMEM版)
const unsigned char* const EMO_F[] PROGMEM = {
  Irisoled::happy, Irisoled::excited, Irisoled::surprised, 
  Irisoled::sad, Irisoled::angry, Irisoled::normal
};
const uint16_t EMO_D[] = { 600, 400, 400, 600, 500, 800 };

// 创建动画 (用PROGMEM构造函数省内存)
IrisoledAnimation blinkA(BLINK_F, 5, true, BLINK_D, 200, true);
IrisoledAnimation scanA(SCAN_F, 5, true, SCAN_D, 200, true);
IrisoledAnimation emoA(EMO_F, 6, true, EMO_D, 200, true);

const unsigned char* const HAPPY_MANUAL_F[] PROGMEM = {
  Irisoled::happy, Irisoled::blink, Irisoled::happy, Irisoled::excited, Irisoled::happy
};
const uint16_t HAPPY_MANUAL_D[] PROGMEM = { 900, 120, 700, 260, 700 };

const unsigned char* const SAD_MANUAL_F[] PROGMEM = {
  Irisoled::sad, Irisoled::blink, Irisoled::sad, Irisoled::look_down, Irisoled::sad
};
const uint16_t SAD_MANUAL_D[] PROGMEM = { 1000, 120, 900, 320, 900 };

const unsigned char* const SLEEPY_MANUAL_F[] PROGMEM = {
  Irisoled::sleepy, Irisoled::blink_down, Irisoled::blink, Irisoled::blink_down, Irisoled::sleepy
};
const uint16_t SLEEPY_MANUAL_D[] PROGMEM = { 1100, 220, 320, 240, 1100 };

const unsigned char* const WORRIED_MANUAL_F[] PROGMEM = {
  Irisoled::worried, Irisoled::look_left, Irisoled::worried, Irisoled::look_right, Irisoled::worried
};
const uint16_t WORRIED_MANUAL_D[] PROGMEM = { 700, 260, 500, 260, 700 };

const unsigned char* const ANGRY_MANUAL_F[] PROGMEM = {
  Irisoled::angry, Irisoled::look_left, Irisoled::angry, Irisoled::look_right, Irisoled::angry
};
const uint16_t ANGRY_MANUAL_D[] PROGMEM = { 700, 180, 450, 180, 700 };

const unsigned char* const SURPRISED_MANUAL_F[] PROGMEM = {
  Irisoled::surprised, Irisoled::blink, Irisoled::surprised
};
const uint16_t SURPRISED_MANUAL_D[] PROGMEM = { 1200, 120, 900 };

const unsigned char* const EXCITED_MANUAL_F[] PROGMEM = {
  Irisoled::excited, Irisoled::look_left, Irisoled::excited, Irisoled::look_right, Irisoled::excited
};
const uint16_t EXCITED_MANUAL_D[] PROGMEM = { 420, 150, 300, 150, 420 };

enum State { S_LOGO, S_BLINK, S_SCAN, S_EMO };
enum Mode { M_AUTO, M_MANUAL };
enum ExpressionId {
  E_ALERT = 0,
  E_ANGRY = 1,
  E_BLINK_DOWN = 2,
  E_BLINK_UP = 3,
  E_BLINK = 4,
  E_BORED = 5,
  E_DESPAIR = 6,
  E_DISORIENTED = 7,
  E_EXCITED = 8,
  E_FOCUSED = 9,
  E_FURIOUS = 10,
  E_HAPPY = 11,
  E_LOOK_DOWN = 12,
  E_LOOK_LEFT = 13,
  E_LOOK_RIGHT = 14,
  E_LOOK_UP = 15,
  E_NORMAL = 16,
  E_SAD = 17,
  E_SCARED = 18,
  E_SLEEPY = 19,
  E_SURPRISED = 20,
  E_WINK_LEFT = 21,
  E_WINK_RIGHT = 22,
  E_WORRIED = 23,
  E_BATTERY_FULL = 24,
  E_BATTERY_LOW = 25,
  E_BATTERY = 26,
  E_LEFT_SIGNAL = 27,
  E_LOGO = 28,
  E_MODE = 29,
  E_RIGHT_SIGNAL = 30,
  E_WARNING = 31
};

State state = S_LOGO;
Mode mode = M_AUTO;
unsigned long nextChange = 0;
const uint16_t DUR[] PROGMEM = { 1500, 5000, 6000, 7000 };
#if FULL_BITMAP_SET
const unsigned char* const EXPRESSIONS[] PROGMEM = {
  Irisoled::alert,
  Irisoled::angry,
  Irisoled::blink_down,
  Irisoled::blink_up,
  Irisoled::blink,
  Irisoled::bored,
  Irisoled::despair,
  Irisoled::disoriented,
  Irisoled::excited,
  Irisoled::focused,
  Irisoled::furious,
  Irisoled::happy,
  Irisoled::look_down,
  Irisoled::look_left,
  Irisoled::look_right,
  Irisoled::look_up,
  Irisoled::normal,
  Irisoled::sad,
  Irisoled::scared,
  Irisoled::sleepy,
  Irisoled::surprised,
  Irisoled::wink_left,
  Irisoled::wink_right,
  Irisoled::worried,
  Irisoled::battery_full,
  Irisoled::battery_low,
  Irisoled::battery,
  Irisoled::left_signal,
  Irisoled::logo,
  Irisoled::mode,
  Irisoled::right_signal,
  Irisoled::warning
};
constexpr uint8_t EXPRESSION_COUNT = sizeof(EXPRESSIONS) / sizeof(EXPRESSIONS[0]);
#endif

uint8_t packetBuffer[5];
uint8_t packetIndex = 0;
const unsigned char* manualExpression = Irisoled::normal;
const unsigned char* const* manualFrames = nullptr;
const uint16_t* manualDelays = nullptr;
uint8_t manualFrameCount = 0;
uint8_t manualFrameIndex = 0;
unsigned long manualNextFrame = 0;

static uint16_t getStateDuration(State s) {
  return pgm_read_word(&DUR[s]);
}

static const unsigned char* getBitmapFromFrameTable(
  const unsigned char* const frames[],
  uint8_t index
) {
  return reinterpret_cast<const unsigned char*>(pgm_read_ptr(&frames[index]));
}

static uint16_t getDelayFromTable(const uint16_t delays[], uint8_t index) {
  return pgm_read_word(&delays[index]);
}

static const unsigned char* getExpressionBitmap(uint8_t expressionId) {
#if FULL_BITMAP_SET
  if (expressionId >= EXPRESSION_COUNT) {
    return nullptr;
  }
  return reinterpret_cast<const unsigned char*>(pgm_read_ptr(&EXPRESSIONS[expressionId]));
#else
  switch (expressionId) {
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
      return Irisoled::look_left;
    case E_LOOK_RIGHT:
      return Irisoled::look_right;
    case E_LOOK_UP:
      return Irisoled::look_up;
    case E_LOOK_DOWN:
      return Irisoled::look_down;
    case E_LOGO:
      return Irisoled::logo;
    default:
      return nullptr;
  }
#endif
}

static void stopAllAnimations() {
  blinkA.stop();
  scanA.stop();
  emoA.stop();
}

static void enterState(State s, unsigned long now) {
  state = s;
  stopAllAnimations();

  switch (state) {
    case S_LOGO:
      break;
    case S_BLINK:
      blinkA.reset();
      blinkA.start();
      break;
    case S_SCAN:
      scanA.reset();
      scanA.start();
      break;
    case S_EMO:
      emoA.reset();
      emoA.start();
      break;
  }

  nextChange = now + getStateDuration(state);
}

static void drawManualExpression() {
  display.clearDisplay();
  display.drawBitmap(0, EYE_OFFSET_Y, manualExpression, SCREEN_W, SCREEN_H, 1);
  display.display();
}

static void resetManualAnimation(
  const unsigned char* const frames[],
  const uint16_t delays[],
  uint8_t frameCount,
  unsigned long now
) {
  manualFrames = frames;
  manualDelays = delays;
  manualFrameCount = frameCount;
  manualFrameIndex = 0;
  manualExpression = getBitmapFromFrameTable(manualFrames, manualFrameIndex);
  manualNextFrame = now + getDelayFromTable(manualDelays, manualFrameIndex);
  drawManualExpression();
}

static void clearManualAnimation() {
  manualFrames = nullptr;
  manualDelays = nullptr;
  manualFrameCount = 0;
  manualFrameIndex = 0;
  manualNextFrame = 0;
}

static bool startManualAnimation(uint8_t expressionId, unsigned long now) {
  switch (expressionId) {
    case E_HAPPY:
      resetManualAnimation(HAPPY_MANUAL_F, HAPPY_MANUAL_D, 5, now);
      return true;
    case E_SAD:
      resetManualAnimation(SAD_MANUAL_F, SAD_MANUAL_D, 5, now);
      return true;
    case E_SLEEPY:
      resetManualAnimation(SLEEPY_MANUAL_F, SLEEPY_MANUAL_D, 5, now);
      return true;
    case E_WORRIED:
      resetManualAnimation(WORRIED_MANUAL_F, WORRIED_MANUAL_D, 5, now);
      return true;
    case E_ANGRY:
      resetManualAnimation(ANGRY_MANUAL_F, ANGRY_MANUAL_D, 5, now);
      return true;
    case E_SURPRISED:
      resetManualAnimation(SURPRISED_MANUAL_F, SURPRISED_MANUAL_D, 3, now);
      return true;
    case E_EXCITED:
      resetManualAnimation(EXCITED_MANUAL_F, EXCITED_MANUAL_D, 5, now);
      return true;
    default:
      clearManualAnimation();
      return false;
  }
}

static void updateManualMode(unsigned long now) {
  if (manualFrames == nullptr || manualFrameCount == 0) {
    return;
  }

  if ((long)(now - manualNextFrame) < 0) {
    return;
  }

  manualFrameIndex++;
  if (manualFrameIndex >= manualFrameCount) {
    manualFrameIndex = 0;
  }

  manualExpression = getBitmapFromFrameTable(manualFrames, manualFrameIndex);
  manualNextFrame = now + getDelayFromTable(manualDelays, manualFrameIndex);
  drawManualExpression();
}

static void sendAck(uint8_t command, uint8_t status) {
  const uint8_t checksum = command ^ status;
  const uint8_t response[5] = { PACKET_HEAD, command, status, checksum, PACKET_TAIL };
  Serial.write(response, sizeof(response));
}

static void setManualExpression(uint8_t expressionId, unsigned long now) {
  mode = M_MANUAL;
  stopAllAnimations();
  if (!startManualAnimation(expressionId, now)) {
    manualExpression = getExpressionBitmap(expressionId);
    drawManualExpression();
  }
}

static void setAutoMode(unsigned long now) {
  mode = M_AUTO;
  clearManualAnimation();
  enterState(S_BLINK, now);
}

static void handlePacket(const uint8_t* packet, unsigned long now) {
  const uint8_t command = packet[1];
  const uint8_t value = packet[2];
  const uint8_t checksum = packet[3];

  if ((command ^ value) != checksum) {
    sendAck(command, ACK_BAD_PACKET);
    return;
  }

  switch (command) {
    case CMD_SET_EXPRESSION:
      if (getExpressionBitmap(value) == nullptr) {
        sendAck(command, ACK_BAD_PARAM);
        return;
      }
      setManualExpression(value, now);
      sendAck(command, ACK_OK);
      break;
    case CMD_SET_AUTO_MODE:
      setAutoMode(now);
      sendAck(command, ACK_OK);
      break;
    default:
      sendAck(command, ACK_BAD_COMMAND);
      break;
  }
}

static void processSerial(unsigned long now) {
  while (Serial.available() > 0) {
    const uint8_t data = static_cast<uint8_t>(Serial.read());

    if (packetIndex == 0) {
      if (data == PACKET_HEAD) {
        packetBuffer[packetIndex++] = data;
      }
      continue;
    }

    packetBuffer[packetIndex++] = data;

    if (packetIndex < sizeof(packetBuffer)) {
      continue;
    }

    if (packetBuffer[4] == PACKET_TAIL) {
      handlePacket(packetBuffer, now);
    } else {
      sendAck(packetBuffer[1], ACK_BAD_PACKET);
    }

    packetIndex = 0;
  }
}

void setup() {
  Serial.begin(SERIAL_BAUD);

  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    while (true) { }
  }

  display.drawBitmap(0, EYE_OFFSET_Y, Irisoled::logo, SCREEN_W, SCREEN_H, 1);
  display.display();
  nextChange = millis() + getStateDuration(S_LOGO);
}

void loop() {
  unsigned long now = millis();
  processSerial(now);
  
  if (mode == M_AUTO && (long)(now - nextChange) >= 0) {
    switch (state) {
      case S_LOGO:
        enterState(S_BLINK, now);
        break;
      case S_BLINK:
        enterState(S_SCAN, now);
        break;
      case S_SCAN:
        enterState(S_EMO, now);
        break;
      case S_EMO:
        enterState(S_BLINK, now);
        break;
    }
  }
  
  if (mode == M_AUTO) {
    switch (state) {
      case S_LOGO:
        break;
      case S_BLINK:
        blinkA.update(display, 0, EYE_OFFSET_Y, SCREEN_W, SCREEN_H);
        break;
      case S_SCAN:
        scanA.update(display, 0, EYE_OFFSET_Y, SCREEN_W, SCREEN_H);
        break;
      case S_EMO:
        emoA.update(display, 0, EYE_OFFSET_Y, SCREEN_W, SCREEN_H);
        break;
    }
  } else {
    updateManualMode(now);
  }
}
