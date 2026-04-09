# robot_protocol

CuteRobot 串口协议库 - 用于与 Arduino 机器人通信的 Python 组件库。

## 安装

```bash
pip install pyserial
```

## 快速开始

```python
import queue
from robot_protocol import SerialWorker, ActionSequence, Keyframe, encode_servo

# 1. 创建串口工作线程
log_q = queue.Queue()
worker = SerialWorker("COM6", log_q)
worker.start()

# 2. 发送舵机命令
worker.send_raw(encode_servo(90, 90))  # 俯仰90°, 偏航90°

# 3. 停止
worker.stop()
worker.join()
```

## 模块结构

```
robot_protocol/
├── __init__.py          # 公共API导出
├── constants.py          # 协议常量
├── protocol.py          # 数据包编解码
├── serial_worker.py      # 串口通信线程
├── playback.py           # 动作回放引擎
└── action.py            # 动作序列数据结构
```

---

## constants.py - 协议常量

### 串口配置

```python
from robot_protocol import BAUD_RATE  # 115200
```

### 数据包格式

```
[AA] [CMD] [VAL] [CSUM] [55]
 0    1     2     3      4
```

- `PACKET_HEAD = 0xAA` - 帧头
- `PACKET_TAIL = 0x55` - 帧尾
- `CSUM = CMD ^ VAL` - 校验和

### 命令码

```python
from robot_protocol import (
    CMD_SET_EXPRESSION,   # 0x01 - 设置表情
    CMD_SET_AUTO_MODE,    # 0x02 - 自动模式
    CMD_SET_SERVO,       # 0x03 - 设置舵机角度
    CMD_SET_ROBOT_STATE,  # 0x04 - 设置机器人状态
)
```

### 舵机角度范围

```python
from robot_protocol import (
    SERVO1_MIN, SERVO1_MID, SERVO1_MAX,  # 俯仰: 50, 90, 130
    SERVO2_MIN, SERVO2_MID, SERVO2_MAX,  # 偏航: 45, 90, 135
)
```

### 表情定义

```python
from robot_protocol import EXPRESSIONS

EXPRESSIONS = {
    "NORMAL": 16,
    "HAPPY": 11,
    "SAD": 17,
    "ANGRY": 1,
    "EXCITED": 8,
    "SURPRISED": 20,
    "SLEEPY": 19,
    "WORRIED": 23,
    "BLINK": 4,
    "LOGO": 28,
    "LOOK_LEFT": 13,
    "LOOK_RIGHT": 14,
    "LOOK_UP": 15,
    "LOOK_DOWN": 12,
}
```

### 机器人状态

```python
from robot_protocol import ROBOT_STATES, STATE_EMOJI

ROBOT_STATES = {
    "IDLE": 0,
    "HAPPY": 1,
    "SAD": 2,
    "ANGRY": 3,
    "SLEEPY": 4,
    "SURPRISED": 5,
    "EXCITED": 6,
    "WORRIED": 7,
}
```

---

## protocol.py - 协议编解码

### build_packet(cmd, val)

构建5字节数据包。

```python
from robot_protocol import build_packet

pkt = build_packet(0x03, 0x44)
# -> b'\xaa\x03\x44G\x55'
```

### encode_servo(tilt, pan)

将角度编码为单字节。

- 俯仰(tilt) → 高4位 (0-8)
- 偏航(pan) → 低4位 (0-8)

```python
from robot_protocol import encode_servo

val = encode_servo(90, 90)   # -> 0x44
val = encode_servo(50, 45)   # -> 0x00
val = encode_servo(130, 135) # -> 0x88
```

### decode_servo(val)

解码单字节为角度值。

```python
from robot_protocol import decode_servo

tilt, pan = decode_servo(0x44)  # -> (90, 90)
```

### parse_ack(buf)

解析 ACK 响应。

```python
from robot_protocol import parse_ack

result = parse_ack(rx_bytes)
if result:
    cmd, status = result
```

---

## serial_worker.py - 串口通信

### SerialWorker(port, log_q)

串口通信后台线程。

```python
import queue
from robot_protocol import SerialWorker

log_q = queue.Queue()
worker = SerialWorker("COM6", log_q)
worker.start()
```

#### 方法

| 方法 | 说明 |
|------|------|
| `send(cmd, val)` | 发送命令（自动打包） |
| `send_raw(pkt)` | 发送原始数据包 |
| `stop()` | 停止线程 |

#### 日志格式

通过 `log_q` 输出，格式为 `(level, message)`：

```python
# 接收日志示例
("ok", "已连接 COM6 @ 115200")
("tx", "TX  AA 03 44 47 55")
("ok", "ACK  cmd=0x03  OK")
("err", "ACK  cmd=0x03  BAD_PACKET")
("info", "串口已关闭")
```

#### 示例：发送表情

```python
from robot_protocol import SerialWorker, build_packet, EXPRESSIONS

worker = SerialWorker("COM6", log_q)
worker.start()

# 发送 HAPPY 表情
worker.send(0x01, EXPRESSIONS["HAPPY"])
```

---

## playback.py - 动作回放

### PlaybackEngine(packets, worker, done_cb)

动作回放引擎（独立线程）。

```python
from robot_protocol import PlaybackEngine

def on_done():
    print("回放完成")

engine = PlaybackEngine(packets, worker, on_done)
engine.start()
```

#### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `progress` | float | 回放进度 (0.0-1.0) |

