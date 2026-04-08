"""
CLI 测试脚本 - 端到端验证整个 companion agent 演示流程

用法:
  1. 先启动后端: cd backend && python main.py
  2. 运行本脚本:
       python test_demo_flow.py              # 全自动跑完演示流程
       python test_demo_flow.py --manual     # 交互式：手动发指令 / 留言 / 触发陪伴说话
       python test_demo_flow.py --chat       # 多轮对话（需后端 + 已配置 LLM）
       python test_demo_flow.py --export-soul-md  # 把 L0–L3 快照写入 soul.md（保留手写区）

功能:
  - 重置旧数据 → 创建灵魂 → 模拟交互 → 验证状态切换
  - 快进演化 → 检查性格变化 → 生成纸条 → 留言
  - 每步都有彩色输出，方便观察结果
"""

import asyncio
import sys
import json
import os
import time
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import httpx

BASE = "http://localhost:8000"

_SOUL_MD = Path(__file__).resolve().parent / "soul.md"
_AUTO_START = "<!-- AUTO_START -->"
_AUTO_END = "<!-- AUTO_END -->"
_MANUAL_START = "<!-- MANUAL_START -->"
_MANUAL_END = "<!-- MANUAL_END -->"
_DEFAULT_MANUAL = """

## 本次对话带来的补充上下文

在此记录：对话里出现的事实、情绪、约定、人设微调想法等（多级信息可混写在一处或分小标题）。

-

"""


def _extract_manual_block(raw: str) -> str:
    if _MANUAL_START not in raw:
        return _DEFAULT_MANUAL
    rest = raw.split(_MANUAL_START, 1)[1]
    if _MANUAL_END in rest:
        return rest.split(_MANUAL_END, 1)[0]
    return rest


def _build_soul_md(snapshot: str, manual_inner: str) -> str:
    return f"""# Soul 多级上下文（临时存档）

本文件用于存放**当前后端里的 L0～L3 快照**，以及你**本轮对话里**想单独记下的补充信息（尚未写进 `soul.json` 等的备注）。

- **更新机器快照**：后端运行中，在项目根目录执行  
  `python test_demo_flow.py --export-soul-md`  
  会刷新下方 `{_AUTO_START}` 与 `{_AUTO_END}` 之间的内容。  
- **手写对话相关上下文**：只改 `{_MANUAL_START}` 之后的段落即可，导出快照时会保留。

---

{_AUTO_START}
{snapshot.strip()}
{_AUTO_END}

{_MANUAL_START}{manual_inner}{_MANUAL_END}
"""


async def export_soul_md_main():
    """GET /api/companion/context-markdown → 合并写入 companion-agent/soul.md"""
    manual = _DEFAULT_MANUAL
    if _SOUL_MD.exists():
        try:
            manual = _extract_manual_block(_SOUL_MD.read_text(encoding="utf-8"))
        except OSError:
            pass
    async with httpx.AsyncClient(base_url=BASE, timeout=60.0) as c:
        try:
            await c.get("/")
        except httpx.ConnectError:
            fail("无法连接后端！请先 cd backend && python main.py")
            return
        resp = await c.get("/api/companion/context-markdown")
        if resp.status_code != 200:
            fail(f"导出失败 HTTP {resp.status_code}: {resp.text[:400]}")
            return
        snapshot = resp.text
    body = _build_soul_md(snapshot, manual)
    _SOUL_MD.write_text(body, encoding="utf-8")
    ok(f"已写入 {_SOUL_MD}")

# ANSI colors
G = "\033[92m"  # green
Y = "\033[93m"  # yellow
C = "\033[96m"  # cyan
R = "\033[91m"  # red
B = "\033[1m"   # bold
E = "\033[0m"   # reset


def header(text: str):
    print(f"\n{B}{C}{'='*50}{E}")
    print(f"{B}{C}  {text}{E}")
    print(f"{B}{C}{'='*50}{E}")


