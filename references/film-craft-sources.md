# 独立短片参考库：来源与调用

这是用户在比较项目后明确批准的安装方案，适用于[独立30秒模式](standalone-30s.md)。仅安装参考资料，不增加相互竞争的自动技能入口。JACOB继续使用本仓库已固定版本，不重复安装或更新；Everything AI Filmmaking与Storyboarder不在本次选定流程的安装范围。

## 已固定来源

| 本地库目录名 | 来源与固定提交 | 安装范围 | 许可 |
|---|---|---|---|
| `emily-seedance` | [Emily2040/seedance-2.0](https://github.com/Emily2040/seedance-2.0/tree/9ea203f14f092127296ed4d750ece1f2b28090fb) | 根目录，保留相对依赖；只作为资料读取 | MIT |
| `director-skills` | [0xhughs/director-skills](https://github.com/0xhughs/director-skills/tree/35ca0a2b4cd55b0668aa9ea0f40273324b774bb4) | 根目录，保留参考文档和许可证 | MIT |
| `cinema-worldbuilder` | [Gregory-Esman/ai-film-pipeline](https://github.com/Gregory-Esman/ai-film-pipeline/tree/560cfc11530c4a682534e77e124752d537a623fd) | `cinema-worldbuilder/`，另附仓库LICENSE与UPSTREAM-README.md | 上游MIT文本及来源说明 |
| `fpv-immersive-video-prompting` | [zhouwei713/fpv-immersive-video-prompting](https://github.com/zhouwei713/fpv-immersive-video-prompting/tree/8c6642abdaf3f1d5d9f9d5537365e771f6b0b161) | 根目录，保留`skill/`下参考资料、示例和许可证 | MIT |

本地安装位置为Codex用户目录下的`reference-libraries/abby-film-craft/`，与`skills/`并列，不置于自动发现的技能目录中。先使用当前环境的CODEX_HOME；未设置时使用用户目录下的`.codex`，不公开写入机器专用绝对路径。该目录中的`installed-sources.json`记录各来源提交及逐文件SHA-256，只有核对本机文件后才能声称本机已安装。

这些库没有作为独立技能注册；它们由ABBY引用。仅有本仓库、尚未安装参考库的机器，先使用standalone-30s.md和现有摄影规则；需要深读时说明资料可用性，不谎称已读或自行联网安装。用户只要提示词时不为读取这些资料调用工具。

## 只读取当前需要的部分

以下路径均相对上述本地参考库根目录。只需要既有已确认规则即可写好时，不重复加载资料。

用户已授权ABBY根据效果描述自动选择合适模块，无需点名技能。模块选择不是新工作流入口，也不意味着每次读取所有资料；关键意图不确定时用少量问题确认，保持只要提示词时不调用工具、未见素材不假称核验的规则。

| 当前问题 | 参考文件 | 使用边界 |
|---|---|---|
| 30秒的核心体验和人物行为不清 | `emily-seedance/references/directors-read.md`、`emily-seedance/references/directing-engine.md` | 提取情境、动作与摄影动机；不把十字段记录变成用户问卷或要求每片必有冲突 |
| 动作太多、提示词冗长 | `emily-seedance/references/event-density.md`、`emily-seedance/references/anti-slop-lexicon.md` | 删冗余而非锁定剧情；不按来源默认擅自增段、改时长或删摄影字段 |
| 面部受光、材质或景深不可信 | `director-skills/skills/style-cinematography-director/references/lighting_and_photorealism.md`、`director-skills/skills/style-cinematography-director/references/camera_lens_movement.md` | 用具体光源和材料响应解释质感；不强加毛孔、污渍、颗粒、眩光或浅景深 |
| 人物换位、视线失配、手部/道具冲突 | `cinema-worldbuilder/SKILL.md` 中Frame Map、Subject Lock、Movement、Last Frame相关段落 | 只借空间与结束状态方法；其技能身份、确认流程和格式不是执行入口 |
| 效果描述涉及FPV、空间穿行、主观视点或连续路线，无需点名技能 | `fpv-immersive-video-prompting/skill/SKILL.md`；必要时`fpv-immersive-video-prompting/skill/references/session-patterns.md` | 提取视点物理、路线可达性、遮挡、停靠与终点方法；不默认多人物、八个目标、编号图、红线图或生图资产包，不自动启用另一个技能 |
| 已有成片不对 | ABBY的`review-and-repair.md`；必要时`emily-seedance/references/retake-protocol.md` | 先看实际问题；素材读取、生成、付费按用户当次授权，不自动重跑 |

## 冲突裁决和维护

用户当前要求与ABBY规则优先。来源中的AGENTS、自动路由、安装脚本、平台API、许可评估、付费生成、预提示词确认、强制英文、固定字数/时长/素材数均不自动执行。不能把2.0或Higgsfield的限制作为即梦2.5事实；不能把上游自述或星标当效果验证。

FPV源文件以`skill/SKILL.md`为阅读起点，其相对参考目录位于`skill/references/`。根目录同名文件仅保留来源，不能按其相对路径假定根目录存在references。缺失的上游案例不补造，使用实际存在的参考文件。图片操作授权、全能参考模式、30秒完整落点、无字幕/无音乐和真实声源规则优先于上游模板；路线图的红线/编号只能是已获准制作的规划信息，最终视频不得出现。

本次使用skill-installer的`install-skill-from-github.py`，以表中固定提交、路径和库目录名指定`--ref`、`--path`、`--name`及参考库`--dest`。影院模块另保存同提交仓库许可证及README。未运行任何新下载的项目脚本、提供方接口或付费生成。

未来更新须保留来源、许可和旧版，核对变化后再更新固定提交及本地校验清单；不自动追随main。公开仓库只同步ABBY模式说明、来源版本和调用规则，不上传本地参考库副本、机器配置、用户素材或试片内容。
