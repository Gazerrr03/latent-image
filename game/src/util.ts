const DIGITS = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九'];

/** 0–999 的中文数字 */
export function cn(n: number): string {
  n = Math.floor(n);
  if (n < 10) return DIGITS[n];
  if (n < 20) return '十' + (n % 10 ? DIGITS[n % 10] : '');
  if (n < 100) return DIGITS[Math.floor(n / 10)] + '十' + (n % 10 ? DIGITS[n % 10] : '');
  if (n < 1000) {
    const rest = n % 100;
    const head = DIGITS[Math.floor(n / 100)] + '百';
    if (!rest) return head;
    return head + (rest < 10 ? '零' + DIGITS[rest] : rest < 20 ? '一' + cn(rest) : cn(rest));
  }
  return String(n);
}

/** 9.3 -> 九米三十，4.2 -> 四米二十，12.05 -> 十二米零五 */
export function cnMeters(x: number): string {
  const m = Math.floor(x);
  const c = Math.round((x - m) * 100);
  if (c === 0) return `${cn(m)}米整`;
  return `${cn(m)}米${c < 10 ? '零' + cn(c) : cn(c)}`;
}

export function clock(t: number): string {
  const d = new Date(t);
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
}

export function wait(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms));
}

/** 逐字显示文本 */
export async function typeText(el: HTMLElement, text: string, msPerChar = 45): Promise<void> {
  el.textContent = '';
  el.classList.add('typing');
  for (const ch of text) {
    el.textContent += ch;
    await wait(ch === '。' || ch === '，' ? msPerChar * 6 : msPerChar);
  }
  el.classList.remove('typing');
}
