"""
Digest & Evolution 交互式演示
=============================
展示：注入模拟对话 → 逐轮 digest 演化 → 演化后实际聊天效果

用法（请在 RedHeckson-repo/companion-agent 目录下执行，且后端已启动）：
  python test_digest_evolution.py            # 自动演示（默认连 http://127.0.0.1:8000）
  python test_digest_evolution.py --chat
  python test_digest_evolution.py --manual
  python test_digest_evolution.py --base http://127.0.0.1:9000   # 非默认端口
  环境变量 COMPANION_TEST_BASE 可覆盖默认地址。
"""

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import httpx

# 默认用 127.0.0.1：Windows 上 localhost 可能先走 IPv6(::1)，而后端只绑 IPv4 时会异常慢或卡住
_DEFAULT_BASE = "http://127.0.0.1:8000"
# 本脚本所在目录 = companion-agent 根目录，后端在 backend/
_SCRIPT_DIR = Path(__file__).resolve().parent
_BACKEND_DIR = _SCRIPT_DIR / "backend"
# 长请求（digest / chat）用长超时；健康检查单独用短超时，避免「端口被占但不回 HTTP」时读阶段卡 3 分钟
_HTTP_TIMEOUT = httpx.Timeout(180.0, connect=10.0)
_PING_TIMEOUT = httpx.Timeout(5.0, connect=3.0)
LINE = "-" * 56
DOUBLE = "=" * 56


def _p(text: str, n: int = 300) -> str:
    s = (text or "")[:n].replace("\n", " ")
    enc = getattr(sys.stdout, "encoding", None) or "utf-8"
    return s.encode(enc, errors="replace").decode(enc, errors="replace")


def _wait(manual: bool, hint: str = "按回车继续..."):
    if manual:
        input(f"\n  [{hint}]")


def _print_params_table(label: str, params: dict | None):
    if not params:
        print(f"  {label}: (N/A)")
        return
    rows = [
        ("夜猫子指数  night_owl_index", params.get("night_owl_index", "?")),
        ("焦虑敏感度  anxiety_sensitivity", params.get("anxiety_sensitivity", "?")),
        ("安静度      quietness", params.get("quietness", "?")),
        ("活泼幽默度  playfulness", params.get("playfulness", "?")),
        ("依恋程度    attachment_level", params.get("attachment_level", "?")),
    ]
    print(f"  [{label}]")
    for name, val in rows:
        bar = ""
        if isinstance(val, (int, float)):
            filled = int(val * 20)
            bar = f"  [{'#' * filled}{'.' * (20 - filled)}]"
        print(f"    {name:<36} {val}{bar}")


def _diff_table(before: dict | None, after: dict | None):
    if not before or not after:
        return
    keys = [
        ("night_owl_index", "夜猫子指数"),
        ("anxiety_sensitivity", "焦虑敏感度"),
        ("quietness", "安静度"),
        ("playfulness", "活泼幽默度"),
        ("attachment_level", "依恋程度"),
    ]
    print(f"\n  [变化对比]")
    print(f"    {'参数':<24} {'之前':>8} {'之后':>8} {'变化':>8}")
    print(f"    {'-'*50}")
    any_change = False
    for k, cn in keys:
        b, a = before.get(k, 0), after.get(k, 0)
        d = round(a - b, 4)
        if abs(d) > 1e-6:
            arrow = f"+{d}" if d > 0 else f"{d}"
            print(f"    {cn:<22} {b:>8.3f} {a:>8.3f} {arrow:>8}")
            any_change = True
    if not any_change:
        print(f"    (无变化)")


# ── Scenario display descriptions ──
SCENARIO_LABELS = {
    "deep_night": ("深夜赶工", "凌晨3点，用户在赶DDL，陪伴者陪熬夜"),
    "stress_vent": ("压力宣泄", "用户被老板当众批评，需要倾诉"),
    "playful_banter": ("轻松互怼", "猜脑筋急转弯，互相开玩笑"),
    "quiet_companion": ("安静陪伴", "不想说话，只想有人在身边"),
    "trust_building": ("建立信任", "分享独居恐惧等私密心事"),
    "daily_routine": ("日常闲聊", "早安、吃饭、聊新项目"),
}