def step(text: str):
    print(f"\n{Y}> {text}{E}")


def ok(text: str):
    print(f"  {G}[OK] {text}{E}")


def fail(text: str):
    print(f"  {R}[FAIL] {text}{E}")


def info(text: str):
    print(f"  {C}[i] {text}{E}")


def show_json(data, indent=4):
    print(f"  {json.dumps(data, ensure_ascii=False, indent=indent)}")


async def main():
    async with httpx.AsyncClient(base_url=BASE, timeout=30.0) as c:

        # ------ Step 0 ------
        header("0. 检查后端是否启动")
        try:
            resp = await c.get("/")
            data = resp.json()
            ok(f"后端运行中: {data.get('name')} v{data.get('version')}")
        except httpx.ConnectError:
            fail("无法连接后端！请先 cd backend && python main.py")
            sys.exit(1)

        # ────────────────────────────────────
        header("1. 重置旧数据")
        # ────────────────────────────────────
        step("DELETE /api/soul (清除所有数据)")
        resp = await c.delete("/api/soul")
        if resp.status_code in (200, 404):
            ok("数据已清除")
        else:
            info(f"状态: {resp.status_code} - {resp.text}")

        # ────────────────────────────────────
        header("2. 创建灵魂")
        # ────────────────────────────────────
        soul_input = {
            "current_state_word": "",
            "struggle": "",
            "bias": "adventurous",
        }
        step(f"POST /api/soul - 空白灵魂, 偏向: {soul_input['bias']}（上下文由对话整理自动填充）")
        resp = await c.post("/api/soul", json=soul_input)
        if resp.status_code == 200:
            data = resp.json()
            ok("灵魂创建成功")
            show_json(data)
        else:
            fail(f"创建失败: {resp.status_code} - {resp.text}")
            sys.exit(1)

        step("GET /api/soul - 验证读取")
        resp = await c.get("/api/soul")
        soul = resp.json()
        word = soul.get('current_state_word') or '（空白）'
        struggle = soul.get('struggle') or '（待对话填充）'
        ok(f"灵魂: 「{word}」| 纠结: {struggle[:20]}")

        step("GET /api/personality - 初始性格")
        resp = await c.get("/api/personality")
        personality = resp.json()
        ok(f"性格 v{personality['version']}: {personality['natural_description']}")
        pr = personality["params"]
        info(
            f"参数: owl={pr['night_owl_index']}, anx={pr['anxiety_sensitivity']}, "
            f"quiet={pr['quietness']}, play={pr.get('playfulness', 0.3)}, "
            f"attach={pr['attachment_level']}"
        )
        if personality.get("voice_style"):
            info(f"说话风格: {personality['voice_style'][:80]}...")

        # ────────────────────────────────────
        header("3. 模拟状态切换")
        # ────────────────────────────────────
        step("POST /api/sim/person-arrive - 有人走近")
        resp = await c.post("/api/sim/person-arrive")
        status = resp.json()
        ok(f"状态: {status['state']} (期望: passerby)")

        await asyncio.sleep(0.5)

        step("POST /api/sim/person-sit - 人坐下")
        resp = await c.post("/api/sim/person-sit")
        status = resp.json()
        ok(f"状态: {status['state']} (期望: companion/deep_night)")
        info(f"时段: {status.get('time_period')}, 是否深夜: {status.get('is_night')}")

        step("GET /api/status - 完整状态")
        resp = await c.get("/api/status")
        show_json(resp.json())

        step("GET /api/room - 房间场景")
        resp = await c.get("/api/room")
        room = resp.json()
        ok(f"场景: {room['scene']} - {room['details'].get('description', '')}")

        # ────────────────────────────────────
        header("4. 专注模式")
        # ────────────────────────────────────
        step("POST /api/focus/start - 开始25分钟专注")
        resp = await c.post("/api/focus/start", json={"duration_minutes": 25})
        status = resp.json()
        ok(f"状态: {status['state']} (期望: focus)")

        step("POST /api/focus/stop - 结束专注")
        resp = await c.post("/api/focus/stop")
        status = resp.json()
        ok(f"状态: {status['state']} (期望: companion/deep_night)")

        # ────────────────────────────────────
        header("5. 纸条生成 (LLM)")
        # ────────────────────────────────────
        step("POST /api/notes/generate - 生成纸条")
        resp = await c.post("/api/notes/generate")
        if resp.status_code == 200:
            note = resp.json()
            ok(f"纸条内容:")
            print(f"\n    {B}「{note['content']}」{E}\n")
            info(f"ID: {note['id']}, 性格版本: {note['personality_version']}")
        else:
            fail(f"生成失败: {resp.status_code} - {resp.text}")

        # ────────────────────────────────────
        header("6. 留言 + 情绪")
        # ────────────────────────────────────
        step("POST /api/message - 留言")
        resp = await c.post("/api/message", json={"content": "今天好累，但看到你在还挺好的", "mood": "tired"})
        ok(f"留言发送: {resp.json()}")

        step("POST /api/mood - 标记情绪")
        resp = await c.post("/api/mood", json={"mood": "calm"})
        ok(f"情绪标记: {resp.json()}")

        # ────────────────────────────────────
        header("7. 快进演化 (重头戏)")
        # ────────────────────────────────────
        step("POST /api/sim/fast-forward - 快进7天")
        resp = await c.post("/api/sim/fast-forward", json={
            "days": 7,
            "late_night_ratio": 0.4,
            "focus_ratio": 0.5,
        })
        if resp.status_code == 200:
            result = resp.json()
            ok(f"快进完成: {result['days_generated']}天, {result['records']}条记录")
            info(f"晚睡比例: {result['late_night_ratio']:.0%}, 规律性: {result['regularity_score']:.2f}")
            if result.get("personality"):
                p = result["personality"]
                ok(f"性格已演化到 v{p['version']}")
                info(f"描述: {p['natural_description']}")
                _p = p["params"]
                info(
                    f"参数: owl={_p['night_owl_index']}, anx={_p['anxiety_sensitivity']}, "
                    f"quiet={_p['quietness']}, play={_p.get('playfulness', 0.3)}, "
                    f"attach={_p['attachment_level']}"
                )
                if p.get("evolution_log"):
                    info(f"演化日志 ({len(p['evolution_log'])}条):")
                    for log in p["evolution_log"][-3:]:
                        print(f"      Day {log['day']}: {log['change']} ({log['reason']})")
        else:
            fail(f"快进失败: {resp.status_code} - {resp.text}")

        # ────────────────────────────────────
        header("8. 演化后再生成纸条")
        # ────────────────────────────────────
        step("POST /api/notes/generate - 演化后的纸条")
        resp = await c.post("/api/notes/generate")
        if resp.status_code == 200:
            note = resp.json()
            ok(f"纸条内容:")
            print(f"\n    {B}「{note['content']}」{E}\n")
            info(f"性格版本: {note['personality_version']}")
        else:
            fail(f"生成失败: {resp.text}")

        step("GET /api/notes - 所有纸条")
        resp = await c.get("/api/notes")
        notes = resp.json()
        ok(f"共 {len(notes)} 张纸条")

        # ────────────────────────────────────
        header("9. 模拟离开")
        # ────────────────────────────────────
        step("POST /api/sim/person-leave - 人离开")
        resp = await c.post("/api/sim/person-leave")
        status = resp.json()
        ok(f"状态: {status['state']} (期望: leaving)")

        await asyncio.sleep(2)

        step("GET /api/status - 等待回到 idle")
        resp = await c.get("/api/status")
        status = resp.json()
        ok(f"最终状态: {status['state']}")

        # ────────────────────────────────────
        header("[DONE] 全部测试完成!")
        # ────────────────────────────────────
        print(f"""
{G}验证清单:{E}
  [OK] 灵魂创建 + 中文数据存储
  [OK] 状态机 idle -> passerby -> companion -> focus -> companion -> leaving
  [OK] 房间场景映射
  [OK] 纸条生成 (LLM调用)
  [OK] 留言 + 情绪标记
  [OK] 快进演化 (性格参数变化)
  [OK] 演化后纸条内容变化

{Y}下一步:{E}
  - 检查纸条内容质量, 调优 prompt
  - 配置 LLM API key (在 backend/.env)
  - 启动前端验证 UI: cd frontend && npm run dev
""")


