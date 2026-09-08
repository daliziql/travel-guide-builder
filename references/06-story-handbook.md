# 06 · 历史人文手册（独立图文子页，三步法）

当用户想「人到，脑子也到」——把行程地点/风景/建筑/餐饮的历史人文讲透时，另建独立子页 `stories/index.html`（扁平英文路径，主攻略工具栏加入口，简洁/详细视图都可见），**不走双视图、不放地图**，专注长读。

## 三步法（顺序不可颠倒）

### ① 素材稿 Markdown（先与用户对稿，再写页面）
- `notes/人文手册-素材稿.md`：先列**覆盖矩阵**，逐条映射主行程 D1…DN **以及备选池**的每个地点/建筑/餐饮，「只多不少」，用户确认前不写 HTML。
- 每条 = 事实段（多源核验、带年份数字）+ 书摘短句（标章节名，不大段搬运，版权敏感）+「到现场看什么」行动钩子。
- 事实部分必须经公开权威来源交叉核验（官方历史机构、UNESCO、Wikidata、学术工具书），分歧数字按区间/多口径并列，不选边。
- 文风：若用户提供行记/著作，模仿其**方法**而非造句——白描多于形容词、以小人物小物件承载大历史、冷静叙述里克制调侃；与主攻略的诙谐风有意区分，成稿前可让用户先试读样条确认语感。
- 结构按「线」组织（城市线/自然地质线/苏联线/餐饮线），卷首放一条可横滑的文明时间轴，卷末放：书章索引表（书章↔行程日映射）、名词小卡、书单/片单、史源折叠区。

### ② 双图源补图（两套分区呈现，绝不混用）
- **实拍图**：沿用小红书双 Gate 管线并入主 `gallery2`（新关键词批次换新物理目录如 imgs4，联系表 Gate2，build 增量合并）。子页引用时注意：gallery-data.js 里的路径相对**仓库根**（`assets/...`），子页在 `stories/` 下，渲染时要给路径加 `../` 前缀。
- **历史影像**：走 **Wikimedia Commons API**（自写 search/info/dl 脚本，带 UA、429 指数退避、延时批量），只收 Public Domain / CC0 / CC BY 授权；统一转 webp（长边 1280、q72）放 `assets/stories/history/`，info 元数据落 `provenance.commons.json`（title/author/date/license/url），CC BY-SA 必须逐张署名；原始大图归档 `raw/` 不入库。
- 老照片与实拍在 UI 上分区：两类按钮（实拍 `.g-btn` / 老照片 `.h-btn`）、两个弹窗标题口径，caption 标年代+授权。

### ③ 页面生成与验证发布
- 复用主攻略 :root 色板、弹窗组件（宫格 480 缩略 → 大图键盘 ←/→/Esc）、响应式断点与 390px 审计；正文用「锚点胶囊 + 条目卡片」长读排版，TOC 快跳。
- 校验：全部 data-gal 键在 window.GALLERY 命中、data-hist 相册文件全部存在、标签/花括号配平、console 0 错、桌面与 390px 截图目检（横滑容器内元素不计页面级溢出，以 `documentElement.scrollWidth==clientWidth` 为准）。
- 发布：白名单 git add（stories/、assets/stories/、gallery 增量、主攻略入口改动），notes 素材稿与 raw 不入库；Pages 构建后 curl 子页/历史图/gallery-data 均 200。

## build_gallery.py 增量合并注意
旧 gallery-data.js 可能是「键名不带引号的合法 JS（非合法 JSON）」。脚本 load_existing_js 现已在 json 解析失败时用 node 兜底解析，node 也失败则**直接中止**而不是静默返回 {}（静默 {} 会在 --merge 时清空全部旧 key）。合并前先 `git status` 留退路；紧急情况下可用独立 merge 脚本以 node eval 解析旧 JS → 合并 → 以合法 JSON 紧凑单行重写。
