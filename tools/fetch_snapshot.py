#!/usr/bin/env python3
"""把 Larch 市集上某個作品的已發佈快照抓下來，並印成人看得懂的流程大綱。

用法：
    python3 tools/fetch_snapshot.py                 # 抓《鴨子探索：是誰？》並印大綱
    python3 tools/fetch_snapshot.py <gameId>        # 抓別的作品
    python3 tools/fetch_snapshot.py --json out.json # 另外把原始快照存起來

這支工具只讀公開的市集端點，不需要登入。抓下來的快照是作者的著作，
本 repo 不收錄，也請不要重新散布（見 README 的「授權」）。
"""
import json
import sys
import urllib.request

DEFAULT_GAME = "b1ce07d9-39f7-429b-8466-9ab6b3778c38"
API = "https://larch.ink/api/marketplace/{}?play=1"


def fetch(game_id):
    with urllib.request.urlopen(API.format(game_id), timeout=60) as r:
        return json.load(r)


def outline(snap):
    p = snap["project"]
    yield f"# {snap['title']}／{snap['authorName']}"
    yield f"release {snap['releaseNumber']}　更新 {snap['updatedAt']}"
    yield ""
    yield "## 變數"
    for v in p.get("variables", []):
        yield f"- {v['name']}（{v.get('label','')}）預設 {v.get('defaultValue')!r}"
    for b in p["boards"]:
        out = {}
        for e in b.get("edges", []):
            out.setdefault(e["source"], []).append(e)
        yield ""
        yield f"## 章節：{b['name']}　卡 {len(b.get('nodes',[]))}　線 {len(b.get('edges',[]))}"
        for n in b.get("nodes", []):
            d = n["data"]
            yield ""
            yield f"### [{n['id'][:14]}] {d.get('title')}"
            lines = d.get("dialogueLines") or [{"text": d.get("text"), "speaker": d.get("speaker")}]
            for L in lines:
                sp = L.get("speaker") or "旁白"
                yield f"    {sp}：{(L.get('text') or '').strip()}"
            if d.get("choices"):
                yield f"    ＊選項：{d['choices']}"
            if d.get("variableOps"):
                yield f"    ＊變數：{json.dumps(d['variableOps'], ensure_ascii=False)}"
            for pr in (d.get("stage") or {}).get("props", []):
                if pr.get("clickAction"):
                    yield f"    ＊道具 {pr.get('name')}：{json.dumps(pr['clickAction'], ensure_ascii=False)}"
            for e in out.get(n["id"], []):
                cond = (e.get("data") or {}).get("condition") or e.get("condition")
                tail = f"　條件 {json.dumps(cond, ensure_ascii=False)}" if cond else ""
                yield f"    → {e['target'][:14]}　{e.get('label') or ''}{tail}"


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    game_id = args[0] if args else DEFAULT_GAME
    snap = fetch(game_id)
    if "--json" in argv:
        path = argv[argv.index("--json") + 1]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(snap, f, ensure_ascii=False, indent=1)
        print(f"原始快照已存到 {path}", file=sys.stderr)
    for line in outline(snap):
        print(line)


if __name__ == "__main__":
    main(sys.argv)
