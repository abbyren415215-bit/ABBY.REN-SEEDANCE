# 旧导演入口归档

2026-10-09用户明确批准精简：`jacob-seedance`、`seedance-director`不再作为本机独立技能入口；ABBY视频创作统一从`abby-seedance/SKILL.md`进入。本规则替代旧“保留两个独立入口继续自动发现”的做法。

## 归档与保留

- 两个已安装目录完整移到Codex用户目录的 `archived-skills/2026-10-09-director-entrypoints/`，位于技能自动发现目录之外；各文件前后SHA-256一致，恢复位置和校验值保存在该目录的本地 `archive-manifest.json`。
- 不删除原文、许可证、脚本、历史文件或用户改动。不向公开仓库上传本机归档；仓库内 `upstream/jacob/` 与 `archive/seedance-director/` 原有来源快照照常保留，仅供按需参考。
- 保留摄影、真人表演、FPV资料库以及dreamina-cli、dreamina-cli-image2video、auto-subtitles执行模块。图片工作流独立，不因这次视频入口整理而删除。
- 在新机器只需安装ABBY；其他机器若仍有这两个入口，按用户本次精简决定先完整归档再移出发现目录，不能只改描述后宣称已停用。

## 恢复

用户要求恢复时，核对本地归档清单并复制回对应技能目录；目标存在则先比较，不覆盖现有文件。归档不是永久删除，也不代表授权运行来源脚本。
