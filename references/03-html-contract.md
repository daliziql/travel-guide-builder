# 03 · 单文件 HTML 图册契约

目标：一个 HTML 走天下（可 file:// 直开、可 Pages 托管），主视图紧凑、细节收进点击弹窗（粗中有细）。
起步直接复制 `assets/html-scaffold.html`，只填数据、不改架构。

## 1. 外部依赖与自包含边界
- 只允许两类外部依赖：Leaflet（unpkg 固定版本 leaflet@1.9.4 的 css+js）、Esri 公共瓦片（Topo + Imagery，`{z}/{y}/{x}` 顺序）。
- 其余一切内联：CSS 在 `<style>`、业务数据与逻辑在文末 `<script>`；实拍图走相对路径 `assets/<gallery>/...`，**禁止** CDN/图床外链（防盗链会让图全挂）。
- 中文目录与文件名 URL 在跳转/刷新时必须百分号编码（`encodeURIComponent`）。

## 2. 必备板块（按顺序）
1. Hero：标题/日期人数/时区/chips 标签（标签短，手机端会换行）。
2. 启程倒计时：T0/T1 用 `Date.UTC` 减 8h 锚定北京时间 0 点；三阶段文案（出发前/旅途中/结束后）先给用户过稿；只保留数字+一句文案。
3. 航段总览 flightline：每程一行、严格列对齐（固定列宽，不用空格凑）；分叉回程同程多目的地、无 A/B 标签、箭头文字写「回程」。
4. 全程航图（Leaflet）：城市 pin（英文标签，不混中文防溢出）、贝塞尔弧线、虚线表飞行、图例；里程用工具现算。
5. 逐日 D1…DN：每天 = 时间轴 + 小地图双栏（窄屏堆叠），编号一一对应。
6. 住宿总览、餐饮速查、红黑榜、预算（区间+口径，合计工具算）、备选池、重点专栏（如徒步，时间轴放锚点 inlink 跳转）、行前待确认、风险与应急（电话/使领馆/救援平台，标核验日期）。
7. 参考链接：聚合去重后收进 `.ref-mask` 弹窗，不在正文堆链接。
8. 实拍弹窗 `.gal-mask`：宫格 → 大图两级。

## 3. 数据 schema（渲染函数只认这个结构）
```js
const C={flight:'#3a7ca5',drive:'#d08a3c',walk:'#8a8f98',hike:'#2e7d6b',food:'#c2553d',stay:'#4f6d7a',rose:'#c2553d',gather:'#b08d3e'};
// 注意：C 里每个 mode 键都必须存在，缺键会让 SVG stroke=undefined
const DAYS=[{
  id:1, date:'10/02 周五', title:'…', stat:'车程15km', level:'●○○○○',
  labels:'permanent'|'hover', fitStops:[0,1],
  stops:[{t:'20:20',n:'地点名',lat,lng,type:'drive',dir:'top',toff:[0,-13],hideName:false}],
  legs:[{a:0,b:1,mode:'drive',d:'15km/25min',lo:{dlat:.02,dlng:0},hideLabel:false}],
  ev:[['flight','15:45','标题','副标题细节','galleryKey']] // 第5位=图集键，可空
}];
```
- 事件五元组 e[4] 存在且 `window.GALLERY[key]` 命中才渲染「实拍 N」按钮；缺键自动不渲染（不出空按钮）。
- legs 的 a/b 是 stops 下标，越界即坏图，渲染前做合法性校验。
- `window.GALLERY={key:{title,items:[{src,cap,url,like}]}}`，由 build_gallery.py 生成；聚合键（citywalk_*）映射到实体目录。

## 4. 实拍弹窗两级加载（弱网关键）
- 宫格用 480px 缩略图 `<file>.th.webp`（均约 20-25KB），大图才用 1280px 原图；
  `onerror` 回退原图路径。一次开 10 张宫格 ≈220KB 而不是 1.3MB。
- 宫格 `loading=lazy decoding=async`；大图态：返回按钮在头部占位（viewing class 给 head 左 padding，防文字重叠）、左右切换、键盘 ←/→/Esc、底部 caption+原笔记链接+序号。
- 图片压缩口径：原图长边 1280、webp q70（平均 ≤150KB，单张不超过 400KB）；缩略图长边 480、q62。用 PIL 批量，仅当新文件更小才替换。