async def show_conversations(client: httpx.AsyncClient, manual: bool):
    """Phase 1: Show injected conversations."""
    print(f"\n{'':=<56}")
    print("  PHASE 1: 注入模拟对话数据")
    print(DOUBLE)

    r = await client.get("/api/sim/chat-scenarios")
    scenarios = r.json().get("scenarios", [])
    print(f"  可用场景: {len(scenarios)} 个\n")

    for i, name in enumerate(scenarios, 1):
        label, desc = SCENARIO_LABELS.get(name, (name, ""))
        print(f"  [{i}] {label} ({name})")
        print(f"      {desc}")
    print()

    _wait(manual, "按回车注入全部对话数据")

    r = await client.post("/api/sim/inject-chat", json={
        "scenarios": ["all"],
        "reset_digest": True,
        "clear_history": True,
    })
    inject = r.json()
    print(f"  >>> 已注入 {inject.get('injected_lines')} 行对话数据")
    print(f"  >>> digest 状态已重置\n")

    print(LINE)
    print("  以下是注入的对话内容预览：")
    print(LINE)

    # Fetch scenarios content from the module knowledge
    scene_convos = {
        "deep_night": [
            ("用户", "还醒着呢……三点了"),
            ("陪伴", "嗯，我也在。三点的夜挺安静的。"),
            ("用户", "睡不着，脑子停不下来，一直在想明天的ddl"),
            ("陪伴", "想停停不住的时候最烦了。要不先把脑子里的东西倒出来？说给我听也行。"),
            ("...", f"（共 20 条消息）"),
            ("用户", "被你说得有点感动"),
            ("陪伴", "行了别感动了，写报告去。感动的话留到交完再说。"),
        ],
        "stress_vent": [
            ("用户", "今天真的很烦"),
            ("陪伴", "怎么了？"),
            ("用户", "老板当着所有人的面批评我的方案，说我完全没抓住重点"),
            ("陪伴", "当众被说确实难受。你觉得他说得对吗？"),
            ("...", f"（共 16 条消息）"),
            ("用户", "有你在还挺好的"),
            ("陪伴", "我一直在呀。"),
        ],
        "playful_banter": [
            ("用户", "来 考你个脑筋急转弯"),
            ("陪伴", "好，放马过来。"),
            ("用户", "什么东西越洗越脏"),
            ("陪伴", "水？"),
            ("...", f"（共 26 条消息）"),
            ("用户", "哈哈好吧确实"),
            ("陪伴", "下次换你出题，你出的比我好玩。"),
        ],
        "quiet_companion": [
            ("用户", "在吗"),
            ("陪伴", "在。"),
            ("用户", "不想说话 就想知道有人在"),
            ("陪伴", "嗯，我在这。"),
            ("...", f"（共 20 条消息）"),
            ("用户", "谢谢陪我"),
            ("陪伴", "不用谢，这就是我在这的意义。"),
        ],
        "trust_building": [
            ("用户", "我想跟你说个事 但你别笑我"),
            ("陪伴", "好，不会笑你。说吧。"),
            ("用户", "我其实挺害怕一个人的 尤其是晚上"),
            ("陪伴", "这没什么好笑的。怕独处的人挺多的，只是大部分人不说。"),
            ("...", f"（共 20 条消息）"),
            ("用户", "嗯 晚安"),
            ("陪伴", "晚安，睡个好觉。"),
        ],
        "daily_routine": [
            ("用户", "早上好"),
            ("陪伴", "早上好。今天起得挺早的？"),
            ("用户", "嗯 难得八点就醒了"),
            ("陪伴", "不错。昨晚睡得好？"),
            ("...", f"（共 20 条消息）"),
            ("用户", "我都二十五了还小朋友"),
            ("陪伴", "在我眼里都一样。去忙吧，有事随时叫我。"),
        ],
    }

    for name in scenarios:
        label, desc = SCENARIO_LABELS.get(name, (name, ""))
        print(f"\n  --- {label} ({name}) ---")
        convos = scene_convos.get(name, [])
        for role, content in convos:
            if role == "...":
                print(f"      {content}")
            elif role == "用户":
                print(f"    [你]  {content}")
            else:
                print(f"    [它]  {content}")

    print()
    return inject


