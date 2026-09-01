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
  <key>/<key>_NN.webp            精选原图（复制，保持文件名规整）
  <key>/<key>_NN.th.webp         480px 宫格缩略图（--thumbs 时生成）
  provenance.json                每张图 → 原笔记溯源
  gallery-data.js                window.GALLERY={key:{title,items:[{src,cap,url,like}]}}

用法：
  python3 build_gallery.py --trip <行程目录> --select gate2_select.json \
      --gallery gallery2 [--thumbs]
"""
import argparse, json, os, shutil, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trip", required=True, help="行程目录绝对路径")
    ap.add_argument("--select", required=True, help="Gate-2 精选清单 JSON")
    ap.add_argument("--gallery", default="gallery", help="assets 下的图库目录名")
    ap.add_argument("--thumbs", action="store_true", help="同时生成 480px 缩略图 (.th.webp)")
    ap.add_argument("--thumb-edge", type=int, default=480)
    ap.add_argument("--thumb-q", type=int, default=62)
    args = ap.parse_args()

    trip = os.path.abspath(args.trip)
    sel = json.load(open(args.select, encoding="utf-8"))
    entities = sel["entities"]
    html_map = sel.get("html_map", {})
    dst_root = os.path.join(trip, "assets", args.gallery)
    os.makedirs(dst_root, exist_ok=True)

    Image = None
    if args.thumbs:
        from PIL import Image as _Image
        Image = _Image

    gallery, provenance = {}, {}
    for key, ent in entities.items():
        d = os.path.join(dst_root, key)
        os.makedirs(d, exist_ok=True)
        items, prov = [], []
        for n, it in enumerate(ent.get("items", []), 1):
            src = it["src"]
            if not os.path.isabs(src):
                src = os.path.join(trip, src)
            ext = os.path.splitext(src)[1].lower() or ".webp"
            name = f"{key}_{n:02d}.webp"
            out = os.path.join(d, name)
            if ext in (".webp", ".jpg", ".jpeg", ".png"):
                shutil.copyfile(src, out)
            else:
                raise SystemExit(f"不支持的图片格式: {src}")
            rel = f"assets/{args.gallery}/{key}/{name}"
            items.append({"src": rel, "cap": it.get("cap", ""), "url": it.get("url", ""), "like": it.get("like")})
            prov.append({"file": rel, "source": it.get("url", ""), "like": it.get("like"), "origin": src})
            if args.thumbs:
                th = out[:-5] + ".th.webp"
                im = Image.open(out).convert("RGB")
                w, h = im.size
                if max(w, h) > args.thumb_edge:
                    s = args.thumb_edge / max(w, h)
                    im = im.resize((round(w * s), round(h * s)), Image.LANCZOS)
                im.save(th, "WEBP", quality=args.thumb_q, method=6)
        gallery[key] = {"title": ent.get("zh", key), "items": items}
        provenance[key] = prov

    # 聚合/别名键：共享同一批 items（浅拷贝即可）
    for alias, keys in html_map.items():
        merged = []
        for k in keys:
            if k in gallery:
                merged.extend(gallery[k]["items"])
        gallery[alias] = {"title": alias, "items": merged}

    with open(os.path.join(dst_root, "provenance.json"), "w", encoding="utf-8") as f:
        json.dump(provenance, f, ensure_ascii=False, indent=1)
    with open(os.path.join(dst_root, "gallery-data.js"), "w", encoding="utf-8") as f:
        f.write("window.GALLERY=")
        json.dump(gallery, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")

    n_img = sum(len(v["items"]) for k, v in gallery.items() if k not in html_map)
    print(f"OK 实体 {len(entities)} 个（含聚合键共 {len(gallery)}），精选图 {n_img} 张，"
          f"缩略图={'已生成' if args.thumbs else '未生成'} → {dst_root}")

if __name__ == "__main__":
    main()