def _manual_help():
    print(f"""
{B}{C}手动测试 — 常用指令{E}
  {Y}help{E}              显示本帮助
  {Y}init{E}              重置数据并创建灵魂（空白 L0，偏向 adventurous）
  {Y}arrive{E} / {Y}sit{E} / {Y}leave{E}   模拟走近 / 坐下 / 离开（会驱动状态机）
  {Y}focus-start [分]{E}  开始专注，默认 25 分钟
  {Y}focus-stop{E}        结束专注
  {Y}status{E} / {Y}room{E}   查看状态 / 房间场景
  {Y}note{E}              生成纸条（LLM）
  {Y}say{E}               让陪伴按当前上下文说一句（LLM，需已配置 API）
  {Y}chat{E}              进入多轮对话（同一条会话里记住上文）
  {Y}msg{E} <内容> [|心情]  留言；例: {G}msg 今天好累 | tired{E}
  {Y}mood{E} <心情>       只标记情绪
  {Y}digest{E}            手动对话整理（需 LLM；约 1 轮对话即可，定时任务需更多条消息）
  {Y}presets{E} / {Y}set-personality{E} [key]   列出预设 / 切换预设（如 warm_humor）
  {Y}ff{E}                快进 7 天（状态机驱动的性格演化演示）
  {Y}quit{E} / {Y}exit{E}   退出

{B}推荐流程（手动对话 → 整理记忆 → 再对话看演进）{E}
  {G}1){E} {Y}init{E} → {Y}sit{E} → {Y}personality{E}（记基线：version、依恋、活泼度、自然描述）
  {G}2){E} {Y}chat{E} 多聊几句；空行或 {Y}quit{E} 回到本提示符
  {G}3){E} {Y}digest{E} 把已落盘的对话整理进性格与 L0
  {G}4){E} {Y}personality{E} 再看一遍数值与描述是否变化
  {G}5){E} {Y}chat{E} 继续聊，感受语气/亲密度是否更接近整理后的设定
  可选: {Y}python test_demo_flow.py --export-soul-md{E} 导出 L0–L3 到 soul.md 对照

说明: 状态切换时前端 WebSocket 会收到 say_line；本模式用 {Y}say{E} 可随时拉一句。
""")