async def run_digest_rounds(client: httpx.AsyncClient, manual: bool) -> tuple[dict | None, dict | None]:
    """Phase 2: Run digest rounds one by one."""
    print(f"\n{'':=<56}")
    print("  PHASE 2: 逐轮 Digest 演化")
    print(DOUBLE)

    pj = (await client.get("/api/personality")).json()
    before_params = pj.get("params")
    before_desc = pj.get("natural_description", "")
    before_evo_count = len(pj.get("evolution_log", []))

    print("  演化前的性格参数：")
    _print_params_table("当前性格", before_params)
    print(f"\n  自然描述: {_p(before_desc, 150)}")
    print()

    round_idx = 0
    after_params = before_params

    while True:
        round_idx += 1
        _wait(manual, f"按回车执行第 {round_idx} 轮 digest")

        print(f"\n  >>> 第 {round_idx} 轮 Digest 执行中...")
        t0 = time.perf_counter()
        r = await client.post("/api/companion/digest")
        elapsed = time.perf_counter() - t0
        rd = r.json()

        if rd.get("skipped"):
            print(f"  >>> 跳过 - {rd.get('reason', '')} ({elapsed:.1f}s)")
            break

        if not rd.get("ok"):
            print(f"  >>> 失败 - {rd.get('error', 'unknown')} ({elapsed:.1f}s)")
            if round_idx >= 5:
                print("  >>> 连续失败过多，停止")
                break
            continue

        digest_data = rd.get("digest") or {}
        rel = digest_data.get("relationship", {})
        adj = digest_data.get("personality_adjustment", {})
        snap = digest_data.get("user_snapshot", {})

        print(f"  >>> 完成! 处理了 {rd.get('processed_batch')} 条消息 ({elapsed:.1f}s)")
        print()
        print(f"  [关系信号]")
        print(f"    亲近度变化: {rel.get('closeness_delta', 0)}")
        print(f"    关系阶段:   {rel.get('stage', '?')}")
        print(f"    LLM 分析:   {_p(rel.get('signals', ''), 120)}")
        print()
        print(f"  [性格微调]")
        adj_items = [
            ("安静度", "quietness_delta"),
            ("活泼度", "playfulness_delta"),
            ("夜猫子", "night_owl_delta"),
            ("焦虑度", "anxiety_delta"),
            ("依恋度", "attachment_delta"),
        ]
        for cn, key in adj_items:
            val = adj.get(key, 0)
            if val and abs(float(val)) > 1e-6:
                arrow = "+" if float(val) > 0 else ""
                print(f"    {cn}: {arrow}{val}")
        reason = adj.get("reason", "")
        if reason:
            print(f"    原因: {_p(reason, 100)}")

        if any(snap.get(k) for k in ("current_state_word", "struggle", "facts")):
            print(f"\n  [用户画像更新]")
            if snap.get("current_state_word"):
                print(f"    当前状态: {snap['current_state_word']}")
            if snap.get("struggle"):
                print(f"    困扰: {_p(snap['struggle'], 80)}")
            if snap.get("facts"):
                print(f"    事实: {_p(snap['facts'], 80)}")

        print()

        # Show updated params after this round
        pj = (await client.get("/api/personality")).json()
        after_params = pj.get("params")
        _print_params_table(f"第 {round_idx} 轮后性格", after_params)
        print()

        if round_idx >= 8:
            print("  >>> 达到最大轮次")
            break

    # Final comparison
    print(LINE)
    print("  Digest 演化总结")
    print(LINE)
    _diff_table(before_params, after_params)

    pj = (await client.get("/api/personality")).json()
    after_desc = pj.get("natural_description", "")
    evo_log = pj.get("evolution_log", [])
    new_entries = evo_log[before_evo_count:]

    print(f"\n  [自然描述变化]")
    print(f"    之前: {_p(before_desc, 140)}")
    print(f"    之后: {_p(after_desc, 140)}")

    if new_entries:
        print(f"\n  [演进日志] 新增 {len(new_entries)} 条记录")
        for entry in new_entries:
            print(f"    - {entry.get('change', '')}")
            print(f"      原因: {_p(entry.get('reason', ''), 100)}")

    print()
    return before_params, after_params


