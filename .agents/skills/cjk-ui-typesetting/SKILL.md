---
name: cjk-ui-typesetting
description: >-
  Universal typography and text layout engine for CJK and mixed-language UI/Web.
  Use when detecting or fixing orphan words/lines (孤字/孤行/widows/orphans),
  Kinsoku line-breaking rules (避头尾), visual balance in multi-line titles/cards,
  responsive word wrapping, or typewriter/stepped text streaming UX (anti-jitter,
  caret alignment, skip UX).
---

# CJK & UI Typesetting: Universal Text Layout & Stepped Streaming Guide

A comprehensive, production-grade guide for detecting, articulating, and resolving typography flaws in Web, Mobile, and Game user interfaces—especially for Chinese/Japanese/Korean (CJK) and mixed-language layouts.

---

## 1. When to Activate This Skill

Activate this skill when:
- Designing or reviewing UI with headings, cards, subtitles, dialog bubbles, banners, or badges.
- Observing **orphan words** (单字成行 / 寡行) at the end of a block or paragraph.
- Observing **punctuation on the start of a line** or opening brackets on the end of a line (**避头尾违规**).
- Reviewing multi-line titles where lines are heavily lopsided (e.g. Line 1 has 30 characters, Line 2 has 2 characters).
- Implementing or refining **AI streaming / typewriter text output** (preventing horizontal centering jitter, stroke ghosting, desynchronized carets, or lack of skip interaction).
- Asking for a typography audit or layout polish in any Web or UI framework.

---

## 2. Core Typography Rules & Universal Standards

### Rule 1: Zero-Orphan Policy (杜绝单字成行与孤字孤页)
* **What is an Orphan (孤字 / 寡行 / 孤行)**:
  - In a paragraph or multi-line block, the last line containing only a single word or fewer than 2~3 CJK characters.
  - In paged or multi-bubble text (e.g., game subtitles, modal dialogs), a subsequent page containing only 1~3 characters.
* **Standard**:
  - The last line of any block **MUST contain at least 4~6 CJK characters** (or 2+ words in English).
  - If a split leaves a trailing orphan, pull words/characters from the preceding line into the current line, or re-balance the entire block.

### Rule 2: Kinsoku Shori (CJK 避头尾规则)
Punctuation marks must respect line boundaries:
* **No Head Characters (避头标点 - 不能出现在行首)**:
  - Full stops / commas: `。` `，` `、` `.` `,` `;` `；` `:` `：` `！` `!` `？` `?`
  - Closing brackets / quotes: `）` `)` `》` `>` `」` `』` `】` `]` `”` `’`
  - Hyphens & tildes: `～` `~` `—` `…`
  *Fix*: If a break lands before these characters, move the preceding character to the new line together with the punctuation, or shrink letter-spacing.
* **No Tail Characters (避尾标点 - 不能出现在行末)**:
  - Opening brackets / quotes: `（` `(` `《` `<` `「` `『` `【` `[` `“` `‘`
  *Fix*: Move the opening punctuation to the start of the next line with its following character.

### Rule 3: Visual Balanced Wrapping (两行与多行对称视觉平衡)
* **The Ragged-Line Problem**:
  - In 2-line headings, cards, or subtitles, standard CSS `break-word` fills Line 1 to 100% capacity and spills remaining 2 words onto Line 2. This creates an awkward "bottom-heavy" or "lopsided" visual silhouette.
* **Balancing Objective**:
  - Minimize $|L_1 - L_2| + \text{Penalties}$, where penalties heavily disfavor short second lines ($L_2 < 4$).
  - For 2-line titles, an optimal visual ratio is roughly $1:1$ or $1.2:1$ (top line slightly longer or symmetrical).

### Rule 4: Stepped Typewriter Streaming UX (打字机流式规范)
* **Zero Horizontal Jitter (杜绝居中抖动)**:
  - If text is center-aligned (`text-align: center`), **DO NOT** dynamically concatenate characters into the DOM/Label, as every added character shifts earlier characters to the left.
  - *Solution*: Pre-render the full line/layout and advance visibility using `visible_characters` or container clipping.
* **No Alpha Ghosting (杜绝描边 Alpha 穿透)**:
  - Many rendering engines (Godot, Canvas, certain CSS `text-shadow` configurations) draw outlines even when text color alpha is `0`.
  - *Solution*: Never use transparent BBCode/CSS color to hide pending text. Use character counts or CSS `mask-image`.
* **Caret Synchronization (击锤光标 `▌`)**:
  - The cursor must calculate exact line-height and active line prefix width in real-time, following each stepped glyph.
* **Punctuation Breathing & Skip Handshake**:
  - Add pause multipliers: commas (1.5x), periods/exclamations/question marks (3x).
  - First click/keypress: immediately completes current page/bubble text. Second click/keypress: advances to next page/state.

---

## 3. Web & CSS Implementation Guide

### A. Modern CSS (Zero-JS)
```css
/* 1. Headings (up to 6 lines): Automatically balances line lengths */
.heading-balanced {
  text-wrap: balance; /* Chrome 114+, Safari 17.5+, Firefox 121+ */
}

/* 2. Paragraphs: Prevents orphan words at paragraph endings */
.text-pretty {
  text-wrap: pretty; /* Chrome 117+, Safari 17.5+ */
  overflow-wrap: break-word; /* Do NOT use break-all */
  word-break: normal;
}

/* 3. Mixed CJK & Latin word breaking without word slicing */
.cjk-text-container {
  word-break: keep-all; /* For CJK, breaks at natural punctuation / phrases */
  overflow-wrap: anywhere;
}
```

