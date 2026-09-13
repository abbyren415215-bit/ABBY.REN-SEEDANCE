#!/usr/bin/env python3

import argparse
import unittest

from validate_prompt import check_prompt


def args(**overrides):
    values = {
        "duration": 10,
        "mode": "text",
        "images": 0,
        "videos": 0,
        "audios": 0,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


def codes(issues):
    return {issue.code for issue in issues}


class ValidatorTests(unittest.TestCase):
    def test_clean_text_prompt_passes(self):
        prompt = (
            "深夜公寓走廊，一名疲惫的上班族走到家门口，看到门缝透出暖黄灯光后停顿，"
            "握钥匙的手慢慢放松。中景固定观察，窗外雨声和室内水壶声形成对比，最终停在门缝暖光上。"
        )
        self.assertEqual(check_prompt(prompt, args()), [])

    def test_empty_prompt_errors(self):
        self.assertIn("S001", codes(check_prompt("  ", args())))

    def test_duration_outside_profile_errors(self):
        self.assertIn("P001", codes(check_prompt("一只猫抬头看向窗外。", args(duration=30))))

    def test_missing_reference_errors(self):
        prompt = "@图片2（场景）用于背景，人物向门口走去。"
        found = codes(check_prompt(prompt, args(mode="multimodal", images=1)))
        self.assertIn("B101", found)

    def test_text_mode_rejects_references(self):
        prompt = "@图片1（人物）只锁定人物形象。"
        found = codes(check_prompt(prompt, args(mode="text", images=1)))
        self.assertIn("P103", found)

    def test_first_last_needs_two_images(self):
        found = codes(check_prompt("从开场走到结尾。", args(mode="first-last", images=1)))
        self.assertIn("P105", found)

    def test_fixed_camera_conflicts_with_push(self):
        prompt = "固定机位观察人物，随后镜头缓慢推近他的脸。"
        self.assertIn("C101", codes(check_prompt(prompt, args())))

    def test_text_constraint_conflict(self):
        prompt = "画面无字幕，结尾显示字幕‘回家’。"
        self.assertIn("C102", codes(check_prompt(prompt, args())))

    def test_music_constraint_conflict(self):
        prompt = "全程不要音乐，背景音乐逐渐增强。"
        self.assertIn("C103", codes(check_prompt(prompt, args())))

    def test_dense_shot_plan_warns(self):
        prompt = "\n".join(f"镜头{i}：人物完成一个动作。" for i in range(1, 5))
        self.assertIn("H302", codes(check_prompt(prompt, args(duration=8))))

    def test_inline_shots_are_checked_separately(self):
        prompt = "全局设定。镜头1：缓慢推近人物。镜头2：横向跟拍人物。镜头3：缓慢环绕产品。"
        self.assertNotIn("H301", codes(check_prompt(prompt, args(duration=15))))

    def test_subject_holding_is_not_handheld_camera(self):
        prompt = "女主手持蓝色香水，镜头缓慢推近她的手腕。"
        self.assertNotIn("H301", codes(check_prompt(prompt, args(duration=8))))

    def test_exact_timing_warns_outside_edit(self):
        prompt = "0-3秒：人物走近。3-6秒：人物回头。"
        self.assertIn("P301", codes(check_prompt(prompt, args(duration=6))))

    def test_clear_audio_role_does_not_warn(self):
        prompt = (
            "@图片1（人物）只锁定人物身份，不迁移背景。"
            "@音频1（节奏参考）只提供音乐节奏，不迁移原声音内容。人物随重拍转身。"
        )
        found = codes(check_prompt(prompt, args(mode="multimodal", images=1, audios=1)))
        self.assertNotIn("B301", found)

    def test_dense_commercial_montage_is_allowed_at_fifteen_seconds(self):
        prompt = (
            "明确的7镜头商业蒙太奇，每个镜头采用独立构图并以清楚硬切分开，不合并为连续长镜头。"
            "镜头1（约0-2秒，硬切）：大全景，低频第一拍。"
            "镜头2（约2-3秒，硬切）：女主抬起香水瓶。"
            "镜头3（约3-4秒，匹配切）：瓶身微距，玻璃轻响。"
            "镜头4（约4-5秒，重拍硬切）：喷头按下。"
            "镜头5（约5-7秒，材质切）：蓝色瓶身折射海浪。"
            "镜头6（约7-11秒，先留白）：女主闭眼，音乐抽空。"
            "镜头7（约11-15秒，英雄收尾）：完整正面产品主视觉，镜头停住。"
        )
        found = codes(check_prompt(prompt, args(duration=15)))
        for code in ("P301", "H302", "H303", "H304", "H305"):
            self.assertNotIn(code, found)

    def test_dense_unmarked_sequence_warns_about_merge(self):
        prompt = "".join(f"镜头{i}：人物完成一个动作。" for i in range(1, 8))
        found = codes(check_prompt(prompt, args(duration=15)))
        self.assertIn("H302", found)
        self.assertIn("H303", found)
        self.assertIn("H304", found)

    def test_overloaded_montage_still_warns(self):
        prompt = (
            "明确的10镜头商业蒙太奇，每个镜头独立构图，全部硬切，切镜跟随重拍。"
            + "".join(f"镜头{i}：产品完成一个简单动作。" for i in range(1, 10))
            + "镜头10：产品英雄构图停住。"
        )
        self.assertIn("H302", codes(check_prompt(prompt, args(duration=15))))

    def test_high_risk_eating_ad_warns_when_too_dense(self):
        prompt = (
            "明确的8镜头商业蒙太奇，全部硬切，切镜跟随重拍。"
            + "".join(f"镜头{i}：女主拿着一口大小的巧克力完成一个简单动作。" for i in range(1, 7))
            + "镜头7：女主咬下巧克力。"
            + "镜头8：产品英雄构图停住。"
        )
        self.assertIn("H306", codes(check_prompt(prompt, args(duration=15))))

    def test_food_contact_needs_size_cue(self):
        prompt = "镜头1：女主拿起巧克力。镜头2：女主咬下巧克力。镜头3：产品英雄构图停住。"
        self.assertIn("H307", codes(check_prompt(prompt, args(duration=15))))

    def test_stacked_stock_reaction_warns(self):
        prompt = "镜头1：女主咬下一小块巧克力。镜头2：她立刻闭眼，肩膀放松，长呼气并露出满足微笑。"
        self.assertIn("H308", codes(check_prompt(prompt, args(duration=10))))

    def test_high_risk_multishot_needs_handoff(self):
        prompt = (
            "镜头1：女主拿起一口大小的巧克力。"
            "镜头2：女主送到唇边。"
            "镜头3：女主咬下一小口。"
            "镜头4：产品英雄构图停住。"
        )
        self.assertIn("H309", codes(check_prompt(prompt, args(duration=15))))

    def test_five_shot_eating_ad_with_handoff_avoids_new_warnings(self):
        prompt = (
            "明确的5镜头商业蒙太奇，每镜独立构图并以清楚硬切分开，切镜跟随重拍。"
            "镜头1：产品微距。"
            "镜头2：女主右手夹起一口大小的巧克力，结束状态停在下巴下方。"
            "镜头3：承接上一镜同一手位，把巧克力送到唇边。"
            "镜头4：从相同位置继续，只咬下一小口；手降低到锁骨高度，眼睛保持睁开。"
            "镜头5：产品英雄构图停住。"
        )
        found = codes(check_prompt(prompt, args(duration=15)))
        for code in ("H306", "H307", "H308", "H309"):
            self.assertNotIn(code, found)

    def test_commercial_prompt_needs_music_plan(self):
        prompt = "高端巧克力广告，产品英雄构图停在打开的礼盒上。"
        self.assertIn("H310", codes(check_prompt(prompt, args(duration=10))))

    def test_commercial_music_should_be_instrumental(self):
        prompt = "高端香水广告，背景音乐使用钢琴和柔和弦乐，最后停在产品英雄构图。"
        self.assertIn("H311", codes(check_prompt(prompt, args(duration=10))))

    def test_visible_soundable_action_needs_foley(self):
        prompt = "人物推开木门，走进客厅后放下钥匙。"
        self.assertIn("H312", codes(check_prompt(prompt, args(duration=8))))

    def test_direct_publish_needs_mix_finish(self):
        prompt = "社交网站无需剪辑直接发布，使用无歌词纯音乐，人物走进房间。"
        self.assertIn("H313", codes(check_prompt(prompt, args(duration=8))))

    def test_publish_ready_ad_with_sound_plan_avoids_sound_warnings(self):
        prompt = (
            "高端巧克力广告，生成后无需剪辑直接发布。使用无歌词、无人声演唱的原创感纯音乐，"
            "暖色毡音钢琴与轻柔弦乐；人物打开礼盒时加入同步纸张摩擦拟音，咬下一口大小的巧克力时"
            "加入克制的咬断声。关键拟音出现时配乐轻微下压，随后平滑恢复，结尾在产品英雄构图上"
            "形成短和声终止并保留自然尾音。"
        )
        found = codes(check_prompt(prompt, args(duration=15)))
        for code in ("H310", "H311", "H312", "H313"):
            self.assertNotIn(code, found)


if __name__ == "__main__":
    unittest.main()
