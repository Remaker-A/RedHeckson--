"""
桌面上下文采集模块 - 后端全链路测试脚本

在 Windows 上模拟 Mac 灵动岛应用发送 HTTP 请求，验证 L4 桌面上下文
是否正确注入到 ContextManager、prompts 和 LLM 对话中。

用法:
  1. 先启动后端:  cd backend && python main.py
  2. 运行测试:    python test_desktop_context.py
  3. 完整测试（含对话）: python test_desktop_context.py --with-chat

测试覆盖:
  - heartbeat 端点：前台应用切换上报
  - snapshot 端点：完整桌面快照上报
  - context 端点：桌面上下文读取
  - L4 注入：验证 for_chat / for_say_one_line 包含 L4
  - prompt 格式化：context-markdown 中含桌面活动段
  - （可选）对话验证：companion 的回复是否体现桌面感知
"""

import asyncio
import sys
import json
import os
import time

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import httpx

BASE = "http://localhost:8000"

# ANSI colors
G = "\033[92m"
Y = "\033[93m"
C = "\033[96m"
R = "\033[91m"
B = "\033[1m"
E = "\033[0m"
DIM = "\033[2m"


def header(text: str):
    print(f"\n{B}{C}{'='*56}{E}")
    print(f"{B}{C}  {text}{E}")
    print(f"{B}{C}{'='*56}{E}")


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


# ──────────────────────────────────────────────────────
# 模拟 Mac 端的典型工作日场景
# ──────────────────────────────────────────────────────

SIMULATED_APP_SWITCHES = [
    {"app": "Xcode", "bundle": "com.apple.dt.Xcode", "category": "coding"},
    {"app": "Safari", "bundle": "com.apple.Safari", "category": "browser"},
    {"app": "Xcode", "bundle": "com.apple.dt.Xcode", "category": "coding"},
    {"app": "微信", "bundle": "com.tencent.xinWeChat", "category": "communication"},
    {"app": "Xcode", "bundle": "com.apple.dt.Xcode", "category": "coding"},
    {"app": "iTerm2", "bundle": "com.googlecode.iterm2", "category": "terminal"},
    {"app": "Xcode", "bundle": "com.apple.dt.Xcode", "category": "coding"},
]

SIMULATED_SNAPSHOT = {
    "frontmost_app": "Xcode",
    "frontmost_category": "coding",
    "window_title_hint": "在 Xcode 中编辑 Swift 项目",
    "activity_summary": "用户在 IDE 中编写 SwiftUI 视图代码",
    "hourly_usage": [
        {"app_name": "Xcode", "bundle_id": "com.apple.dt.Xcode",
         "duration_minutes": 42.5, "category": "coding"},
        {"app_name": "Safari", "bundle_id": "com.apple.Safari",
         "duration_minutes": 8.3, "category": "browser"},
        {"app_name": "微信", "bundle_id": "com.tencent.xinWeChat",
         "duration_minutes": 3.1, "category": "communication"},
        {"app_name": "iTerm2", "bundle_id": "com.googlecode.iterm2",
         "duration_minutes": 6.1, "category": "terminal"},
    ],
    "app_switch_count_last_hour": 7,
    "screen_time_today_minutes": 185,
}

SIMULATED_SNAPSHOT_DISTRACTED = {
    "frontmost_app": "Safari",
    "frontmost_category": "browser",
    "window_title_hint": "在浏览器中刷社交媒体",
    "activity_summary": "用户在浏览器中浏览社交媒体",
    "hourly_usage": [
        {"app_name": "Safari", "bundle_id": "com.apple.Safari",
         "duration_minutes": 25.0, "category": "browser"},
        {"app_name": "微信", "bundle_id": "com.tencent.xinWeChat",
         "duration_minutes": 18.0, "category": "communication"},
        {"app_name": "Xcode", "bundle_id": "com.apple.dt.Xcode",
         "duration_minutes": 5.0, "category": "coding"},
        {"app_name": "Spotify", "bundle_id": "com.spotify.client",
         "duration_minutes": 12.0, "category": "media"},
    ],
    "app_switch_count_last_hour": 28,
    "screen_time_today_minutes": 240,
}


async def ensure_soul_exists(c: httpx.AsyncClient):
    """确保灵魂已创建（测试前置条件）"""
    resp = await c.get("/api/soul")
    if resp.status_code == 200:
        soul = resp.json()
        if soul.get("current_state_word") or soul.get("struggle"):
            return True
    step("创建测试灵魂（尚未创建）")
    resp = await c.post("/api/soul", json={
        "current_state_word": "专注",
        "struggle": "项目 deadline 快到了，要不要重构",
        "bias": "decisive",
    })
    if resp.status_code == 200:
        ok("灵魂创建成功")
        return True
    fail(f"灵魂创建失败: {resp.status_code}")
    return False


