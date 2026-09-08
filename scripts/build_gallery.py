#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用实拍图库构建（travel-guide-builder）。

输入 gate2 精选清单 JSON：
{
  "entities": {
    "<key>": {"zh": "中文名", "items": [
      {"src": "原始图绝对/相对 trip 目录的路径", "url": "原笔记链接", "like": 123, "cap": "图说"}
    ]}
  },
  "html_map": {"<聚合键或旧键>": ["<entity key>", ...]}   // 可选
}

产出（写到 <trip>/assets/<gallery>/）：
  <key>/<key>_NN.webp            主图：长边 1280、webp q70（单张目标 ≤400KB）
  <key>/<key>_NN.th.webp         缩略图：长边 480、q62（默认生成，--no-thumbs 关闭）
  provenance.json                每张图 → 原笔记溯源
  gallery-data.js                window.GALLERY={key:{title,items:[{src,cap,url,like}]}}

用法：
  # 全量构建（按 select 重建整个图库索引）
  python3 build_gallery.py --trip <行程目录> --select gate2_select.json --gallery gallery2

  # 增量合并（只重建 select 里的 key，其余旧 key/索引原样保留，用于补新点位）
  python3 build_gallery.py --trip <行程目录> --select gate2_select_new.json --merge
"""
import argparse, json, os, re, sys


def save_webp(src_path, out_path, edge, quality):
    """统一压缩为 webp；已是 webp 也重编码以保证体积/尺寸达标。"""
    from PIL import Image
    with Image.open(src_path) as im:
        im = im.convert("RGB")
        w, h = im.size
        if max(w, h) > edge:
            k = edge / max(w, h)
            im = im.resize((round(w * k), round(h * k)), Image.LANCZOS)
        im.save(out_path, "WEBP", quality=quality, method=6)


def load_existing_js(js_path):
    """从现有 gallery-data.js 还原 dict；不存在或损坏返回 {}。
    旧版产物可能是带不引号 key 的多行合法 JS（非合法 JSON），json 失败时用 node 兜底。"""
    if not os.path.exists(js_path):
        return {}
    txt = open(js_path, encoding="utf-8").read()
    body = re.sub(r"^\s*/\*[\s\S]*?\*/", "", txt)  # 去头部注释
    m = re.search(r"window\.GALLERY\s*=\s*(\{.*\})\s*;?\s*$", body, re.S)
    if not m:
        return {}
    raw = m.group(1)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        import shutil, subprocess
        if not shutil.which("node"):
            print("WARN: 旧 gallery-data.js 非合法 JSON 且无 node 可解析，为防清空索引已中止合并")
            raise SystemExit("请先将旧 js 规范化为合法 JSON，或安装 node 后重试 --merge")
        node_code = "process.stdout.write(JSON.stringify(eval('('+process.argv[1]+')')))"
        r = subprocess.run(["node", "-e", node_code, raw], capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit("旧 gallery-data.js 无法解析: " + r.stderr[:300])
        return json.loads(r.stdout)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trip", required=True, help="行程目录绝对路径")
    ap.add_argument("--select", required=True, help="Gate-2 精选清单 JSON")
    ap.add_argument("--gallery", default="gallery", help="assets 下的图库目录名")
    ap.add_argument("--merge", action="store_true",
                    help="增量模式：只覆盖 select 中的 key，保留库内其他 key 与索引")
    ap.add_argument("--main-edge", type=int, default=1280)
    ap.add_argument("--main-q", type=int, default=70)
    ap.add_argument("--no-thumbs", action="store_true", help="不生成 480px 缩略图")
    ap.add_argument("--thumb-edge", type=int, default=480)
    ap.add_argument("--thumb-q", type=int, default=62)
    args = ap.parse_args()

    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        sys.exit("需要 Pillow：pip3 install Pillow")

    trip = os.path.abspath(args.trip)
    sel = json.load(open(args.select, encoding="utf-8"))
    entities = sel["entities"]
    html_map = sel.get("html_map", {})
    dst_root = os.path.join(trip, "assets", args.gallery)
    os.makedirs(dst_root, exist_ok=True)
    js_path = os.path.join(dst_root, "gallery-data.js")
    pv_path = os.path.join(dst_root, "provenance.json")

    gallery = load_existing_js(js_path) if args.merge else {}
    provenance = {}
    if args.merge and os.path.exists(pv_path):
        provenance = json.load(open(pv_path, encoding="utf-8"))

    n_new_files = 0
    for key, ent in entities.items():
        d = os.path.join(dst_root, key)
        os.makedirs(d, exist_ok=True)
        items, prov = [], []
        for n, it in enumerate(ent.get("items", []), 1):
            src = it["src"]
            if not os.path.isabs(src):
                src = os.path.join(trip, src)
            if not os.path.exists(src):
                raise SystemExit(f"源图不存在: {src}")
            stem = f"{key}_{n:02d}"
            main = os.path.join(d, stem + ".webp")
            save_webp(src, main, args.main_edge, args.main_q)
            n_new_files += 1
            rel = f"assets/{args.gallery}/{key}/{stem}.webp"
            items.append({"src": rel, "cap": it.get("cap", ""),
                          "url": it.get("url", ""), "like": it.get("like")})
            prov.append({"file": rel, "source": it.get("url", ""),
                         "like": it.get("like"), "origin": it.get("src", "")})
            if not args.no_thumbs:
                th = os.path.join(d, stem + ".th.webp")
                save_webp(src, th, args.thumb_edge, args.thumb_q)
        gallery[key] = {"title": ent.get("zh", key), "items": items}
        provenance[key] = prov

    # 聚合/别名键：共享同一批 items（merge 时也按最新 html_map 重建）
    for alias, keys in html_map.items():
        merged = []
        for k in keys:
            if k in gallery:
                merged.extend(gallery[k]["items"])
        gallery[alias] = {"title": alias, "items": merged}

    with open(pv_path, "w", encoding="utf-8") as f:
        json.dump(provenance, f, ensure_ascii=False, indent=1)
    with open(js_path, "w", encoding="utf-8") as f:
        f.write("window.GALLERY=")
        json.dump(gallery, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")

    n_ent = len(entities)
    n_img = sum(len(v["items"]) for k, v in gallery.items() if k not in html_map)
    mode = "增量合并" if args.merge else "全量构建"
    print(f"OK [{mode}] 本次实体 {n_ent} 个、压缩主图 {n_new_files} 张，"
          f"库内共 {len(gallery)} key / {n_img} 张，缩略图={'未生成' if args.no_thumbs else '已生成'} → {dst_root}")


if __name__ == "__main__":
    main()
