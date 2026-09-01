# 04 · 验证、版本快照与 GitHub Pages 发布

## 1. 每轮改动后的验证闭环（不过不交付）
1. file:// 不随磁盘改动热更新：在用户正在看的 tab 用 `bu.navigate(完整百分号编码 URL)` 重载，不要只改文件就宣称完成。
2. DOM/数据校验（bu.js 表达式）：
   - legs 下标不越界：遍历 DAYS，每 leg 的 a/b 都能取到 stop；
   - 图集键全命中：每个事件 e[4] 都能在 window.GALLERY 找到；
   - `bu.console_messages()` 为 0 error；
   - 窄屏溢出审计：遍历 `.wrap *`，`getBoundingClientRect().right > clientWidth+1.5` 的元素列出（排除 leaflet 瓦片、横滑导航、table-scroll 内部表）。
3. 截图目检关键区：首屏、航段总览、一日时间轴+小地图、实拍宫格、大图态、表格、弹窗；桌面宽度（≥1024）也要回归一张，确认媒体查询没误伤。
4. 线上发布后：curl 关键资源状态码/体积，再用浏览器开线上 URL 实测一次（file:// 过 ≠ 公网过）。

### 移动视口模拟注意
- `bu.cdp("Emulation.setDeviceMetricsOverride",width=390,height=844,deviceScaleFactor=2,mobile=True)`，**参数用 kwargs**；
  override 在导航后可能丢失或出现 innerWidth/clientWidth 不一致，以 clientWidth 与计算样式为准，必要时 clear→set→navigate 重来。
- 后台/非前台标签会冻结懒加载与定时器：用户主动点开的弹窗图用 `loading="eager" fetchpriority="high"`，不要依赖 lazy。

## 2. 版本快照（大改前留档）
```bash
# 本地工程内（行程目录路径按实际，发布仓可能已扁平化，见第 3 节）
cp 主攻略.html 主攻略_vN备份.html
cp -R assets/<gallery> assets/<gallery>_vN
# 备份 HTML 内部的图库引用路径 sed 改写为独立目录，保证快照自包含
# 多版本最终统一移入 backup/ 并 tar.gz 压缩留档，不进 git
```

## 3. GitHub Pages 发布（扁平 + 全英文 URL）
工程只发布最新版；raw/、backup/、_cand/ 候选图、.DS_Store、__pycache__ 进 .gitignore。

**本地工程结构（trips 多行程机制）与发布仓结构是两回事**：本地可继续用 `trips/<行程>/` 组织多份攻略；
但对外发布仓要**扁平化、URL 全英文、无中文、无 trips 多层嵌套**：

```
发布仓根/
├── index.html              # 主攻略本身（不再用 meta-refresh 中转跳转）
├── hotels/index.html       # 住宿选型页 = 单一英文子目录，URL 即 /<repo>/hotels/
├── assets/                 # 图库/酒店图（主攻略用 assets/..，hotels 子页用 ../assets/..）
└── lodging-data/ notes/ …  # 数据与素材（raw/_cand 不入库）
```

```bash
# 首次：在发布仓根建仓（public），Pages 源选 main 分支根目录
git init -b main && git add -A && git commit -m "init"
gh repo create <英文目的地名，如 almaty-aktau-2026> --public --source=. --remote=origin --push
gh api repos/<owner>/<repo>/pages -X POST -f source[branch]=main -f source[path]=/   # 若未自动开启
# 扁平化移动（保留 git 历史）：git mv 旧中文行程页 index.html；新建 hotels/ 放住宿页
# 之后：常规提交推送，Pages 自动重建（约 1 分钟）
git add -A && git commit -m "..." && git push
# 查构建：gh api repos/<owner>/<repo>/pages/builds/latest --jq .status  → built
```
- 主攻略内互链用相对英文路径：入口 `href="hotels/"`，住宿页返回 `href="../"`；**不要**在 URL 里留中文文件名或 trips 段。
- 仓库改名：`gh repo rename <new> --yes`（remote 自动更新）；**旧 Pages 地址不会跳转，旧 URL 直接 404，要同步换新地址**。
- 本地 git 身份若与全局不同，用 `git -c user.name=.. -c user.email=.. commit` 或仓内 `git config`。
- 发布后实测：根 `/` 与 `/hotels/` 均 200、`curl -sI <图片URL>` 看 content-type/content-length/x-cache、旧中文 URL 预期 404、线上页面浏览器实测图集出图。
- 回滚：`git revert <commit> && git push` 或 Pages 构建历史里选旧 build。

## 4. 公网图片问题排查路径（按顺序）
1. 路径/大小写：macOS 磁盘不区分大小写，Pages（Linux）区分——抽 20-30 个 data.js 里的真实路径 curl 线上，全 200 才排除；
2. content-type：webp 应为 image/webp；
3. 体积：单张 >400KB 即压缩（长边 1280/q70），宫格另出 480px 缩略图；
4. 加载策略：弹窗图 eager；弱网实测「点开弹窗到全部出图」耗时；
5. 外链图床防盗链：全部改本地相对路径。
