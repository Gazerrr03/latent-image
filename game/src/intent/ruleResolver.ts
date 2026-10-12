import { cnMeters, wait } from '../util';
import type { IntentKind, IntentRequest, IntentResolver, IntentResult } from './types';

/**
 * 临时规则解析器：用关键词识别意图，只用于验证流程。
 * 它不能证明自由语言体验成立，接入模型后应替换。
 */

const DENY = /(没有门|没门|没有什么门|不存在|根本没有|并没有|不是门|是墙|只有墙|消失|假的|幻觉|看错|不在那)/;
const LENGTH = /(\d+(?:\.\d+)?)\s*(米|公尺|m(?![a-z]))/i;
const QUESTION = /[?？]|什么|为什么|怎么|是谁|谁|吗|呢$/;
const DOOR_WORDS = /(门|把手|门牌|编号|号码|写着|刻着|贴着|漆|颜色|木|铁|旧|新)/;
const CN_NUM: Record<string, string> = {
  一: '1', 二: '2', 两: '2', 三: '3', 四: '4', 五: '5', 六: '6', 七: '7', 八: '8', 九: '9', 十: '10',
};

const COLORS: { re: RegExp; word: string; hex: string }[] = [
  { re: /红/, word: '红色的', hex: '#6e2620' },
  { re: /绿/, word: '绿色的', hex: '#2f4a37' },
  { re: /蓝/, word: '蓝色的', hex: '#2a3a55' },
  { re: /黑/, word: '黑色的', hex: '#151414' },
  { re: /白/, word: '白色的', hex: '#d9d5cb' },
  { re: /黄/, word: '黄色的', hex: '#86692b' },
  { re: /铁|金属|钢/, word: '铁', hex: '#454849' },
];

export const COLOR_HEX: Record<string, string> = Object.fromEntries(COLORS.map((c) => [c.word, c.hex]));

function findNumber(text: string): string | null {
  const t = text.replace(LENGTH, '');
  const digits = t.match(/(\d{1,4})/);
  if (digits) return digits[1];
  const near = t.match(/(?:写着|刻着|编号|号码|门牌|数字)[^一二两三四五六七八九十]{0,3}([一二两三四五六七八九十])/);
  if (near) return CN_NUM[near[1]];
  const hao = t.match(/([一二两三四五六七八九十])号/);
  if (hao) return CN_NUM[hao[1]];
  return null;
}

function hallLine(len: number | undefined): string {
  return len ? `，全长${cnMeters(len)}` : '';
}

export class RuleResolver implements IntentResolver {
  readonly label = '批注解析：临时规则（尚未接入模型）';

  async resolve(req: IntentRequest): Promise<IntentResult> {
    await wait(500);
    const text = req.text.trim();
    const kinds: IntentKind[] = [];
    const result: IntentResult = { kinds, stage: '' };

    const len = text.match(LENGTH);
    if (len) {
      const v = parseFloat(len[1]);
      if (v > 0.5 && v < 200) {
        result.recordedLength = Math.round(v * 100) / 100;
        kinds.push('measure');
      }
    }

    if (DENY.test(text)) {
      kinds.push('deny');
      result.door = { status: 'denied', number: null, color: null };
      result.stage = `【场景：一条走廊${hallLine(result.recordedLength)}。尽头什么也没有。】`;
      return result;
    }

    if (QUESTION.test(text) && !findNumber(text)) {
      kinds.push('ask');
      result.stage = `【场景：一条走廊${hallLine(result.recordedLength)}。尽头有一扇门。门后——】`;
      return result;
    }

    const number = findNumber(text);
    const color = COLORS.find((c) => c.re.test(text));
    if (number || color || (DOOR_WORDS.test(text) && !kinds.includes('measure'))) {
      kinds.push('describe');
      result.door = { status: 'described', number, color: color?.word ?? null };
      const colorWord = color ? color.word : '';
      const numberPart = number ? `，门上写着 ${number}` : '';
      result.stage = `【场景：一条走廊${hallLine(result.recordedLength)}。尽头有一扇${colorWord}门${numberPart}。】`;
      return result;
    }

    if (kinds.includes('measure')) {
      result.stage = `【场景：一条走廊${hallLine(result.recordedLength)}。】`;
      return result;
    }

    kinds.push('note');
    result.stage = '';
    return result;
  }
}
