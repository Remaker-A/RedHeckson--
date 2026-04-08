"""升级后对话冒烟：空白灵魂 + warm_humor + 入座 + 多轮 chat + digest。"""
import asyncio
import json
import os
import sys
import time

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import httpx

BASE = "http://localhost:8000"


def _preview(text: str, n: int = 180) -> str:
    s = (text or "")[:n].replace("\n", " ")
    enc = getattr(sys.stdout, "encoding", None) or "utf-8"
    return s.encode(enc, errors="replace").decode(enc, errors="replace")


async def main() -> None:
    async with httpx.AsyncClient(base_url=BASE, timeout=120.0) as c:
        try:
            r = await c.get("/")
            print("[OK] 后端:", r.json().get("name"), r.json().get("version"))
        except Exception as e:
            print("[FAIL] 无法连接:", e)
            return

        await c.delete("/api/soul")
        r = await c.post(
            "/api/soul",
            json={
                "current_state_word": "",
                "struggle": "",
                "bias": "warm_humor",
            },
        )
        print("[init soul]", r.status_code)
        if r.status_code != 200:
            print(r.text[:400])
            return

        pj = (await c.get("/api/personality")).json()
        print("[人格预设 warm_humor] voice_style 前200字:")
        print(_preview(pj.get("voice_style") or "(空)", 220))
        print("[自然描述]", _preview(pj.get("natural_description") or "", 140))

        await c.post("/api/sim/person-sit")

        msgs = [
            "嗨，我在测升级后的多级上下文和人格系统。",
            "有点累，今晚还在赶项目。",
            "希望你说话更有性格一点，别总像客服。",
            "那我问你：如果只能选一个，奶茶还是咖啡？",
        ]
        h: list[dict] = []
        for m in msgs:
            t0 = time.perf_counter()
            r = await c.post("/api/companion/chat", json={"message": m, "history": h})
            ms = int((time.perf_counter() - t0) * 1000)
            d = r.json()
            rep = _preview(d.get("reply") or "", 200)
            print(f"--- ({ms}ms) 你: {m[:50]}")
            print(f"    ok={d.get('ok')} err={repr(d.get('error'))}")
            print(f"    陪伴: {rep}...")
            if d.get("ok") and d.get("reply"):
                h.append({"role": "user", "content": m})
                h.append({"role": "assistant", "content": d["reply"]})

        r = await c.post("/api/companion/digest")
        dig = r.json()
        print("[digest]", _preview(json.dumps(dig, ensure_ascii=False), 850))

        pj = (await c.get("/api/personality")).json()
        p = pj.get("params") or {}
        print(
            "[digest 后] playfulness=",
            p.get("playfulness"),
            "attachment=",
            p.get("attachment_level"),
        )
        print("[digest 后 natural]", _preview(pj.get("natural_description") or "", 220))

        ctx = await c.get("/api/companion/context-markdown")
        if ctx.status_code == 200:
            body = ctx.text
            i = body.find("L1")
            snippet = body[max(0, i - 20) : i + 450] if i >= 0 else body[:500]
            print("[context-markdown 片段]", _preview(snippet, 520))


if __name__ == "__main__":
    asyncio.run(main())
