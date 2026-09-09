#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""養鷹達人例句規範 v2 機械檢查。

用法：
  python3 tools/check_sentences.py                # 全庫回歸掃描（讀 index.html）
  python3 tools/check_sentences.py --draft 檔案   # 待匯入草稿預檢

草稿檔行格式與 SEED2／SEED3 條目相同（可含結尾逗號與註解行）：
  ['word','中文','Example sentence.',7],

進場順序＝SEED（Fry 2nd 100）→ SEED2（3rd 100）→ SEED3（4th 100）→ 草稿。

機械層規則（FAIL 會使 exit code = 1）：
  1. 目標字必須出現在例句中（7/21 thought 句教訓）
  2. 句長 5–9 字（規範 v2；只適用 Fry 3rd 100 List 3 起與所有草稿，舊批次豁免）
  3. 不可引用「尚未進場」的批次字（進場順序＝陣列順序；EXTRA_KNOWN 內的字降為提醒）
草稿模式另列每句表外字與撇號提醒，供人工驗品味層（加壓字配置、獎勵名詞）。
"""
import argparse, re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"

# ── 課外已知字清單（媽媽確認後就地增補；全部小寫）────────────────────
# 依據：興趣清單（守宮/昆蟲、足球、摺紙手作、工作細胞）＋已核准獎勵名詞＋真人。
EXTRA_KNOWN = {
    "gecko", "geckos", "football", "bird", "birds", "sun", "safe", "class",
    "taipei", "mantis", "harper", "cells", "blood", "paper", "feet",
    "eagle", "eagles", "sky", "bug", "bugs", "leaf", "ball", "goal",
    "park", "road", "rain", "team", "game", "games", "video", "pet",
    "box", "door", "tape", "toy", "cool", "sunday",
    "dad", "mom", "please",
    "cats", "apollo", "midnight", "japan",   # 2026-08-06：過世家貓名（Apollo/Midnight）、全家日本行——媽媽於 List 7–10 驗收時確認
}

# 刻意預習字：先以加壓字身分放進較早批次的例句曝露、之後才成為 SEED 目標字。
# 孩子在該字正式進場前已聽讀過（設計紅利），故回溯掃描不視為順序違規。
# eat/grow（7/16、7/21 例句）→ List 7 目標；watch/stop（7/21 例句）→ List 8–9 目標。
# 2026-09-09 SEED3 匯入補入：下列 9 字早已散見於 SEED／SEED2 例句，成為 4th 100 目標字。
PREVIEWED_BEFORE_ENTRY = {
    "eat", "grow", "watch", "stop",
    "birds", "dog", "door", "fish", "red", "short", "stand", "sun", "today",
}

# Fry 第 1 個 100 字（入 App 前已學，視為基底詞彙）
FRY_1ST_100 = set("""the of and a to in is you that it he was for on are as with his they i
at be this have from or one had by words but not what all were we when your can said there
use an each which she do how their if will up other about out many then them these so some
her would make like him into time has look two more write go see number no way could people
my than first water been called who am its now find long down day did get come made may part""".split())

# 常見縮寫展開（用於詞彙歸屬判定；縮寫本身若是 SEED 目標字則直接命中）
CONTRACTIONS = {
    "don't": ["do", "not"], "it's": ["it", "is"], "i'm": ["i", "am"],
    "that's": ["that", "is"], "can't": ["can", "not"], "isn't": ["is", "not"],
    "let's": ["let", "us"], "we're": ["we", "are"], "he's": ["he", "is"],
    "she's": ["she", "is"], "you're": ["you", "are"], "won't": ["will", "not"],
    "didn't": ["did", "not"], "doesn't": ["does", "not"],
}

ENTRY_RE = re.compile(
    r"\[\s*'((?:[^'\\]|\\.)*)'\s*,\s*'(?:[^'\\]|\\.)*'\s*,\s*'((?:[^'\\]|\\.)*)'\s*,\s*(\d+)\s*\]")


def unescape(s):
    return s.replace("\\'", "'").replace('\\"', '"')


def tokens(sentence):
    return [t.strip("'").lower() for t in re.findall(r"[A-Za-z']+", sentence) if t.strip("'")]


def stem_candidates(w):
    out = set()
    for suf in ("s", "es", "ed", "d", "ing"):
        if w.endswith(suf) and len(w) > len(suf) + 1:
            base = w[: -len(suf)]
            out.add(base)
            if suf in ("ed", "ing") and len(base) > 2 and base[-1] == base[-2]:
                out.add(base[:-1])          # running → run
            if suf in ("ed", "es", "ing"):
                out.add(base + "e")          # closed → close
    if w.endswith("ies") and len(w) > 4:
        out.add(w[:-3] + "y")               # flies → fly
    return out


def parse_array(src, name):
    m = re.search(rf"const {name}\s*=\s*\[(.*?)\]\.map", src, re.S)
    if not m:
        sys.exit(f"❌ 在 index.html 找不到 {name} 陣列")
    return [(unescape(a), unescape(s), int(n)) for a, s, n in ENTRY_RE.findall(m.group(1))]


def known_lookup(word, vocab):
    """回傳 True 若 word（含輕量詞形變化、縮寫展開）屬於 vocab 集合。"""
    if word in vocab:
        return True
    if word in CONTRACTIONS:
        return all(p in vocab or p in FRY_1ST_100 for p in CONTRACTIONS[word])
    return any(b in vocab for b in stem_candidates(word))


def check(entries, base_vocab, seed_order, v2_from_idx, draft_mode):
    """entries: [(word, sentence, batch_label, list_num, global_idx)]；回傳 (fails, reports)"""
    fails, reports = 0, []
    for word, sentence, batch, lst, idx in entries:
        w = word.lower()
        toks = tokens(sentence)
        problems, notes = [], []

        # 規則 1：目標字在句中
        if w not in toks:
            problems.append(f"句中沒有目標字「{word}」")

        # 規則 2：句長 5–9（v2 適用範圍）
        if draft_mode or idx >= v2_from_idx:
            if not 5 <= len(toks) <= 9:
                problems.append(f"句長 {len(toks)} 字（規範 5–9）")

        # 規則 3：進場順序（只約束 SEED2 / SEED3 / 草稿的字）
        for t in set(toks):
            if t == w:
                continue
            j = seed_order.get(t)
            if j is not None and j > idx:
                if t in EXTRA_KNOWN:
                    notes.append(f"「{t}」晚進場（List {entries_list_num(seed_order, j)}）但屬課外已知，可用")
                elif t in PREVIEWED_BEFORE_ENTRY:
                    notes.append(f"「{t}」為刻意預習字（先入舊例句曝露、後成目標字），可用")
                else:
                    problems.append(f"引用尚未進場的字「{t}」（陣列序 {j} > {idx}）")

        # 草稿模式：表外字清點＋撇號提醒
        if draft_mode:
            entered = {t2 for t2, j2 in seed_order.items()
                       if isinstance(j2, int) and j2 <= idx}
            vocab_now = base_vocab | entered
            unknown = [t for t in toks
                       if t != w and seed_order.get(t) is None
                       and not known_lookup(t, vocab_now)
                       and t not in EXTRA_KNOWN]
            if unknown:
                notes.append("表外字：" + "、".join(unknown) + "（人工判定：加壓字／新獎勵名詞／該換字）")
            if any("'" in t for t in toks):
                notes.append("含撇號——照常成磚，首遇時媽媽提點一句")

        if problems:
            fails += 1
            reports.append(f"❌ {batch} List {lst}〈{word}〉“{sentence}”\n     " + "；".join(problems))
        elif notes:
            reports.append(f"⚠️ {batch} List {lst}〈{word}〉“{sentence}”\n     " + "；".join(notes))
    return fails, reports


def entries_list_num(order_map, idx):
    return order_map.get("__listnum__", {}).get(idx, "?")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--draft", help="待匯入草稿檔（行格式同 SEED2 條目）")
    args = ap.parse_args()

    src = INDEX.read_text(encoding="utf-8")
    seed1 = parse_array(src, "SEED")
    seed2 = parse_array(src, "SEED2")
    seed3 = parse_array(src, "SEED3")

    # 受順序約束的字＝SEED2 → SEED3 →（草稿）串成一條進場序；SEED（已學）只當基底詞彙
    ordered = [("3rd 100", e) for e in seed2] + [("4th 100", e) for e in seed3]
    base_vocab = FRY_1ST_100 | {w.lower() for w, _, _ in seed1}
    seed_order = {e[0].lower(): i for i, (_, e) in enumerate(ordered)}
    seed_order["__listnum__"] = {i: e[2] for i, (_, e) in enumerate(ordered)}
    v2_from_idx = next((i for i, (_, e) in enumerate(ordered) if e[2] >= 3), len(ordered))

    if args.draft:
        raw = pathlib.Path(args.draft).read_text(encoding="utf-8")
        draft = [(unescape(a), unescape(s), int(n)) for a, s, n in ENTRY_RE.findall(raw)]
        if not draft:
            sys.exit("❌ 草稿檔解析不到任何條目（行格式須同 SEED2：['word','中文','句子',listNum],）")
        # 行數守衛：像條目的行數 ≠ 解析成功數 → 必有壞行（常見：句中撇號未寫成 \'）
        entry_like = sum(1 for ln in raw.splitlines() if re.match(r"\s*\[", ln))
        if entry_like != len(draft):
            sys.exit(f"❌ 草稿有 {entry_like} 行條目但只解析出 {len(draft)} 句——"
                     f"有壞行被跳過（檢查撇號是否寫成 \\'、引號是否配對），修正後重跑")
        # 草稿字接在 SEED3 之後進場；草稿內部也依行序
        offset = len(ordered)
        for i, (w, _, n) in enumerate(draft):
            seed_order[w.lower()] = offset + i
            seed_order["__listnum__"][offset + i] = n
        entries = [(w, s, "草稿", n, offset + i) for i, (w, s, n) in enumerate(draft)]
        fails, reports = check(entries, base_vocab, seed_order, v2_from_idx, draft_mode=True)
        print(f"📋 草稿預檢：{len(draft)} 句"
              f"（接續全庫 {len(seed1)+len(ordered)} 字之後進場）\n")
    else:
        entries = [(e[0], e[1], b, e[2], i) for i, (b, e) in enumerate(ordered)]
        fails, reports = check(entries, base_vocab, seed_order, v2_from_idx, draft_mode=False)
        print(f"🔍 全庫回歸掃描：SEED {len(seed1)} 字（豁免 v2 句長）"
              f"＋ SEED2 {len(seed2)} 字 ＋ SEED3 {len(seed3)} 字\n")

    for r in reports:
        print(r)
    print(f"\n{'❌' if fails else '✅'} FAIL {fails} ｜ 提醒 {sum(1 for r in reports if r.startswith('⚠️'))}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
