#!/usr/bin/env python3
"""
audit_typesetting.py
--------------------
Universal typography and text layout auditor for CJK and mixed-language content.
Scans text, markdown, CSV, JSON, or source code files for:
  1. Orphan lines / words (孤行 / 单字成行)
  2. Kinsoku line-breaking violations (避头尾标点违规)
  3. Visual line imbalance (两行视觉悬殊失衡)

Usage:
    python3 audit_typesetting.py --path <file_or_dir> [--max-col 24] [--verbose]
"""

import sys
import os
import re
import argparse
from typing import List, Tuple, Dict, Any

# Kinsoku line-start forbidden characters
KINSOKU_HEAD = set("!%),.:;?]}¢°’”‰′″℃、。々〉》」』】〕〞〟ゝゞ・ヽヾ！％），．：；？］｝～…—")

# Kinsoku line-end forbidden characters
KINSOKU_TAIL = set("$([\\{£¥‘“〈《「『【〔〝﹙﹛﹝＄（［｛")

def is_cjk(ch: str) -> bool:
    cp = ord(ch)
    return (
        0x4E00 <= cp <= 0x9FFF or
        0x3400 <= cp <= 0x4DBF or
        0x20000 <= cp <= 0x2A6DF or
        0xF900 <= cp <= 0xFAFF
    )

def cjk_len(s: str) -> int:
    """Calculates display length where CJK glyphs count as 2, ASCII as 1."""
    length = 0
    for ch in s:
        length += 2 if is_cjk(ch) else 1
    return length

class TypesettingAuditor:
    def __init__(self, min_tail_chars: int = 3, max_ratio: float = 3.0):
        self.min_tail_chars = min_tail_chars
        self.max_ratio = max_ratio
        self.issues: List[Dict[str, Any]] = []

    def audit_lines(self, file_path: str, line_no: int, lines: List[str]) -> None:
        if not lines:
            return

        for idx, line in enumerate(lines):
            line_str = line.strip()
            if not line_str:
                continue

            # 1. Kinsoku Line-Head violation
            first_char = line_str[0]
            if first_char in KINSOKU_HEAD:
                self.issues.append({
                    "file": file_path,
                    "line": line_no + idx,
                    "type": "KINSOKU_HEAD",
                    "text": line_str,
                    "msg": f"行首出现避头标点 '{first_char}'"
                })

            # 2. Kinsoku Line-Tail violation
            last_char = line_str[-1]
            if last_char in KINSOKU_TAIL:
                self.issues.append({
                    "file": file_path,
                    "line": line_no + idx,
                    "type": "KINSOKU_TAIL",
                    "text": line_str,
                    "msg": f"行末出现避尾标点 '{last_char}'"
                })

            # 3. Orphan line check (if it's the last line of a multi-line block)
            if len(lines) > 1 and idx == len(lines) - 1:
                # count CJK characters in trailing line
                cjk_count = sum(1 for ch in line_str if is_cjk(ch))
                word_count = len(line_str.split())
                if (cjk_count > 0 and cjk_count < self.min_tail_chars) or (cjk_count == 0 and word_count < 2):
                    self.issues.append({
                        "file": file_path,
                        "line": line_no + idx,
                        "type": "ORPHAN_LINE",
                        "text": line_str,
                        "msg": f"末行字数过少构成孤行 (CJK: {cjk_count} 字)"
                    })

        # 4. Visual imbalance check for 2-line blocks
        if len(lines) == 2:
            l1, l2 = lines[0].strip(), lines[1].strip()
            len1, len2 = cjk_len(l1), cjk_len(l2)
            if len1 > 0 and len2 > 0:
                ratio = max(len1, len2) / min(len1, len2)
                if ratio > self.max_ratio:
                    self.issues.append({
                        "file": file_path,
                        "line": line_no,
                        "type": "VISUAL_IMBALANCE",
                        "text": f"L1: {l1} | L2: {l2}",
                        "msg": f"两行长度比例悬殊 (长度比 {ratio:.1f}:1 > {self.max_ratio}:1)"
                    })

    def scan_text(self, text: str, file_path: str = "<stdin>") -> None:
        paragraphs = text.split("\n\n")
        line_counter = 1
        in_code_block = False

        for p in paragraphs:
            raw_lines = p.split("\n")
            filtered_lines = []
            
            for line in raw_lines:
                stripped = line.strip()
                if stripped.startswith("```"):
                    in_code_block = not in_code_block
                    continue
                if not in_code_block:
                    filtered_lines.append(line)
                else:
                    # preserve line height
                    filtered_lines.append("")

            self.audit_lines(file_path, line_counter, filtered_lines)
            line_counter += len(raw_lines) + 1

    def scan_file(self, file_path: str) -> None:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            self.scan_text(content, file_path)
        except Exception as e:
            print(f"Error reading {file_path}: {e}", file=sys.stderr)

    def scan_path(self, target_path: str, extensions: Tuple[str, ...] = (".txt", ".md", ".csv", ".json", ".html")) -> None:
        if os.path.isfile(target_path):
            self.scan_file(target_path)
        elif os.path.isdir(target_path):
            for root, _, files in os.walk(target_path):
                for f in files:
                    if f.endswith(extensions):
                        self.scan_file(os.path.join(root, f))

def main():
    parser = argparse.ArgumentParser(description="Audit CJK text layout and typography.")
    parser.add_argument("--path", required=True, help="Path to file or directory to scan.")
    parser.add_argument("--min-tail", type=int, default=3, help="Minimum CJK characters required on trailing line.")
    parser.add_argument("--max-ratio", type=float, default=3.0, help="Maximum allowed length ratio for 2-line headings.")
    parser.add_argument("--verbose", action="store_true", help="Print all scanned checks.")
    args = parser.parse_args()

    auditor = TypesettingAuditor(min_tail_chars=args.min_tail, max_ratio=args.max_ratio)
    auditor.scan_path(args.path)

    print(f"==================================================")
    print(f"== 文本排版审查报告 (Typography Audit Report) ==")
    print(f"==================================================")
    print(f"扫描目标: {args.path}")
    print(f"发现问题数: {len(auditor.issues)}")

    if not auditor.issues:
        print("\n✅ PASS: 未发现孤行、孤字或避头尾排版缺陷。")
        sys.exit(0)
    else:
        print("\n❌ 发现排版缺陷如下：")
        for i, issue in enumerate(auditor.issues, 1):
            print(f"[{i}] [{issue['type']}] {issue['file']}:{issue['line']}")
            print(f"    说明: {issue['msg']}")
            print(f"    内容: {issue['text']}")
        sys.exit(1)

if __name__ == "__main__":
    main()
