# 工作流更新总账

## 2026-09-13 — 统一JACOB基础、ABBY更新与剧集执行

本次按用户授权整理本地未提交稿、已保存表演更新、GitHub既有更新、JACOB上游和近期项目规则。历史更新按来源归档，未核实的发生日期不补造。

| 来源/更新内容 | 统一落点 |
|---|---|
| JACOB最新远端HEAD `f74d2fcfa803cec4007fdfbeae9cde8831693ee7`，发布记录2.1 | `upstream/jacob/`保留完整文字、实例、许可与署名 |
| JACOB逐镜焦段、可见效果、景别、机位、运镜、光源三层、潜台词、结束状态、画框可行性 | `references/cinematography.md`，由SKILL必经路由执行 |
| GitHub初始参考模块、场景生态、人物身份、多视图、声音与成片修复 | 保留Git历史，集中到ABBY对应reference；旧JACOB路径保留跳转 |
| 本地已提交的`6ce31cc`表演和连续性更新 | `references/abby-production-rules.md`、`review-and-repair.md` |
| 近期Seedance Director接触尺寸、物理结果、反应延迟、手部回落、参考姿势排除、拟音、混音距离 | `references/contact-and-sound.md`；原工作流和脚本保留于`archive/seedance-director/`，不运行第二套默认流程 |
| 剧情覆盖、混合镜头长度、双人近景公平覆盖、语速曲线、微表情、状态账本、白线/道具连续性 | ABBY实拍规则与项目稳定生成协议 |
| 本剧16:9、30秒、前中后有效场景、25秒前结束台词、5秒无台词、1.5秒稳定尾段 | `projects/bingbing/workflow.md`与`production-protocol.md` |
| 第六集人物、夜市衣服、15厘米差、已确认剧情台词、六项第二段素材、禁止虚构“周末夜市” | `projects/bingbing/current-state.md`；草稿与已确认状态分开 |
| 本地固定设定档与稳定协议中的既有更新 | 整理为`series-bible.md`、`production-protocol.md`并同步工作目录副本；过时默认明确裁决 |
| 旧最短3秒、固定5:3、强制出门/进场、强制硬首帧、27.5秒才开始末句、默认三个版本/BGM等冲突 | `references/rule-precedence.md`；执行模块同时修正，不靠模型猜优先级 |
| 今后以项目执行、每项工作流更新同步GitHub | 根AGENTS、`references/maintenance.md`、剧集目录接入规则 |
| 旧技能自动选择与来源嵌套重名 | 旧安装入口加ABBY专用路由，规则保存于`integrations/legacy-routing.md`；归档入口改名SKILL.source.md，仅调整对应README链接，原文仍保留 |

保留用户现有改动与远端提交；合并历史已有`d8f6b2d`，不重建或强推。公开同步范围为工作流文字、代码来源及已确认设定；不上传人物图片、音色或成片。

本次没有生成图片、视频，也没有改写第二段提示词或补写第三四段台词。新镜头草稿仍须用户确认。

校验：统一入口及两份旧入口均通过skill-creator格式验证；所有执行模块的相对文档链接存在；22份上游文件与固定提交逐份比较通过（仅入口改名、README对应链接和末尾空白规范化）；本地剧集接入、设定和协议与仓库副本一致（公开副本仅去除个人素材绝对路径）。

同步方式：终端HTTPS推送缺少凭据，使用已授权GitHub连接器按相同文件树提交，保留远端历史；原本地提交分支保留，安装main跟踪经树SHA核验一致的远端提交。后续同类情况遵循维护文档中的连接器回退流程。