#### 方法

| 方法 | 说明 |
|------|------|
| `stop()` | 停止回放 |
| `is_alive()` | 检查是否在运行 |

---

## action.py - 动作序列

### Keyframe

单个关键帧。

```python
from robot_protocol import Keyframe

kf = Keyframe(t_ms=0, tilt=90, pan=90, expr="HAPPY", easing="ease_in_out")
```

#### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `t_ms` | int | 时间戳（毫秒） |
| `tilt` | int | 俯仰角度 (50-130) |
| `pan` | int | 偏航角度 (45-135) |
| `expr` | str | 表情名称（可选） |
| `easing` | str | 缓动曲线 |

#### 方法

- `to_dict()` → dict
- `from_dict(d)` → Keyframe

### ActionSequence

动作序列容器。

```python
from robot_protocol import ActionSequence, Keyframe

seq = ActionSequence("摇头", loop=False)
seq.add_frame(Keyframe(0, 90, 45))
seq.add_frame(Keyframe(500, 90, 135))
seq.add_frame(Keyframe(1000, 90, 45))
```

#### 方法

| 方法 | 说明 |
|------|------|
| `add_frame(kf)` | 添加关键帧（自动排序） |
| `remove_frame(idx)` | 删除关键帧 |
| `trim_start(ms)` | 掐头：删除指定时间之前的帧 |
| `trim_end(ms)` | 去尾：删除指定时间之后的帧 |
| `duration_ms()` | 获取总时长（毫秒） |
| `build_playback_packets(interval_ms=20)` | 生成回放数据包列表 |
| `to_dict()` | 序列化为字典 |
| `from_dict(d)` | 从字典反序列化 |

#### build_playback_packets()

返回格式：`List[Tuple[int, bytes]]` - `(时间戳, 数据包)`

```python
from robot_protocol import ActionSequence, Keyframe

seq = ActionSequence("摇头")
seq.add_frame(Keyframe(0, 90, 45))
seq.add_frame(Keyframe(500, 90, 135))

packets = seq.build_playback_packets(interval_ms=20)
# -> [(0, b'...'), (20, b'...'), (40, b'...'), ...]
```

---

## 使用示例

### 完整示教-回放流程

```python
import queue
import time
from robot_protocol import (
    SerialWorker, ActionSequence, Keyframe,
    encode_servo, build_packet,
    CMD_SET_SERVO, CMD_SET_EXPRESSION,
)

# 1. 连接
log_q = queue.Queue()
worker = SerialWorker("COM6", log_q)
worker.start()

# 2. 录制动作
seq = ActionSequence("跳舞")
timestamps = [0, 500, 1000, 1500]
tilt_angles = [90, 70, 110, 90]
pan_angles = [90, 45, 135, 90]

for t, tilt, pan in zip(timestamps, tilt_angles, pan_angles):
    seq.add_frame(Keyframe(t, tilt, pan))
    # 实时发送到机器人
    worker.send_raw(build_packet(CMD_SET_SERVO, encode_servo(tilt, pan)))
    time.sleep(0.1)

# 3. 回放
packets = seq.build_playback_packets()

def on_done():
    print("动作完成")

engine = PlaybackEngine(packets, worker, on_done)
engine.start()

# 4. 等待完成
while engine.is_alive():
    time.sleep(0.1)
    print(f"进度: {engine.progress * 100:.1f}%")

# 5. 断开
worker.stop()
worker.join()
```

### 加载/保存动作序列

```python
import json
from robot_protocol import ActionSequence

# 保存
data = [seq.to_dict() for seq in sequences]
with open("actions.json", "w") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# 加载
with open("actions.json", "r") as f:
    data = json.load(f)
sequences = [ActionSequence.from_dict(d) for d in data]
```

---

## 协议详解

### 数据包格式

```
┌─────────┬─────────┬─────────┬─────────┬─────────┐
│  0xAA   │   CMD   │   VAL   │  CSUM   │  0x55   │
│  帧头    │  命令字节 │  参数值  │ CMD^VAL │  帧尾   │
└─────────┴─────────┴─────────┴─────────┴─────────┘
```

### 命令详解

| CMD | 名称 | VAL | 说明 |
|-----|------|-----|------|
| 0x01 | SET_EXPRESSION | 0-31 | 表情ID |
| 0x02 | SET_AUTO_MODE | 0 | 进入自动模式 |
| 0x03 | SET_SERVO | 0xTP | T=俯仰索引(0-8), P=偏航索引(0-8) |
| 0x04 | SET_ROBOT_STATE | 0-7 | 机器人状态ID |

### 舵机角度编码

```
VAL 字节:
  bit7   bit4   bit0
  ┌───────┬───────┐
  │ Tilt  │  Pan  │
  │ 0-8   │ 0-8   │
  └───────┴───────┘

角度计算:
  tilt = SERVO1_MIN + tilt_index * (SERVO1_MAX - SERVO1_MIN) / 8
  pan  = SERVO2_MIN + pan_index  * (SERVO2_MAX - SERVO2_MIN) / 8
```

### ACK 响应

机器人收到命令后返回5字节ACK：

```
AA CMD STATUS CSUM 55
```

- `STATUS = 0x00` → OK
- `STATUS = 0xE1` → BAD_PACKET（校验失败）
- `STATUS = 0xE2` → BAD_COMMAND（未知命令）
- `STATUS = 0xE3` → BAD_PARAM（参数错误）