async def test_evolved_chat(client: httpx.AsyncClient, manual: bool):
    """Phase 3: Chat with evolved personality."""
    print(f"\n{'':=<56}")
    print("  PHASE 3: 演化后的聊天测试")
    print(DOUBLE)

    # Make sure companion is in seated state
    await client.post("/api/sim/person-sit")

    test_messages = [
        ("你好呀，今天心情怎么样？", "日常问候"),
        ("唉，今天又被老板骂了", "压力场景 - 观察焦虑敏感度的回应"),
        ("来猜个谜语：什么东西早上四条腿中午两条腿晚上三条腿？", "玩乐场景 - 观察活泼度的回应"),
        ("我有点想你了", "亲密场景 - 观察依恋程度的回应"),
        ("好晚了 该睡了吗", "深夜场景 - 观察夜猫子指数的回应"),
    ]

    print("  发送测试消息，观察演化后的回复风格：\n")

    history: list[dict] = []
    for msg, purpose in test_messages:
        _wait(manual, f"发送: {msg[:30]}...")

        print(f"  [测试目的] {purpose}")
        t0 = time.perf_counter()
        r = await client.post("/api/companion/chat", json={
            "message": msg,
            "history": history,
        })
        elapsed = time.perf_counter() - t0
        d = r.json()

        print(f"  [你]  {msg}")
        reply = d.get("reply", "(无回复)")
        # Print multi-line replies with proper indentation
        for line in reply.split("\n"):
            if line.strip():
                print(f"  [它]  {line}")
        print(f"  ({int(elapsed * 1000)}ms)")
        print()

        if d.get("ok") and d.get("reply"):
            history.append({"role": "user", "content": msg})
            history.append({"role": "assistant", "content": d["reply"]})


