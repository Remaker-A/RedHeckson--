# Soul 多级上下文（临时存档）

本文件用于存放**当前后端里的 L0～L3 快照**，以及你**本轮对话里**想单独记下的补充信息（尚未写进 `soul.json` 等的备注）。

- **更新机器快照**：后端运行中，在项目根目录执行  
  `python test_demo_flow.py --export-soul-md`  
  会刷新下方 `<!-- AUTO_START -->` 与 `<!-- AUTO_END -->` 之间的内容。  
- **手写对话相关上下文**：只改 `<!-- MANUAL_START -->` 之后的段落即可，导出快照时会保留。

---

<!-- AUTO_START -->
*快照时间：`2026-04-08 21:29:54`（由后端根据当前 soul / personality / rhythm / 状态机生成）*

## L0 · 灵魂

用户用「迷茫」描述自己当前的状态。
用户最近纠结的事：不知道该不该换工作，现在的工作稳定但没有成长空间

## L1 · 性格

你的性格偏向：冒险
关于你：它刚刚来到这里，还在认识你。它的性格偏冒险，对新事物充满好奇。

## L2 · 节律

还没有足够的节律数据。

## L3 · 实时情境

当前状态：主人不在桌前
现在是傍晚

---

## 原始结构（JSON，便于调试或复制）

```json
{
  "L0": {
    "created_at": "2026-04-08T21:03:00.288252",
    "current_state_word": "迷茫",
    "struggle": "不知道该不该换工作，现在的工作稳定但没有成长空间",
    "bias": "adventurous",
    "opening_response": "你来了。"
  },
  "L1": {
    "version": 1,
    "updated_at": "2026-04-08T21:03:00.288657",
    "params": {
      "bias": "adventurous",
      "night_owl_index": 0.0,
      "anxiety_sensitivity": 0.0,
      "quietness": 0.5,
      "attachment_level": 0.0
    },
    "natural_description": "它刚刚来到这里，还在认识你。它的性格偏冒险，对新事物充满好奇。",
    "evolution_log": []
  },
  "L3": {
    "state": "idle",
    "state_since": "2026-04-08T21:16:25.296206",
    "seated_minutes": 0,
    "distance_cm": 999.0,
    "time_period": "evening",
    "is_night": false,
    "today_total_minutes": 0,
    "focus": {
      "active": false,
      "duration_minutes": 25,
      "started_at": null
    }
  }
}
```
<!-- AUTO_END -->

<!-- MANUAL_START -->` 之后的段落即可，导出快照时会保留。

---

<!-- AUTO_START -->

*（尚未导出：请先 `cd backend && python main.py` 启动后端，再运行 `python test_demo_flow.py --export-soul-md`）*

<!-- AUTO_END -->

<!-- MANUAL_START -->

## 本次对话带来的补充上下文

在此记录：对话里出现的事实、情绪、约定、人设微调想法等（多级信息可混写在一处或分小标题）。

-

<!-- MANUAL_END -->
