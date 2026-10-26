# Web 前端排版与流式文本模式库 (Web Patterns)

涵盖现代 CSS 特性、Tailwind 配置、React/Vue 组件模式、`Intl.Segmenter` 分词算法，以及 Canvas/SVG 动态折行方案。

---

## 1. 现代 CSS 排版方案 (Pure CSS)

### A. 标题平衡折行 (`text-wrap: balance`)
适用于标题、Modal 标题、卡片头部等 6 行以内的短文本：
```css
.card-title, h1, h2, h3 {
  text-wrap: balance;
  /* 现代浏览器原生平衡算法，尽量让每行字符宽度趋近一致，杜绝孤字 */
}
```
*兼容性*: Chrome 114+, Safari 17.5+, Firefox 121+。不支持的浏览器平稳回退至普通折行。

### B. 正文防孤行 (`text-wrap: pretty`)
适用于文章、段落正文等长文本：
```css
.prose-body, p {
  text-wrap: pretty;
  /* 专注于解决段落最后一行单字寡行问题，微调前几行断点 */
  overflow-wrap: break-word;
  word-break: normal; /* 避免 break-all 劈裂单词 */
}
```
*兼容性*: Chrome 117+, Safari 17.5+。

### C. 中英混排防止单词被切断
```css
.mixed-text {
  word-break: normal;
  overflow-wrap: break-word;
  /* 如果是纯中文或主要为东亚文字，希望按词或意群断开 */
  word-break: keep-all; 
}
```

---

## 2. Tailwind CSS 实用配置

在 `tailwind.config.js` 中或通过任意值属性使用：
```html
<!-- 标题平衡折行 -->
<h2 class="text-2xl font-bold [text-wrap:balance]">
  探索未知的视界与隐匿的真相
</h2>

<!-- 正文段落抗孤行 -->
<p class="text-base text-gray-700 [text-wrap:pretty] break-words">
  这里是一段包含中英文混排的长文本内容，它会在接近行尾时自动处理标点避头尾与尾行孤字。
</p>
```

---

## 3. JavaScript / TypeScript: 原生 `Intl.Segmenter` 两行平衡器

当需要完全可控的标题或副标题排版（如海报生成、视频封面、跨端对齐）时，利用浏览器原生分词 API：

```typescript
export interface BalancedLines {
  line1: string;
  line2: string;
}

/**
 * 将中英文标题基于语义词边界智能折成平衡的两行，杜绝孤行与避头尾违规
 */
export function balanceTitle(text: string, locale = 'zh-CN'): BalancedLines {
  if (text.length <= 12) return { line1: text, line2: '' };

  // 1. 原生语义分词
  const segmenter = new Intl.Segmenter(locale, { granularity: 'word' });
  const segments = Array.from(segmenter.segment(text)).map(s => s.segment);

  // 2. 搜索最优切分点
  let bestIndex = 1;
  let minScore = Infinity;

  const KINSOKU_HEAD = new Set(['。', '，', '、', '！', '？', '；', '：', '）', '》', '」', '』', '】', '”', '’']);

  for (let i = 1; i < segments.length; i++) {
    const l1 = segments.slice(0, i).join('');
    const l2 = segments.slice(i).join('');

    // 避头尾硬约束：第二行首字不能为避头标点
    if (KINSOKU_HEAD.has(l2[0])) {
      continue;
    }

    // 长度对称代价
    const lengthDiff = Math.abs(l1.length - l2.length);

    // 惩罚项：第二行字数过少（孤行惩罚）
    let penalty = 0;
    if (l2.length < 3) penalty += 500;
    else if (l2.length < 5) penalty += 150;

    // 上长下短微弱偏好（视觉重心更稳）
    if (l1.length < l2.length) penalty += 10;

    const totalScore = lengthDiff + penalty;
    if (totalScore < minScore) {
      minScore = totalScore;
      bestIndex = i;
    }
  }

  return {
    line1: segments.slice(0, bestIndex).join(''),
    line2: segments.slice(bestIndex).join(''),
  };
}
```

---

## 4. Web 杜绝居中抖动的打字机实现 (React 范式)

许多 AI Chat 界面使用 `text-align: center` 时，动态追加字符会使前面的字每打一下就往左平移 0.5 个字符宽度，产生剧烈晃动。

### 核心解法：双层容器预排版 (Pre-rendered Layout)
```tsx
import React, { useState, useEffect } from 'react';

interface TypewriterProps {
  fullText: string;
  speedMs?: number;
  onComplete?: () => void;
}

export const SmoothTypewriter: React.FC<TypewriterProps> = ({
  fullText,
  speedMs = 35,
  onComplete,
}) => {
  const [visibleCount, setVisibleCount] = useState(0);

  useEffect(() => {
    setVisibleCount(0);
    const timer = setInterval(() => {
      setVisibleCount(prev => {
        if (prev >= fullText.length) {
          clearInterval(timer);
          onComplete?.();
          return prev;
        }
        return prev + 1;
      });
    }, speedMs);
    return () => clearInterval(timer);
  }, [fullText, speedMs]);

  // 跳过交互
  const handleSkip = () => {
    setVisibleCount(fullText.length);
    onComplete?.();
  };

  return (
    <div 
      onClick={handleSkip} 
      className="relative text-center cursor-pointer select-none"
    >
      {/* 底层隐形占位：确保容器尺寸从第 1 帧就完全稳定，绝不触发重排与重心抖动 */}
      <span className="invisible pointer-events-none" aria-hidden="true">
        {fullText}
      </span>

      {/* 顶层可见字符：绝对定位覆盖在底层之上，逐字 Reveal */}
      <span className="absolute inset-0 flex justify-center items-center">
        <span>{fullText.slice(0, visibleCount)}</span>
        {visibleCount < fullText.length && (
          <span className="inline-block w-2 bg-red-600 animate-pulse ml-0.5">▌</span>
        )}
      </span>
    </div>
  );
};
```

---

## 5. HTML 纯静态轻量方案 (`&nbsp;` 尾词胶水)

如果你在服务端渲染（SSR）或无法使用上述高级特性的静态页面中：
只需在生成 HTML 时，将标题最后两个汉字（或词组）中间的普通空格替换为 `&nbsp;`，即可彻底杜绝孤字成行：

```javascript
function glueOrphan(text) {
  // 若结尾是两字，中间黏贴；若有空格，将最后一个空格替换为 &nbsp;
  if (!text) return '';
  const lastSpace = text.lastIndexOf(' ');
  if (lastSpace !== -1) {
    return text.substring(0, lastSpace) + '&nbsp;' + text.substring(lastSpace + 1);
  }
  // 纯中文标题：在倒数第 2 和第 3 字之间注入无宽连接符或保护 span
  if (text.length > 5) {
    return text.slice(0, -2) + '<span style="white-space:nowrap">' + text.slice(-2) + '</span>';
  }
  return text;
}
```