## 5. 响应式（必须做，且必须截图验证）
- 断点：≤860 双栏改单栏；≤640 手机竖屏全面重排；≤380 再收紧。
- 手机端规则要点：
  - 航段卡改 flex 纵向：日期一行、时刻行内自适应、航班号/时长/里程 meta 独占一行（绝不挤在同一行遮挡）。
  - 快跳导航改单行横滑（flex-wrap:nowrap + overflow-x:auto + 隐藏滚动条）。
  - 表格外包 `.table-scroll`（JS 包裹）横向滚动，**不要**给 table 自身 display:block+min-width（会撑破父容器）。
  - 密集日地图：`IS_MOBILE` 下点位名不 permanent，点编号弹名；路段 seg-label 直接隐藏（时间轴已有里程）；航图城市 pin 缩短加宽、fitBounds padding 加大防贴边。
  - 两个弹窗全屏化（100vw/100dvh、圆角清零），宫格 minmax(106px)、大图 max-height 56vh、箭头 38px。
  - 长链接/英文必须 `overflow-wrap:anywhere`，打开弹窗时重置 scrollTop/Left。
- 验证手段：CDP `Emulation.setDeviceMetricsOverride`（kwargs 传参：`bu.cdp("...",width=390,...)`）模拟 390×844；
  注意 override 后再导航可能出现 innerWidth/clientWidth 不一致的测试态，以 `documentElement.clientWidth` + getBoundingClientRect 溢出审计为准；
  全页跑一遍「有无元素 right>clientWidth」的 JS 审计，排除 leaflet 瓦片与横滑导航。

## 6. 文案与样式原则
- 调侃诙谐、不说教；同一餐厅/项目不重复排（重复即 bug）；同类只留最值得的一个（如博物馆）。
- 配色用 :root 变量，低饱和大地色；对齐优先（固定列宽 grid，不用 &nbsp; 凑）；标签英文不混排。
- 每改一轮：重载用户正在看的 tab（file:// 不热更新，navigate 完整编码 URL）→ DOM 校验（legs 不越界、GALLERY 键全命中、console 0 错）→ 关键区截图目检 → 才交付。

## 7. 简洁版 / 详细版双视图（默认简洁版）
- `<body class="simple">` 为默认态；顶部 `.view-toolbar` 放切换按钮，选择写 localStorage（打开瞬间先用内联脚本同步，避免闪烁）。
- 简洁版只保留：启程倒计时、hero 基本信息、D1…DN 时间轴文字（时间+标题+副标题）与日快跳（非 D* 链接隐藏）。
  隐藏：航段总览、全程航图与图例、日地图、实拍按钮、住宿 pill、红黑盒、强度统计，以及逐日之后的全部附加板块（用一个 `.tail` 容器包住，一条 CSS 全收）。
- 关键坑：地图在 `display:none` 容器里初始化尺寸为 0；必须维护 `window.__maps` 注册表并在每次地图上保存 `map.__fit={bounds,opts}`，展开详细版时多次延时 `invalidateSize()+fitBounds()` 重绘。
- 新增 CSS 规则后检查 `<style>` 花括号配平，别把规则误写进 @media 块内（会导致桌面端不生效）。

## 8. 住宿选型页（独立只读页，样板 assets/hotel-picker.html；采集方法见 references/05）
- 用户要评估订哪家时，另建**英文路径**子页 `hotels/index.html`，主攻略工具栏放入口（简洁/详细版都可见）；子页资源用 `../assets/...`、返回链接 `../`。
- **只读展示**（用户明确不要编辑/对比）：无 input/textarea/checkbox、无新增删除/导出导入、不写 localStorage；保留城市 tabs、搜索、排序、实拍灯箱。
- 分两组：`isBnb=h.tier==='民宿'` 区分「酒店 / 连锁与品牌公寓」与「民宿 / 公寓（Airbnb+小红书高评）」；民宿优先 Guest favorite/Superhost 且评分高、评论有量。
- 单卡：名称/区域/档次/适用晚次、各平台报价（价格+采集日期+真实深链，无深链退化为平台搜索链接，无报价显「未采集到报价」）、评分评论数、标签、🟥优势/🖤避坑、同事原话、小红书口碑（带样本量）、实拍、备注；`status:'out'` 作避坑项保留防误订。
- 报价唯一权威是 `lodging-data/quotes_summary.json`、口碑是 `xhs_reputation.json`，页面只渲染不改价；**内部「采集口径/字段说明」SOP 块不进发布页，交付前删除**。
- 酒店/民宿图同样走双 AI Gate，按「全名+城市」强关联、防串店（同名连锁/近似名分开建卡），无专属实拍就留空标注。
