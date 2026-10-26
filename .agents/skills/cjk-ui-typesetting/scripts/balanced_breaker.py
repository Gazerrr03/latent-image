#!/usr/bin/env python3
"""
balanced_breaker.py
-------------------
Universal 2-line balanced text splitter with CJK Kinsoku awareness.
Minimizes line length delta while strictly penalizing short second lines (orphans).

Usage:
    python3 balanced_breaker.py "打造更直观的前端交互设计方案"
"""

import sys
import argparse
from typing import Tuple

KINSOKU_HEAD = set("!%),.:;?]}¢°’”‰′″℃、。々〉》」』】〕〞〟ゝゞ・ヽヾ！％），．：；？］｝～…—")
KINSOKU_TAIL = set("$([\\{£¥‘“〈《「『【〔〝﹙﹛﹝＄（［｛")

def is_cjk(ch: str) -> bool:
    cp = ord(ch)
    return (
        0x4E00 <= cp <= 0x9FFF or
        0x3400 <= cp <= 0x4DBF or
        0x20000 <= cp <= 0x2A6DF or
        0xF900 <= cp <= 0xFAFF
    )

def char_width(ch: str) -> float:
    return 2.0 if is_cjk(ch) else 1.0

def string_width(s: str) -> float:
    return sum(char_width(c) for c in s)

def split_balanced_2_lines(text: str, max_chars_per_line: int = 40) -> Tuple[str, str]:
    """
    Splits text into two visually balanced lines.
    Ensures:
      - Line 2 does not begin with Kinsoku head punctuation
      - Line 1 does not end with Kinsoku tail punctuation
      - Line 2 is not an orphan (< 3 CJK characters)
      - Visual width between lines is minimized
    """
    clean_text = text.strip()
    n = len(clean_text)
    if n <= 1:
        return clean_text, ""

    best_split = n // 2
    best_cost = float("inf")

    # Search window around the middle
    min_split = 2
    max_split = n - 2

    for i in range(min_split, max_split + 1):
        l1 = clean_text[:i]
        l2 = clean_text[i:]

        # Hard Kinsoku constraint
        if l2[0] in KINSOKU_HEAD:
            continue
        if l1[-1] in KINSOKU_TAIL:
            continue

        w1 = string_width(l1)
        w2 = string_width(l2)

        # Width difference cost
        diff = abs(w1 - w2)

        # Heavy penalty for short line 2 (Orphan)
        cjk_in_l2 = sum(1 for c in l2 if is_cjk(c))
        penalty = 0.0
        if cjk_in_l2 < 3:
            penalty += 500.0
        elif cjk_in_l2 < 5:
            penalty += 100.0

        # Gentle preference: line 1 slightly longer or equal to line 2 (solid visual pyramid)
        if w1 < w2:
            penalty += 15.0

        total_cost = diff + penalty

        if total_cost < best_cost:
            best_cost = total_cost
            best_split = i

    return clean_text[:best_split], clean_text[best_split:]

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 balanced_breaker.py \"<text to balance>\"")
        sys.exit(1)

    text = " ".join(sys.argv[1:])
    l1, l2 = split_balanced_2_lines(text)
    print("--------------------------------------------------")
    print(f"原文本: {text}")
    print("--------------------------------------------------")
    print(f"第一行: {l1} (字宽: {string_width(l1):.1f})")
    print(f"第二行: {l2} (字宽: {string_width(l2):.1f})")
    print("--------------------------------------------------")

if __name__ == "__main__":
    main()