### B. HTML & Semantic Joiners
When modern CSS is unsupported or precise control is required:
* **Glue the last two words with Non-Breaking Space (`&nbsp;`)**:
  ```html
  <!-- BAD: '方案' may drop onto line 2 alone -->
  <h2>打造更直观的前端交互设计方案</h2>

  <!-- GOOD: '设计' and '方案' will never be split across lines -->
  <h2>打造更直观的前端交互设计&nbsp;方案</h2>
  ```
* **Use Word Joiner (`&#8288;` or `\u2060`)**:
  Glues punctuation to the preceding word without introducing visual spacing.
* **Wrap unbreakable phrases in `inline-block`**:
  ```html
  <h2><span class="inline-block">打造更直观的</span><span class="inline-block">前端交互方案</span></h2>
  ```

### C. JavaScript & `Intl.Segmenter` (Native CJK Word Boundary)
Modern browsers natively support CJK phrase segmentation:
```typescript
function balanceTwoLines(text: string): [string, string] {
  const segmenter = new Intl.Segmenter('zh-CN', { granularity: 'word' });
  const words = Array.from(segmenter.segment(text)).map(s => s.segment);
  if (words.length <= 1) return [text, ''];

  let bestSplit = 1;
  let minDiff = Infinity;
  for (let i = 1; i < words.length; i++) {
    const l1 = words.slice(0, i).join('');
    const l2 = words.slice(i).join('');
    // Heavy penalty for short 2nd line (< 4 chars)
    const penalty = l2.length < 4 ? 100 : 0;
    const diff = Math.abs(l1.length - l2.length) + penalty;
    if (diff < minDiff) {
      minDiff = diff;
      bestSplit = i;
    }
  }
  return [words.slice(0, bestSplit).join(''), words.slice(bestSplit).join('')];
}
```

---

## 4. Game & Native Engine Guide (Godot, Flutter, Canvas)

### Godot Engine
* **Wrap Mode**: Set `autowrap_mode = TextServer.AUTOWRAP_WORD_SMART` (never `AUTOWRAP_ARBITRARY`).
* **Stepped Output**:
  ```gdscript
  # Advance via visible_characters
  label.text = full_page_text
  label.visible_characters = 0
  while label.visible_characters < total_chars:
      label.visible_characters += 1
      _update_caret_position(label)
      await get_tree().create_timer(speed).timeout
  ```
* **Paragraph-First Paging**:
  Always split by `\n` first before line-wrapping:
  ```gdscript
  var paragraphs := raw_text.split("\n")
  for para in paragraphs:
      pages.append_array(_layout_paragraph(para, max_width, font))
  ```

### Flutter
* Use `TextSpan` with `Characters` API to measure glyph count.
* Avoid raw `SoftWrap` without `TextWidthBasis.longestLine`.
* Use `selectionHeightStyle` and `TextPainter` to accurately anchor the typewriter cursor.

---

## 5. Team Communication & Terminology Card

When reporting or discussing these issues with developers, designers, or product managers, use standard industry terminology to achieve instant clarity:

| Visual Symptom (视觉现象) | Formal Typography Term (专业术语) | Developer / Designer Action Phrase (提议话术) |
| :--- | :--- | :--- |
| 标题最后单独掉下来 1~2 个字 | **孤行 / 寡行 (Widow / Orphan)** | "建议在标题样式上添加 `text-wrap: balance`，或在末尾两个词间增加 `&nbsp;` 消除孤行。" |
| 句号、逗号、闭括号出现在下一行最开头 | **避头尾违规 (Kinsoku Violation)** | "标点落入行首违反了避头尾规范，建议引入 CJK 避头尾断行处理。" |
| 两行标题第一行极长、第二行极短 | **视觉失衡 (Ragged Line / Lopsided Wrap)** | "两行标题视觉重心偏左，建议采用两行对称折行算法进行长度平衡。" |
| 英文单词或专有名词被暴力劈成两截 | **截断碎词 (Arbitrary Word Slicing)** | "请将 `word-break: break-all` 改为 `word-break: normal; overflow-wrap: break-word`。" |
| 居中对齐时打字机每敲一字整行向左抖动 | **居中抖动 (Center-Alignment Jitter)** | "打字机采用动态拼接导致居中重绘抖动，请改用完整布局 + 步进可见字符数控制。" |
| 隐藏待显文字时出现整行黑色描边鬼影 | **描边通道泄露 (Outline Alpha Bleed)** | "文字透明并未抑制描边通道渲染，建议改用字符索引裁剪代替 Alpha 透明度。" |

*Full terminology guide available in [references/terminology.md](./references/terminology.md).*

---

## 6. Automated Audit Workflow (Agent Operational Checklist)

When tasked with auditing or polishing typography in a repository:

1. **Scan**: Run the automated audit script on content or UI files:
   ```bash
   python3 scripts/audit_typesetting.py --path <target_dir_or_file>
   ```
2. **Diagnose**:
   - Count lines where length $< 3$ CJK characters (orphans).
   - Check first characters of every line against `避头标点` set.
   - Check last characters of every line against `避尾标点` set.
3. **Fix**:
   - For Web: Apply modern CSS (`text-wrap: balance`, `overflow-wrap: break-word`) or insert non-breaking spaces.
   - For Game/App: Apply the balanced 2-line break algorithm and kinsoku re-distributor.
4. **Verify**:
   - Re-run `audit_typesetting.py` to confirm `0 orphans, 0 kinsoku violations`.
   - Inspect edge-case viewport widths (Mobile 360px, Tablet 768px, Desktop 1440px).
