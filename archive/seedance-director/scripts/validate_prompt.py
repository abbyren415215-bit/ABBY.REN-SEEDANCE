#!/usr/bin/env python3
"""Seedance 2.0 中文提示词静态预检。

本工具只检查可确定的结构风险和保守启发式，不预测生成质量，也不代替
即梦、火山引擎或其他提供商的实时参数校验。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class Issue:
    severity: str
    code: str
    message: str
    basis: str


MODES = ("auto", "text", "first-frame", "first-last", "multimodal", "edit", "extend", "stitch")
LIMITS = {"image": 9, "video": 3, "audio": 3}
REF_PATTERNS = {
    "image": re.compile(r"(?<!\w)(?:@|\[)?(?:image|图片|图像|图)\s*[_#-]?\s*(\d+)\]?", re.I),
    "video": re.compile(r"(?<!\w)(?:@|\[)?(?:video|视频)\s*[_#-]?\s*(\d+)\]?", re.I),
    "audio": re.compile(r"(?<!\w)(?:@|\[)?(?:audio|音频|音声)\s*[_#-]?\s*(\d+)\]?", re.I),
}
CAMERA_GROUPS = {
    "pan": ("摇镜", "横摇", "pan ", "pans "),
    "tilt": ("俯仰", "上摇", "下摇", "tilt ", "tilts "),
    "push-pull": ("推镜", "推近", "拉远", "拉镜", "dolly", "push-in", "push in", "pull-back", "pull back"),
    "track": ("跟拍", "横移", "tracking", "track shot", "follow shot"),
    "orbit": ("环绕", "绕拍", "orbit", "arc shot"),
    "zoom": ("变焦", "zoom ", "zooms "),
    "crane": ("升降", "航拍下降", "航拍上升", "crane", "jib"),
    "handheld": ("手持镜头", "手持摄影", "手持跟拍", "handheld", "hand-held"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="静态检查即梦/Seedance 2.0 视频提示词")
    parser.add_argument("prompt_file", nargs="?", help="UTF-8 提示词文件；省略时从 stdin 读取")
    parser.add_argument("--text", help="直接传入提示词；不能和 prompt_file 同时使用")
    parser.add_argument("--duration", type=int, help="单次生成时长（秒）")
    parser.add_argument("--mode", choices=MODES, default="auto")
    parser.add_argument("--images", type=int, help="实际上传图片数")
    parser.add_argument("--videos", type=int, help="实际上传视频数")
    parser.add_argument("--audios", type=int, help="实际上传音频数")
    parser.add_argument("--format", choices=("text", "json"), default="text", dest="output_format")
    parser.add_argument("--strict", action="store_true", help="仍有警告时返回退出码 2")
    return parser.parse_args()


def read_prompt(args: argparse.Namespace) -> str:
    if args.text is not None and args.prompt_file:
        raise ValueError("--text 和 prompt_file 只能使用一个")
    if args.text is not None:
        return args.text
    if args.prompt_file:
        return Path(args.prompt_file).read_text(encoding="utf-8")
    return sys.stdin.read()


def add(issues: list[Issue], severity: str, code: str, message: str, basis: str) -> None:
    issues.append(Issue(severity, code, message, basis))


def references_in(text: str) -> dict[str, list[int]]:
    return {
        kind: [int(match.group(1)) for match in pattern.finditer(text)]
        for kind, pattern in REF_PATTERNS.items()
    }


def camera_moves(text: str) -> list[str]:
    normalized = f" {text.lower()} "
    return [name for name, terms in CAMERA_GROUPS.items() if any(term.lower() in normalized for term in terms)]


def is_beat_montage(text: str) -> bool:
    lower = text.lower()
    signals = (
        "卡点",
        "快切",
        "硬切",
        "蒙太奇",
        "重拍",
        "鼓点",
        "节拍",
        "独立切镜",
        "商业剪辑",
        "beat-synced",
        "beat synced",
        "fast-cut",
        "fast cut",
        "hard cut",
        "montage",
    )
    return any(signal in lower for signal in signals)


def has_cut_contract(text: str) -> bool:
    lower = text.lower()
    contract_terms = (
        "独立构图",
        "独立镜头",
        "独立切镜",
        "清楚硬切",
        "明确的",
        "不合并为连续长镜头",
        "不是一镜到底",
        "非一镜到底",
        "visible cuts",
        "distinct shots",
        "do not merge",
        "not a continuous take",
    )
    return any(term in lower for term in contract_terms)


def has_high_risk_interaction(text: str) -> bool:
    lower = text.lower()
    terms = (
        "吃下", "入口", "咬", "喝下", "饮用", "吞咽", "嘴唇", "口红", "涂抹",
        "擦在脸", "贴近嘴", "喂食", "chew", "bite", "drink", "swallow",
        "apply to face", "apply lipstick", "touches her lips", "touches his lips",
    )
    return any(term in lower for term in terms)


def has_food_contact(text: str) -> bool:
    lower = text.lower()
    action_terms = ("吃下", "入口", "咬", "咀嚼", "chew", "bite", "eat")
    food_terms = (
        "巧克力", "食物", "饼干", "蛋糕", "水果", "糖果", "面包", "甜点",
        "chocolate", "food", "cookie", "cake", "fruit", "candy", "bread", "dessert",
    )
    return any(term in lower for term in action_terms) and any(term in lower for term in food_terms)


def has_size_cue(text: str) -> bool:
    lower = text.lower()
    cues = (
        "一口大小", "拇指大小", "指尖大小", "小块", "小片", "小口", "小颗",
        "不规则碎片", "2厘米", "3厘米", "2 cm", "3 cm", "bite-sized",
        "bite sized", "small piece", "small shard", "small square",
    )
    return any(cue in lower for cue in cues)


def is_commercial_content(text: str) -> bool:
    lower = text.lower()
    terms = (
        "广告", "商业短片", "品牌片", "产品片", "产品展示", "英雄构图",
        "香水", "巧克力", "礼盒", "护肤", "美妆", "汽车",
        "commercial", "advertisement", "brand film", "product film", "packshot",
    )
    return any(term in lower for term in terms)


def forbids_music(text: str) -> bool:
    lower = text.lower()
    return any(term in lower for term in ("不要音乐", "无配乐", "只有环境声", "no music"))


def requests_music(text: str) -> bool:
    lower = text.lower()
    terms = (
        "背景音乐", "配乐", "纯音乐", "钢琴", "弦乐", "吉他", "合成器",
        "音乐进入", "音乐开始", "音乐收束", "bgm", "instrumental", "score builds", "music starts",
    )
    return any(term in lower for term in terms)


def has_instrumental_cue(text: str) -> bool:
    lower = text.lower()
    cues = (
        "纯音乐", "无歌词", "无人声", "无人声演唱", "无哼唱", "不使用人声",
        "不要歌词", "不要人声", "instrumental", "no lyrics", "no vocals", "without vocals",
    )
    return any(cue in lower for cue in cues)


def has_soundable_action(text: str) -> bool:
    lower = text.lower()
    patterns = (
        r"(?:打开|推开|关上|带上).{0,4}门",
        r"(?:放下|丢下|落下|扔下).{0,5}钥匙",
        r"(?:打开|掀开|合上|拆开).{0,5}(?:盒|包装|瓶盖)",
        r"(?:倒入|倒出|注入).{0,5}(?:水|酒|咖啡|饮料|液体)",
        r"(?:放下|落下).{0,5}(?:杯|瓶|产品)",
        r"(?:喷出|喷洒|按下喷头)",
        r"(?:open|close).{0,12}door",
        r"(?:drop|put down).{0,12}keys?",
        r"(?:open|unwrap).{0,12}(?:box|package)",
    )
    return has_food_contact(text) or any(re.search(pattern, lower) for pattern in patterns)


def has_foley_cue(text: str) -> bool:
    lower = text.lower()
    cues = (
        "拟音", "动作声", "音效", "开门声", "关门声", "锁舌", "门轴",
        "钥匙声", "金属清响", "包装纸", "纸张摩擦", "托纸", "咬断声", "脆裂声",
        "咀嚼声", "脚步声", "衣料声", "液体流声", "杯壁", "落台声", "喷雾声",
        "foley", "sound effect", "sfx", "bite sound", "door sound", "key sound",
    )
    return any(cue in lower for cue in cues)


def wants_direct_publish(text: str) -> bool:
    lower = text.lower()
    terms = (
        "直接发布", "直接发社交", "直接发到社交", "无需剪辑", "不用剪辑",
        "免剪辑", "成片直出", "可以直发", "直发社交", "ready to post", "publish-ready",
    )
    return any(term in lower for term in terms)


def has_mix_finish(text: str) -> bool:
    lower = text.lower()
    cues = (
        "音乐轻微下压", "配乐轻微下压", "音乐闪避", "平滑恢复", "自然尾音",
        "自然衰减", "和声终止", "音乐收束", "淡出", "不突然截断", "无爆音",
        "音量跳变", "响度", "duck", "fade out", "natural tail", "no clipping",
    )
    return any(cue in lower for cue in cues)


def shot_segments(text: str) -> list[str]:
    # Copy-ready prompts are often one paragraph, so do not require markers to
    # begin on a new line. Ignore any global preamble before the first marker.
    marker = re.compile(r"(?i)(?=(?:镜头|shot|scene)\s*[#:_：-]?\s*\d+)")
    parts = [part.strip(" \t\r\n。；;") for part in marker.split(text) if part.strip(" \t\r\n。；;")]
    marked = [part for part in parts if re.match(r"(?i)^\s*(?:镜头|shot|scene)\s*[#:_：-]?\s*\d+", part)]
    if marked:
        return marked
    windows = list(re.finditer(r"\b\d+(?:\.\d+)?\s*[-–—至到]\s*\d+(?:\.\d+)?\s*(?:秒|s|sec(?:ond)?s?)\b", text, re.I))
    return [text] * max(1, len(windows))


def check_counts(
    issues: list[Issue],
    refs: dict[str, list[int]],
    counts: dict[str, int | None],
    mode: str,
) -> None:
    for kind, limit in LIMITS.items():
        count = counts[kind]
        if count is not None:
            if count < 0:
                add(issues, "error", "S101", f"{kind} 素材数量不能为负数。", "schema")
                continue
            if count > limit:
                add(issues, "error", "P101", f"{kind} 素材数 {count} 超过 Seedance 2.0 官方上限 {limit}。", "official")
            used = set(refs[kind])
            for index in sorted(used):
                if index < 1 or index > count:
                    add(issues, "error", "B101", f"提示词引用了 {kind} {index}，但只声明上传 {count} 个。", "binding")
            unused = [index for index in range(1, count + 1) if index not in used]
            if unused:
                add(issues, "warning", "H101", f"已上传但未引用的 {kind} 编号：{unused}；为它分配任务或删除素材。", "heuristic")

        unique = sorted(set(refs[kind]))
        if unique and unique != list(range(1, max(unique) + 1)):
            add(issues, "warning", "H102", f"{kind} 引用编号不连续：{unique}；检查上传顺序。", "heuristic")

    image_count = counts["image"] or 0
    video_count = counts["video"] or 0
    audio_count = counts["audio"] or 0
    if audio_count and not (image_count or video_count):
        add(issues, "error", "P102", "全能参考不能只上传音频；至少还需要图片或视频。", "official")
    if mode == "text" and any(refs.values()):
        add(issues, "error", "P103", "text 模式不能包含编号媒体引用。", "official")
    if mode == "first-frame" and counts["image"] is not None and image_count < 1:
        add(issues, "error", "P104", "严格首帧模式至少需要 1 张图片。", "official")
    if mode == "first-last" and counts["image"] is not None and image_count < 2:
        add(issues, "error", "P105", "严格首尾帧模式至少需要 2 张图片。", "official")
    if mode in {"edit", "extend"} and counts["video"] is not None and video_count < 1:
        add(issues, "error", "P106", f"{mode} 模式需要至少 1 个原视频。", "official")
    if mode == "stitch" and counts["video"] is not None and video_count < 2:
        add(issues, "error", "P107", "stitch 模式需要至少 2 个视频。", "official")


def check_reference_jobs(issues: list[Issue], text: str, refs: dict[str, list[int]]) -> None:
    total_unique = sum(len(set(values)) for values in refs.values())
    if total_unique < 2:
        return
    role_words = ("只", "作为", "用于", "参考", "控制", "锁定", "提供", "不迁移", "不要迁移", "only", "controls", "reference")
    for kind, pattern in REF_PATTERNS.items():
        for match in pattern.finditer(text):
            tail = text[match.end() : match.end() + 60]
            if not any(word in tail.lower() for word in role_words):
                add(
                    issues,
                    "warning",
                    "B201",
                    f"{kind} {match.group(1)} 后没有读到明确任务；多素材时写清它控制什么以及不迁移什么。",
                    "binding",
                )


def check_prompt(text: str, args: argparse.Namespace) -> list[Issue]:
    issues: list[Issue] = []
    stripped = text.strip()
    if not stripped:
        add(issues, "error", "S001", "提示词为空。", "schema")
        return issues

    if len(stripped) > 6000:
        add(issues, "warning", "H001", "提示词超过 6000 字符，容易稀释优先级；删除重复细节或拆成连续片段。", "heuristic")
    if args.duration is not None and not 4 <= args.duration <= 15:
        add(issues, "error", "P001", f"时长 {args.duration} 秒不在 Seedance 2.0 当前官方单次 4–15 秒档案内。", "official")

    refs = references_in(stripped)
    counts = {"image": args.images, "video": args.videos, "audio": args.audios}
    check_counts(issues, refs, counts, args.mode)
    check_reference_jobs(issues, stripped, refs)

    lower = stripped.lower()
    if re.search(r"\bseed\s*[:=]\s*-?\d+", lower):
        add(issues, "error", "P201", "不要把未支持的 seed 控制写进 Seedance 2.0 提示词。", "official")
    if "camera_fixed" in lower:
        add(issues, "error", "P202", "不要把未支持的 camera_fixed API 字段写进自然语言提示词。", "official")
    if re.search(r"(?<!\d)(?:4k|8k|16k)(?!\d)", lower):
        add(issues, "warning", "H201", "检测到 4K/8K 等分辨率词；应优先使用平台设置，不把它当作画质保证。", "heuristic")

    beat_montage = is_beat_montage(stripped)
    timed = re.search(r"\b\d+(?:\.\d+)?\s*[-–—至到]\s*\d+(?:\.\d+)?\s*(?:秒|s|sec(?:ond)?s?)\b", stripped, re.I)
    if timed and args.mode not in {"edit", "stitch"} and not beat_montage:
        add(issues, "warning", "P301", "检测到精确时间窗；官方指南指出分秒控制可能不稳定，非编辑/卡点任务优先使用镜头顺序。", "official")

    segments = shot_segments(stripped)
    for index, segment in enumerate(segments, start=1):
        moves = camera_moves(segment)
        if len(moves) > 1:
            add(issues, "warning", "H301", f"镜头 {index} 可能叠加多个主运镜：{moves}；保留一个或说明由参考视频提供复合路径。", "heuristic")

    if args.duration is not None:
        if beat_montage:
            max_shots = 3 if args.duration <= 6 else 5 if args.duration <= 9 else 6 if args.duration <= 12 else 9
        else:
            max_shots = 2 if args.duration <= 6 else 3 if args.duration <= 9 else 4 if args.duration <= 12 else 5
        if len(segments) > max_shots:
            route = "商业卡点蒙太奇" if beat_montage else "标准"
            add(issues, "warning", "H302", f"{args.duration} 秒内检测到约 {len(segments)} 个镜头，超过{route}路线建议 {max_shots} 个。", "heuristic")

    if len(segments) >= 5 and not has_cut_contract(stripped):
        add(issues, "warning", "H303", "五镜头以上但没有读到独立构图/明确硬切契约；模型可能把多个分镜合并成长镜头。", "heuristic")

    beat_audio_terms = (
        "重拍", "鼓点", "节拍", "卡点", "第一拍", "落点", "静音", "音乐抽空",
        "音效", "轻响", "喷雾声", "撞击声", "beat", "downbeat", "sfx", "silence",
    )
    if len(segments) >= 5 and not any(term in lower for term in beat_audio_terms):
        add(issues, "warning", "H304", "高密度分镜没有声音/重拍触发点；为关键切镜绑定动作声、重拍或短暂停顿。", "heuristic")

    product_terms = ("产品", "香水", "瓶身", "包装", "product", "bottle", "packshot")
    hero_terms = ("英雄", "hero", "定格", "停在", "停留", "停住", "完整正面", "主视觉")
    if len(segments) >= 5 and any(term in lower for term in product_terms):
        final_segment = segments[-1].lower()
        if not any(term in final_segment for term in hero_terms):
            add(issues, "warning", "H305", "高密度产品广告的最后镜头没有明确英雄构图或停留；为品牌记忆保留清楚终点。", "heuristic")

    high_risk = has_high_risk_interaction(stripped)
    if high_risk and args.duration is not None and args.duration >= 13 and len(segments) > 5:
        add(
            issues,
            "warning",
            "H306",
            "检测到嘴部/脸部等高风险人物接触，却安排了超过5个镜头；优先降到4–5镜头，并给核心表演保留3–5秒连续镜头。",
            "heuristic",
        )

    if has_food_contact(stripped) and not has_size_cue(stripped):
        add(
            issues,
            "warning",
            "H307",
            "检测到吃/咬食物，但没有读到一口大小或可执行尺寸；过大的食物容易造成手嘴接触僵硬。",
            "heuristic",
        )

    for index, segment in enumerate(segments, start=1):
        segment_lower = segment.lower()
        closes_eyes = any(term in segment_lower for term in ("闭眼", "眼睛闭上", "双眼合上", "closes her eyes", "closes his eyes"))
        relaxes = any(term in segment_lower for term in ("放松", "舒展", "呼气", "吐气", "exhale", "relaxes"))
        smiles = any(term in segment_lower for term in ("微笑", "笑意", "满足", "陶醉", "smile", "satisfied", "bliss"))
        if closes_eyes and relaxes and smiles:
            add(
                issues,
                "warning",
                "H308",
                f"镜头 {index} 同时堆叠闭眼、放松/呼气和满足微笑，容易生成僵硬库存表演；改为触发后的延迟反应，只保留2–3个顺序变化。",
                "heuristic",
            )

    handoff_terms = (
        "承接", "开场状态", "结束状态", "下一镜", "从上一镜", "同一手位",
        "同一位置继续", "从相同位置", "动作匹配", "match action", "continues from the previous shot",
    )
    if high_risk and len(segments) >= 4 and not any(term in lower for term in handoff_terms):
        add(
            issues,
            "warning",
            "H309",
            "多镜头人物接触没有读到明确交接状态；记录上一镜结束手位、道具状态、视线与下一镜开场。",
            "heuristic",
        )

    commercial = is_commercial_content(stripped)
    no_music = forbids_music(stripped)
    has_music = requests_music(stripped)
    if commercial and not no_music and not has_music:
        add(
            issues,
            "warning",
            "H310",
            "商业/产品内容没有读到背景音乐方案；默认写明与产品匹配的纯音乐、速度、核心乐器和能量变化。",
            "heuristic",
        )
    if commercial and has_music and not no_music and not has_instrumental_cue(stripped):
        add(
            issues,
            "warning",
            "H311",
            "商业配乐没有明确纯音乐/无人声/无歌词；直发社交内容应避免模型自行加入歌声或歌词。",
            "heuristic",
        )
    if has_soundable_action(stripped) and not has_foley_cue(stripped):
        add(
            issues,
            "warning",
            "H312",
            "检测到可发声的可见动作，但没有对应动作拟音；为接触瞬间指定材质、远近和同步声音。",
            "heuristic",
        )
    if wants_direct_publish(stripped) and not has_mix_finish(stripped):
        add(
            issues,
            "warning",
            "H313",
            "要求无需剪辑直接发布，但没有读到音乐闪避、音量稳定或结尾自然收束；补充一次生成混音要求。",
            "heuristic",
        )

    fixed = any(term in lower for term in ("固定机位", "镜头固定", "锁定机位", "fixed camera", "locked camera"))
    all_moves = {move for segment in segments for move in camera_moves(segment)}
    if fixed and (all_moves - {"handheld"}):
        add(issues, "error", "C101", "同时要求固定机位和镜头移动，指令冲突。", "contradiction")

    forbids_text = any(term in lower for term in ("画面无字幕", "不要字幕", "不生成字幕", "无任何文字", "不要任何文字", "no subtitles", "no text"))
    requests_text = any(term in lower for term in ("显示字幕", "字幕出现", "添加字幕", "标题出现", "文案出现", "render subtitles", "display subtitles"))
    if forbids_text and requests_text:
        add(issues, "error", "C102", "同时要求禁止文字/字幕和生成文字/字幕。", "contradiction")

    if no_music and has_music:
        add(issues, "error", "C103", "同时要求无音乐和生成背景音乐。", "contradiction")

    if refs["audio"] and not any(term in lower for term in ("音色", "声音", "音乐", "节奏", "鼓点", "环境声", "音效", "voice", "timbre", "music", "rhythm", "ambience", "sound")):
        add(issues, "warning", "B301", "引用了音频，但没有说明它控制音色、内容、音乐、节奏、环境声还是音效。", "binding")

    generic = ("电影级", "高级感", "史诗感", "梦幻感", "震撼", "大师级", "杰作", "极致", "顶级", "cinematic", "masterpiece", "epic")
    generic_hits = sum(lower.count(term.lower()) for term in generic)
    if generic_hits >= 5:
        add(issues, "warning", "H401", "抽象风格词过多；把至少一半替换为具体镜头、光源、动作或声音。", "heuristic")

    connectors = sum(lower.count(term) for term in ("然后", "随后", "紧接着", "同时", "接着", "并且", "突然"))
    if args.duration is not None and connectors > max(3, args.duration // 2):
        add(issues, "warning", "H402", "连续事件连接词很多，动作密度可能超过时长容量。", "heuristic")

    for opening, closing in (("（", "）"), ("{", "}"), ("<", ">"), ("【", "】"), ("〖", "〗")):
        if stripped.count(opening) != stripped.count(closing):
            add(issues, "warning", "S201", f"符号 {opening}{closing} 数量不平衡。", "schema")

    return issues


def print_text(issues: list[Issue]) -> None:
    if not issues:
        print("PASS：未发现静态预检问题。")
        return
    for issue in issues:
        print(f"{issue.severity.upper()} {issue.code} [{issue.basis}]：{issue.message}")
    errors = sum(issue.severity == "error" for issue in issues)
    warnings = sum(issue.severity == "warning" for issue in issues)
    print(f"SUMMARY：{errors} 个错误，{warnings} 个警告。")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args()
    try:
        prompt = read_prompt(args)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"ERROR：{exc}", file=sys.stderr)
        return 1

    issues = check_prompt(prompt, args)
    if args.output_format == "json":
        payload = {
            "ok": not any(issue.severity == "error" for issue in issues),
            "profile": {
                "mode": args.mode,
                "duration": args.duration,
                "images": args.images,
                "videos": args.videos,
                "audios": args.audios,
            },
            "issues": [asdict(issue) for issue in issues],
            "summary": {
                "errors": sum(issue.severity == "error" for issue in issues),
                "warnings": sum(issue.severity == "warning" for issue in issues),
            },
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print_text(issues)

    if any(issue.severity == "error" for issue in issues):
        return 1
    if args.strict and any(issue.severity == "warning" for issue in issues):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