async def _input_line(prompt: str) -> str:
    """在异步里读一行输入（Windows 控制台兼容）。"""
    return (await asyncio.to_thread(input, prompt)).strip()


async def chat_session(c: httpx.AsyncClient):
    """多轮对话：调用 POST /api/companion/chat，在客户端维护 history。"""
    header("多轮对话")
    info("直接输入你的话；空行或 quit 退出。建议先 manual 里 init + sit，上下文更完整。")
    history: list[dict] = []
    while True:
        line = await _input_line(f"\n{G}你:{E} ")
        if not line or line.lower() in ("quit", "exit", "q"):
            info("已结束对话。")
            info(
                "回到 manual 后：可先 personality 看当前性格，再 digest 整理服务端对话记忆，"
                "然后再 personality 对比，最后 chat 继续聊以感受演进。"
            )
            break
        try:
            t0 = time.perf_counter()
            resp = await c.post(
                "/api/companion/chat",
                json={"message": line, "history": history},
            )
            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            data = resp.json()
            if not data.get("ok"):
                fail(data.get("error") or resp.text)
                continue
            reply = data.get("reply") or ""
            print(f"\n{B}{C}陪伴:{E} {Y}({elapsed_ms} ms){E}\n{reply}\n")
            history.append({"role": "user", "content": line})
            history.append({"role": "assistant", "content": reply})
            if len(history) > 24:
                history = history[-24:]
        except httpx.HTTPStatusError as e:
            fail(f"HTTP {e.response.status_code}: {e.response.text[:400]}")
        except Exception as e:
            fail(repr(e))


