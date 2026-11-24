# 岗位小镇 · 看板

把 `data/` 里的全部岗位卡做成一个电脑横屏的工作台：底部图标栏选岗位，每张卡是一块田，勾待核事项（浇水）和练预练题（施肥）会让作物长大、积累经验升级。它是简洁卡之外的附加界面，正式申请状态仍以原岗位卡为准。

## 打开

双击 `dashboard/dashboard.html`。离线可用；联网时会额外加载像素字体，离线时退回系统字体。

勾选、经验、音效开关只保存在当前浏览器（`localStorage` 的 `career-desk-v1` 与 `career-desk-sound`），按岗位 `filename` 记录，不会上传，也不会改变投递状态。它和简洁卡里的五项准备勾选是两套独立记录。

## 文件

| 位置 | 用途 |
| --- | --- |
| `template.dc.html` | 界面模板（与 Claude Design 画布同一格式） |
| `logic.js` | 交互逻辑：切卡、标签、勾选、经验、转场、音效 |
| `runtime.js` | 离线单页用的小型渲染器，无第三方依赖 |
| `sprites.py` | 原创像素图：公司图标、作物六阶段、Logo、月亮 |
| `../data/dashboard.json` | 每个岗位的图标名与底色 |
| `../scripts/dashboard.py` | 生成脚本 |
| `dashboard.html` | 生成：双击打开的离线单页 |
| `canvas.dc.html` | 生成：可放回 Claude Design 画布继续改设计 |

`dashboard.html` 和 `canvas.dc.html` 是生成物，不要手改，改模板或数据后重新生成。

## 来了新岗位卡

1. 照 `docs/UPDATING.md`「增加岗位」，在 `data/cards.json` 和 `data/evidence.json` 各加一条。
2. 在 `data/dashboard.json` 的 `cards` 里加一行，选图标和底色：

   ```json
   "company-pageprefix.html": { "icon": "chip", "color": "#155E75" }
   ```

   可用图标：bank、bars、bed、box、briefcase、building、bulb、camera、chip、coins、gear、gem、globe、magnifier、megaphone、pencil、phone、pie、plane、sparkle、tv、wallet。不写也能生成，会用 building 和自动配色，并在构建时提示。需要新图标时，在 `sprites.py` 的 `ICONS` 里照格式画一个 12×12 网格。
3. 运行 `python3 scripts/build.py`：简洁卡、ZIP 和看板一起更新。只想重做看板可运行 `python3 scripts/dashboard.py`。
4. 双击 `dashboard/dashboard.html` 检查：新卡出现在对应分组、底部图标栏和田野地图里。
5. 改 `data/project.json` 的版本号，写 `CHANGELOG.md`，再提交。

分类变化（候选 → 已投、归档等）只改 `cards.json` / `evidence.json` 的 `category`，看板会自动换组；已结束和废纸篓的田固定为枯萎。

## 容量

当前按 1440×900 设计。底部图标栏放到 28 张左右会变挤，田野地图超出一屏时会在地图区内滚动。岗位明显变多时，再考虑缩小图标或按分组折叠。

## 和 Claude Design 画布同步

`canvas.dc.html` 与画布里的界面是同一份。改设计时可以在画布里改，再把改动搬回 `template.dc.html` / `logic.js`；或者改完仓库后把新生成的 `canvas.dc.html` 交给 Claude 放回画布。