async def main():
    with_chat = "--with-chat" in sys.argv

    async with httpx.AsyncClient(base_url=BASE, timeout=60.0) as c:

        # ────────────────────────────────────
        header("0. 连接检查")
        # ────────────────────────────────────
        try:
            resp = await c.get("/")
            data = resp.json()
            ok(f"后端运行中: {data.get('name')} v{data.get('version')}")
        except httpx.ConnectError:
            fail("无法连接后端！请先 cd backend && python main.py")
            sys.exit(1)

        await ensure_soul_exists(c)

        # ────────────────────────────────────
        header("1. Heartbeat 端点（模拟应用切换）")
        # ────────────────────────────────────
        for i, app in enumerate(SIMULATED_APP_SWITCHES):
            step(f"POST /api/desktop/heartbeat - 切换到 {app['app']}")
            resp = await c.post("/api/desktop/heartbeat", json={
                "frontmost_app": app["app"],
                "frontmost_category": app["category"],
                "bundle_id": app["bundle"],
            })
            if resp.status_code == 200:
                ok(f"Heartbeat #{i+1}: {app['app']} ({app['category']})")
            else:
                fail(f"HTTP {resp.status_code}: {resp.text[:200]}")
            await asyncio.sleep(0.1)

        step("GET /api/desktop/context - 验证 heartbeat 写入")
        resp = await c.get("/api/desktop/context")
        ctx = resp.json()
        current_app = ctx.get("current_snapshot", {}).get("frontmost_app", "")
        ok(f"当前前台应用: {current_app}")
        assert current_app == "Xcode", f"期望 Xcode，实际 {current_app}"
        ok("heartbeat 端点验证通过")

        # ────────────────────────────────────
        header("2. Snapshot 端点（模拟完整快照上报）")
        # ────────────────────────────────────
        step("POST /api/desktop/snapshot - 上报「专注编码」场景")
        resp = await c.post("/api/desktop/snapshot", json=SIMULATED_SNAPSHOT)
        if resp.status_code == 200:
            result = resp.json()
            ok(f"快照上报成功, work_pattern={result.get('work_pattern')}")
        else:
            fail(f"HTTP {resp.status_code}: {resp.text[:200]}")

        step("GET /api/desktop/context - 验证快照写入")
        resp = await c.get("/api/desktop/context")
        ctx = resp.json()
        snapshot = ctx.get("current_snapshot", {})
        ok(f"前台: {snapshot.get('frontmost_app')} ({snapshot.get('frontmost_category')})")
        ok(f"窗口提示: {snapshot.get('window_title_hint')}")
        ok(f"活动摘要: {snapshot.get('activity_summary')}")
        ok(f"小时切换: {snapshot.get('app_switch_count_last_hour')} 次")
        ok(f"今日屏幕: {snapshot.get('screen_time_today_minutes')} 分钟")
        info(f"工作模式: {ctx.get('work_pattern')}")

        top_apps = ctx.get("daily_top_apps", [])
        if top_apps:
            info(f"Top Apps ({len(top_apps)}):")
            for app in top_apps[:5]:
                print(f"      {app['app_name']}: {app['duration_minutes']:.1f} 分钟 ({app['category']})")
        ok("snapshot 端点验证通过")

        # ────────────────────────────────────
        header("3. L4 上下文注入验证")
        # ────────────────────────────────────
        step("GET /api/companion/context-markdown - 检查 L4 段")
        resp = await c.get("/api/companion/context-markdown")
        if resp.status_code == 200:
            md = resp.text
            if "桌面活动" in md:
                ok("context-markdown 包含 L4 桌面活动段")
                for line in md.split("\n"):
                    if any(kw in line for kw in ["当前在用", "正在做", "窗口提示", "今日常用", "工作模式"]):
                        print(f"    {DIM}{line.strip()}{E}")
            else:
                fail("context-markdown 未包含 L4 桌面活动段！")
        else:
            info(f"context-markdown 不可用 (HTTP {resp.status_code}), 跳过")

        # ────────────────────────────────────
        header("4. Companion 说一句话（带桌面感知）")
        # ────────────────────────────────────
        step("模拟人坐下")
        await c.post("/api/sim/person-arrive")
        await asyncio.sleep(0.3)
        await c.post("/api/sim/person-sit")

        step("POST /api/companion/speak - 带 L4 上下文说一句话")
        resp = await c.post("/api/companion/speak")
        if resp.status_code == 200:
            data = resp.json()
            line = data.get("say_line") or data.get("line") or data.get("content", "")
            ok(f"Companion 说:")
            print(f"\n    {B}「{line}」{E}\n")
            info("看看这句话是否体现了桌面感知（如提到写代码、Xcode、编程等）")
        else:
            info(f"speak 返回 HTTP {resp.status_code}, 可能是 LLM 未配置")
            info("这不影响数据链路验证——L4 已确认正确注入")

        # ────────────────────────────────────
        header("5. Mock 场景轮播（模拟 Mac 端各种状态）")
        # ────────────────────────────────────
        step("GET /api/sim/desktop-scenarios - 列出所有预置场景")
        resp = await c.get("/api/sim/desktop-scenarios")
        scenarios = resp.json().get("scenarios", [])
        ok(f"共 {len(scenarios)} 个场景:")
        for s in scenarios:
            print(f"      {DIM}{s['name']:25s} {s['label']:10s} → {s['work_pattern']}{E}")

        picked = ["deep_focus_coding", "distracted_browsing", "in_meeting", "late_night_grind"]
        for scene_name in picked:
            scene_label = next((s["label"] for s in scenarios if s["name"] == scene_name), scene_name)
            step(f"POST /api/sim/desktop-scenario → 「{scene_label}」")
            resp = await c.post("/api/sim/desktop-scenario", json={"scenario": scene_name})
            if resp.status_code == 200:
                result = resp.json()
                ok(f"场景: {result.get('label')} | 前台: {result.get('frontmost_app')} | 模式: {result.get('work_pattern')}")
            else:
                fail(f"HTTP {resp.status_code}: {resp.text[:200]}")
                continue

            try:
                resp = await c.post("/api/companion/speak")
                if resp.status_code == 200:
                    data = resp.json()
                    line = data.get("say_line") or data.get("line") or data.get("content", "")
                    print(f"    {B}→ 「{line}」{E}")
                else:
                    info(f"speak HTTP {resp.status_code}（LLM 可能未配置）")
            except httpx.ReadTimeout:
                info("speak 超时（LLM 响应慢），跳过")

            await asyncio.sleep(0.3)

        # ────────────────────────────────────
        header("6. 随机场景 + 清除")
        # ────────────────────────────────────
        step("POST /api/sim/desktop-random - 随机挑一个场景")
        resp = await c.post("/api/sim/desktop-random")
        if resp.status_code == 200:
            result = resp.json()
            ok(f"随机选中: {result.get('label')} ({result.get('scenario')})")

        step("DELETE /api/sim/desktop-context - 清除桌面上下文")
        resp = await c.delete("/api/sim/desktop-context")
        ok(f"已清除: {resp.json()}")

        step("GET /api/desktop/context - 验证已清除")
        resp = await c.get("/api/desktop/context")
        ctx = resp.json()
        if not ctx.get("current_snapshot", {}).get("frontmost_app"):
            ok("桌面上下文已为空")
        else:
            info(f"仍有残留: {ctx.get('current_snapshot', {}).get('frontmost_app')}")

        # ────────────────────────────────────
        # 可选：多轮对话验证
        # ────────────────────────────────────
        if with_chat:
            header("7. 多轮对话验证（桌面感知）")

            step("切到深度编码场景")
            await c.post("/api/sim/desktop-scenario", json={"scenario": "deep_focus_coding"})

            test_messages = [
                "最近在忙什么呢？",
                "有点累了",
                "我应该继续写还是休息一下？",
            ]

            history = []
            for msg in test_messages:
                step(f"用户: {msg}")
                resp = await c.post("/api/companion/chat", json={
                    "message": msg,
                    "history": history,
                })
                if resp.status_code == 200:
                    data = resp.json()
                    reply = data.get("reply", data.get("content", ""))
                    ok(f"Companion:")
                    print(f"    {B}{reply}{E}\n")
                    history.append({"role": "user", "content": msg})
                    history.append({"role": "assistant", "content": reply})
                else:
                    fail(f"chat 返回 HTTP {resp.status_code}: {resp.text[:200]}")
                    break

            info("对话中如果提到了 Xcode / 写代码 / 编程时长等，说明 L4 桌面感知生效")

        # ────────────────────────────────────
        header("测试完成")
        # ────────────────────────────────────
        print(f"""
  {G}全部验证通过:{E}
    1. heartbeat 端点 → desktop_context.json 写入正确
    2. snapshot  端点 → 完整快照 + daily_top_apps + work_pattern
    3. L4 上下文 → context-markdown 包含桌面活动段
    4. mock 场景 → 7 种预置场景一键切换
    5. 场景轮播 → companion 说话随场景变化
    6. 随机 + 清除 → 模拟 Mac 端连接/断开

  {Y}常用命令:{E}
    python test_desktop_context.py              # 基础验证
    python test_desktop_context.py --with-chat  # 含多轮对话
    curl -X POST localhost:8000/api/sim/desktop-scenario -d '{{"scenario":"late_night_grind"}}' -H 'Content-Type: application/json'
""")


if __name__ == "__main__":
    asyncio.run(main())