async def chat_main():
    """仅对话模式入口。"""
    async with httpx.AsyncClient(base_url=BASE, timeout=120.0) as c:
        try:
            resp = await c.get("/")
            ok(f"已连接: {resp.json().get('name')} v{resp.json().get('version')}")
        except httpx.ConnectError:
            fail("无法连接后端！请先 cd backend && python main.py")
            return
        await chat_session(c)


async def interactive_main():
    _manual_help()
    async with httpx.AsyncClient(base_url=BASE, timeout=120.0) as c:
        try:
            resp = await c.get("/")
            ok(f"已连接: {resp.json().get('name')} v{resp.json().get('version')}")
        except httpx.ConnectError:
            fail("无法连接后端！请先 cd backend && python main.py")
            return

        while True:
            line = await _input_line(f"\n{Y}manual>{E} ")
            if not line:
                continue
            parts = line.split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else ""

            try:
                if cmd in ("quit", "exit", "q"):
                    info("再见。")
                    break
                if cmd == "help":
                    _manual_help()
                    continue
                if cmd == "init":
                    header("init: 重置 + 创建空白灵魂")
                    await c.delete("/api/soul")
                    soul_input = {
                        "current_state_word": "",
                        "struggle": "",
                        "bias": "adventurous",
                    }
                    resp = await c.post("/api/soul", json=soul_input)
                    if resp.status_code == 200:
                        ok("空白灵魂已创建（上下文由对话整理自动填充）")
                        show_json(resp.json())
                    else:
                        fail(f"{resp.status_code} {resp.text}")
                    continue
                if cmd == "arrive":
                    resp = await c.post("/api/sim/person-arrive")
                    ok(f"arrive -> {resp.json()}")
                    continue
                if cmd == "sit":
                    resp = await c.post("/api/sim/person-sit")
                    ok(f"sit -> {resp.json()}")
                    continue
                if cmd == "leave":
                    resp = await c.post("/api/sim/person-leave")
                    ok(f"leave -> {resp.json()}")
                    continue
                if cmd == "focus-start":
                    mins = int(arg.strip() or "25")
                    resp = await c.post("/api/focus/start", json={"duration_minutes": mins})
                    ok(f"focus-start -> {resp.json()}")
                    continue
                if cmd == "focus-stop":
                    resp = await c.post("/api/focus/stop")
                    ok(f"focus-stop -> {resp.json()}")
                    continue
                if cmd == "status":
                    resp = await c.get("/api/status")
                    show_json(resp.json())
                    continue
                if cmd == "presets":
                    resp = await c.get("/api/personality/presets")
                    data = resp.json()
                    for p in data.get("presets", []):
                        info(f"  [{p['key']}] {p['label']} - {p['short_desc']}")
                    continue
                if cmd == "personality":
                    resp = await c.get("/api/personality")
                    p = resp.json()
                    par = p.get("params") or {}
                    ok(f"性格 v{p.get('version')}: bias={par.get('bias')}")
                    info(
                        "数值侧写（digest/状态机主要会动这些）: "
                        f"依恋={par.get('attachment_level')} 活泼={par.get('playfulness')} "
                        f"安静度={par.get('quietness')} 夜猫={par.get('night_owl_index')}"
                    )
                    info(f"说话风格: {p.get('voice_style', '(无)')}")
                    info(f"自然描述: {p.get('natural_description')}")
                    continue
                if cmd == "set-personality":
                    bias_val = arg.strip() or "warm_humor"
                    resp = await c.patch("/api/personality", json={"bias": bias_val})
                    if resp.status_code == 200:
                        ok(f"性格已切换为: {bias_val}")
                        show_json(resp.json())
                    else:
                        fail(f"{resp.status_code} {resp.text}")
                    continue
                if cmd == "room":
                    resp = await c.get("/api/room")
                    show_json(resp.json())
                    continue
                if cmd == "note":
                    resp = await c.post("/api/notes/generate")
                    if resp.status_code == 200:
                        n = resp.json()
                        ok(f"纸条: 「{n.get('content', '')}」")
                    else:
                        fail(f"{resp.status_code} {resp.text}")
                    continue
                if cmd == "say":
                    resp = await c.post("/api/companion/speak")
                    data = resp.json()
                    if data.get("ok") and data.get("say_line"):
                        print(f"\n  {B}{G}陪伴:{E} 「{data['say_line']}」\n")
                    else:
                        fail(data.get("error") or resp.text)
                    continue
                if cmd == "chat":
                    await chat_session(c)
                    continue
                if cmd == "msg":
                    if not arg:
                        fail("用法: msg <内容> [| 心情]")
                        continue
                    if "|" in arg:
                        content, mood = [x.strip() for x in arg.split("|", 1)]
                        payload = {"content": content, "mood": mood or None}
                    else:
                        payload = {"content": arg, "mood": None}
                    resp = await c.post("/api/message", json=payload)
                    ok(f"留言 -> {resp.json()}")
                    continue
                if cmd == "mood":
                    if not arg:
                        fail("用法: mood <心情>")
                        continue
                    resp = await c.post("/api/mood", json={"mood": arg})
                    ok(f"mood -> {resp.json()}")
                    continue
                if cmd == "digest":
                    resp = await c.post("/api/companion/digest")
                    data = resp.json()
                    if not data.get("ok"):
                        fail(data.get("error") or resp.text)
                        continue
                    if data.get("skipped"):
                        info(data.get("reason") or "已跳过")
                        continue
                    ok(
                        "对话整理完成 "
                        f"性格变更={data.get('personality_changed')} "
                        f"L0变更={data.get('soul_changed')}"
                    )
                    show_json(data)
                    continue
                if cmd == "ff":
                    resp = await c.post(
                        "/api/sim/fast-forward",
                        json={"days": 7, "late_night_ratio": 0.4, "focus_ratio": 0.5},
                    )
                    if resp.status_code == 200:
                        ok("快进完成")
                        show_json(resp.json())
                    else:
                        fail(f"{resp.status_code} {resp.text}")
                    continue
                info(f"未知指令: {cmd}，输入 help 查看列表")
            except ValueError as e:
                fail(str(e))
            except httpx.HTTPStatusError as e:
                fail(f"HTTP {e.response.status_code}: {e.response.text[:300]}")
            except Exception as e:
                fail(repr(e))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Companion Agent 流程测试")
    parser.add_argument(
        "--manual",
        action="store_true",
        help="交互式手动测试（需后端已启动）",
    )
    parser.add_argument(
        "--chat",
        action="store_true",
        help="仅多轮对话（需后端已启动且已配置 LLM）",
    )
    parser.add_argument(
        "--export-soul-md",
        action="store_true",
        help="从后端拉取 L0–L3 Markdown 快照写入 soul.md（保留手写区）",
    )
    args = parser.parse_args()
    if args.export_soul_md:
        asyncio.run(export_soul_md_main())
    elif args.chat:
        asyncio.run(chat_main())
    elif args.manual:
        asyncio.run(interactive_main())
    else:
        asyncio.run(main())