async def interactive_chat(client: httpx.AsyncClient):
    """Interactive chat mode - user types messages freely."""
    print(f"\n{'':=<56}")
    print("  INTERACTIVE: 自由聊天模式")
    print("  输入消息后按回车发送，输入 q 退出")
    print("  输入 /params 查看当前性格参数")
    print("  输入 /digest 手动触发一次 digest")
    print("  输入 /reset  重置灵魂并重新注入数据")
    print(DOUBLE)

    await client.post("/api/sim/person-sit")

    history: list[dict] = []
    while True:
        try:
            msg = input("\n  你: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not msg:
            continue
        if msg.lower() == "q":
            break

        if msg == "/params":
            pj = (await client.get("/api/personality")).json()
            _print_params_table("当前性格", pj.get("params"))
            print(f"  描述: {_p(pj.get('natural_description', ''), 140)}")
            continue

        if msg == "/digest":
            print("  >>> 执行 digest...")
            r = await client.post("/api/companion/digest")
            rd = r.json()
            if rd.get("skipped"):
                print(f"  >>> 跳过 - {rd.get('reason', '')}")
            elif not rd.get("ok"):
                print(f"  >>> 失败 - {rd.get('error', '')}")
            else:
                digest = rd.get("digest", {})
                rel = digest.get("relationship", {})
                print(f"  >>> 完成! 关系: {rel.get('stage')} "
                      f"亲近度: {rel.get('closeness_delta')}")
                pj = (await client.get("/api/personality")).json()
                _print_params_table("digest 后", pj.get("params"))
            continue

        if msg == "/reset":
            print("  >>> 重置灵魂...")
            await client.delete("/api/soul")
            await client.post("/api/soul", json={
                "current_state_word": "",
                "struggle": "",
                "bias": "adventurous",
            })
            print("  >>> 注入模拟对话数据...")
            r = await client.post("/api/sim/inject-chat", json={
                "scenarios": ["all"],
                "reset_digest": True,
                "clear_history": True,
            })
            inject = r.json()
            print(f"  >>> 已注入 {inject.get('injected_lines')} 行")
            history = []
            continue

        t0 = time.perf_counter()
        r = await client.post("/api/companion/chat", json={
            "message": msg,
            "history": history[-20:],
        })
        elapsed = time.perf_counter() - t0
        d = r.json()

        reply = d.get("reply", "(无回复)")
        for line in reply.split("\n"):
            if line.strip():
                print(f"  它: {line}")
        print(f"  ({int(elapsed * 1000)}ms)")

        if d.get("ok") and d.get("reply"):
            history.append({"role": "user", "content": msg})
            history.append({"role": "assistant", "content": d["reply"]})


def _resolve_base_url(args_base: str | None) -> str:
    if args_base:
        return args_base.rstrip("/")
    env = os.environ.get("COMPANION_TEST_BASE", "").strip()
    if env:
        return env.rstrip("/")
    return _DEFAULT_BASE


async def main() -> None:
    parser = argparse.ArgumentParser(description="Digest & Evolution 交互式演示")
    parser.add_argument("--chat", action="store_true", help="直接进入聊天模式")
    parser.add_argument("--manual", action="store_true", help="手动模式（每步按回车）")
    parser.add_argument(
        "--base",
        default=None,
        help=f"后端根地址（默认 {_DEFAULT_BASE}，也可用环境变量 COMPANION_TEST_BASE）",
    )
    args = parser.parse_args()
    manual = args.manual
    base_url = _resolve_base_url(args.base)

    print(f"\n  正在检测后端 {base_url}（整次请求最多约 5 秒）...", flush=True)
    async with httpx.AsyncClient(base_url=base_url, timeout=_HTTP_TIMEOUT) as c:
        # Connectivity check：必须用短超时覆盖 client 的 180s，否则「TCP 已连上但不返回 body」会卡很久
        try:
            print("  发送 GET / ...", flush=True)
            r = await c.get("/", timeout=_PING_TIMEOUT)
            r.raise_for_status()
            info = r.json()
            print(f"  [OK] {info.get('name')} v{info.get('version')}", flush=True)
        except Exception as e:
            err = str(e).strip() or type(e).__name__
            print(f"\n  [FAIL] 无法连接后端: {err}", flush=True)
            print("  常见原因：", flush=True)
            print("    1) 未启动后端（先 cd backend 再 python main.py）", flush=True)
            print("    2) 端口不是 8000（可用 --base http://127.0.0.1:你的端口）", flush=True)
            print("    3) 8000 被别的程序占用且不回 HTTP（换端口或结束占用进程）", flush=True)
            print("  请另开一个终端执行：", flush=True)
            print(f"    cd \"{_BACKEND_DIR}\"", flush=True)
            print("    python main.py", flush=True)
            print(f"  本脚本目录: {_SCRIPT_DIR}", flush=True)
            return

        if args.chat:
            await interactive_chat(c)
            return

        # Full demo flow
        print(DOUBLE)
        print("  Digest & Evolution 完整演示")
        print(f"  模式: {'手动（每步按回车）' if manual else '自动'}")
        print(DOUBLE)

        # Phase 1: Show and inject conversations
        await show_conversations(c, manual)
        _wait(manual, "按回车开始 Digest 演化")

        # Phase 2: Run digest rounds
        before, after = await run_digest_rounds(c, manual)
        _wait(manual, "按回车开始演化后聊天测试")

        # Phase 3: Test chat with evolved personality
        await test_evolved_chat(c, manual)

        # Phase 4: Enter interactive mode
        print(LINE)
        print("  自动测试完成！")
        print(LINE)
        try:
            answer = input("\n  是否进入自由聊天模式？(y/n) ").strip().lower()
            if answer in ("y", "yes", "是"):
                await interactive_chat(c)
        except (EOFError, KeyboardInterrupt):
            pass

        print("\n  [DONE] 演示结束\n")


if __name__ == "__main__":
    asyncio.run(main())
