# 简洁版岗位卡

个人岗位档案的简洁版 HTML、Python 生成器与更新记录。沿用已确认的 Monee / 小米版式：一岗一页、五个内容区、五项本地准备勾选。

当前资料快照：**2026-11-25**；项目版本：**0.1.0**。共 **22 张**：11 张候选、4 张岗位明确的已投、4 张已投证据待补、1 张已结束、2 张废纸篓归档。

本项目用于个人私有仓库。包含个人岗位分析和私人资料入口，当前未授予开源许可，也不部署公开网站。以后如需开源，另做通用模板与虚构示例版本。

## 直接查看

- 下载 [最新 HTML 压缩包](dist/career-cards-simple.zip)，解压后双击 `index.html`。
- 或下载仓库完整 ZIP，双击 `site/index.html`。
- 岗位小镇看板：下载仓库后双击 `dashboard/dashboard.html`（电脑横屏使用）。
- [原岗位调度台](https://chatgpt.com/space/page_63ef26ac3cfc81919b258f4932221be5)保留正式记录；各原卡已附 2026-11-25 简洁版入口。
- [最初交付的压缩包](releases/岗位卡_简洁版_2026-11-25.zip)原样保留。

GitHub 的文件页主要显示 HTML 源码，查看完整卡片请下载后在浏览器打开。来源入口可能需要本人登录。练习勾选只保存在使用它的浏览器中，不会上传 GitHub，也不会改变投递状态；更换浏览器或文件地址后进度可能不可见。

## 项目内容

| 位置 | 用途 |
| --- | --- |
| `data/cards.json` | 逐岗文案、分类、准备题及稳定身份 |
| `data/evidence.json` | 原卡状态、来源、地点及待核事项 |
| `data/project.json` | 版本号、资料快照日期、调度台入口 |
| `templates/` | 简洁版样式、勾选交互及已确认的小米快照 |
| `scripts/renderer.py` | 生成独立 HTML 和目录 |
| `scripts/build.py` | 一次完成生成、校验、打包与同步候选准备 |
| `scripts/validate.py` | 核对一岗一条、路径、目录及独立进度键 |
| `scripts/prepare_sync.py` | 准备原 Pages 的附件副本与差异清单，不上传 |
| `site/` | 可直接打开的当前 22 张卡和本地目录 |
| `dist/` | 当前 ZIP、文件校验清单、待同步附件 |
| `releases/` | 初次实际交付的原始压缩包 |
| `sync/` | 历史 Pages 同步回执摘要 |
| `docs/UPDATING.md` | 新增、更新和后续同步方法 |
| `dashboard/` | 岗位小镇看板：双击 `dashboard/dashboard.html`，说明见 `dashboard/README.md` |
| `data/dashboard.json` | 看板里每岗的像素图标与底色 |
| `CHANGELOG.md` | 版本变更记录 |

## 重新生成

需要 Python 3.9 或以上，无第三方依赖。在项目目录执行：

```sh
python3 scripts/build.py
```

脚本读取本仓库内的数据，不依赖原电脑路径，不读取邮箱、CV 文件或账号凭据，也不访问网络。它重新生成 `site/`，核对链接与身份，再生成 `dist/career-cards-simple.zip`、`dist/manifest.json` 和 `dashboard/` 里的看板；同一输入重复生成的 ZIP 一致。

单独校验已生成内容：

```sh
python3 scripts/validate.py
```

## 后续维护

新岗位在 `data/cards.json` 与 `data/evidence.json` 各新增一条对应记录，保留真实来源和核验日期。已有岗位沿用原 `page_id`、`filename`、`storage_key`；不要因换渠道或更新文字新增重复岗位。默认继续使用现有简洁版。

详见 [更新与同步说明](docs/UPDATING.md)。GitHub 提交用于版本保存，**不会自动写回原 Pages**。`dist/sync-plan.json` 只是相对历史回执的差异清单；更新原卡需要另行执行上传并核对原内容、状态与回执。

当前资料是已有材料的整理，不是实时招聘状态监控。岗位不明的四张保留“待补证据”；已结束与废纸篓保持归档。日期、申请状态与个人经历只能依据实际新证据更新。
