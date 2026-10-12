import type { GameState } from '../state';
import { cnMeters } from '../util';

export type Layer = 'site' | 'heading' | 'record' | 'study' | 'note' | 'stage' | 'reader';
export type Seg = string | { slot: string; text: string };

export interface Block {
  id: string;
  layer: Layer;
  segs: Seg[];
  /** 时间码、署名等附加信息 */
  meta?: string;
  /** 首次出现时逐字显示 */
  typed?: boolean;
}

export interface Comment {
  user: string;
  when: string;
  text: string;
}

export const SLOT_DOOR = 'door';

export const LEGEND: { layer: Layer; label: string }[] = [
  { layer: 'record', label: '录音转写 · E. 普拉姆' },
  { layer: 'study', label: '研究手稿 · L. 塞耶' },
  { layer: 'note', label: '整理批注 · J. 坦尼' },
  { layer: 'stage', label: '场景提示 · W. 惠特克' },
  { layer: 'reader', label: '你' },
];

const BLANK = '████';

function doorPhrase(s: GameState): string {
  if (s.door.status === 'denied') return BLANK;
  if (s.door.status === 'described' && s.door.color) {
    return s.door.color === '铁' ? '一扇铁门' : `一扇${s.door.color}门`;
  }
  return '一扇门';
}

export function stageForState(s: GameState): string {
  const hall = s.recordedLength ? `，全长${cnMeters(s.recordedLength)}` : '';
  if (s.door.status === 'denied') return `【场景：一条走廊${hall}。尽头什么也没有。】`;
  const num = s.door.status === 'described' && s.door.number ? `，门上写着 ${s.door.number}` : '';
  const phrase = s.door.status === 'described' ? doorPhrase(s) : '一扇门';
  return `【场景：一条走廊${hall}。尽头有${phrase}${num}。】`;
}

export function chapter1(s: GameState): Block[] {
  const denied = s.door.status === 'denied';
  const doorWord = denied ? BLANK : '门';
  const hall = s.recordedLength ? cnMeters(s.recordedLength) : '四米二十';
  const doorNum = s.door.status === 'described' && s.door.number ? `，门上写着 ${s.door.number}` : '';

  const blocks: Block[] = [
    {
      id: 'site-intro',
      layer: 'site',
      segs: ['本连载由用户 jonah_t 整理上传。原稿为卢西安·塞耶的遗稿，夹有录音转写与多人笔迹。部分批注来源无法核实。'],
    },
    { id: 'h1', layer: 'heading', segs: ['一　门'] },
    {
      id: 's-intro',
      layer: 'study',
      segs: [
        '梣林巷 7 号拆除之前，测绘员埃利亚斯·普拉姆受雇为它做最后一次测绘。那是他长大的房子。他一共留下十一盘录音带，第三盘是我们的起点。',
      ],
    },
    {
      id: 'r-wall',
      layer: 'record',
      meta: '第三盘 · 00:04:12',
      segs: [
        '普拉姆：外墙，东侧，十一米四十。……内墙，同一面，十一米四十三。\n普拉姆：[停顿] 再量一次。\n普拉姆：十一米四十三。多三厘米。',
      ],
    },
    {
      id: 's-3cm',
      layer: 'study',
      segs: ['三厘米，大约是一本精装书的厚度；或者，一个孩子侧身贴着墙站好时，肩膀到墙面的距离。¹'],
    },
    {
      id: 'n-3cm',
      layer: 'note',
      meta: '——J.',
      segs: ['塞耶先生总爱这么打比方。他是个盲人，我不知道他从哪儿知道孩子贴墙站着是什么样子。'],
    },
    {
      id: 'r-hall',
      layer: 'record',
      meta: '第三盘 · 00:19:50',
      segs: [`普拉姆：二楼走廊。地板是人字拼的旧橡木，墙纸是褪色的藤蔓纹。全长${hall}。`],
    },
    {
      id: 'r-door',
      layer: 'record',
      segs: ['普拉姆：走廊尽头有', { slot: SLOT_DOOR, text: doorPhrase(s) }, `${doorNum}。`],
    },
  ];

  for (const a of s.annotations.filter((x) => x.slotId === SLOT_DOOR)) {
    blocks.push({ id: `a-${a.id}`, layer: 'reader', meta: '——你', segs: [a.text] });
  }

  blocks.push(
    {
      id: 'r-door2',
      layer: 'record',
      segs: [
        `普拉姆：……我不记得这里有${doorWord}。\n普拉姆：两边的门，我数了三次。七扇，五扇，八扇。\n[约 40 秒静音]`,
      ],
    },
    {
      id: 's-door',
      layer: 'study',
      segs: [
        `值得注意的是，普拉姆没有说"这里以前没有${doorWord}"，他说的是"我不记得"。一个测绘员把怀疑放在自己的记忆上，而不是${denied ? BLANK : '房子'}上。²`,
      ],
    },
    { id: 'stage-1', layer: 'stage', meta: '舞台剧《7 号》排练本，第一场。——W.W.', segs: [stageForState(s)] },
    {
      id: 'n-stage',
      layer: 'note',
      meta: '——J.',
      segs: ['这一行方括号不是塞耶写的，笔迹是另一个人的，夹在第 41 页和第 42 页之间。我查过，W.W. 是个编剧，去年失踪了。'],
    },
    {
      id: 'fn',
      layer: 'site',
      segs: ['¹ 原稿此处注明出处为《居住与缺席》，第 112 页。站务组未能查到这本书。\n² 原稿此处的脚注被胶带贴住，无法揭开。'],
    },
  );

  if (s.flags.scratches) {
    blocks.push({
      id: 'stage-room',
      layer: 'stage',
      typed: true,
      segs: ['【场景：一间小书房。桌上有一台电脑。有人在读。】\n【读者回头。门框上有三道划痕。】'],
    });
  }
  if (s.flags.ghostNote) {
    blocks.push({
      id: 'ghost',
      layer: 'reader',
      meta: '——你',
      typed: true,
      segs: ['我回头了。门框上的划痕，是从里面抓的。'],
    });
  }
  if (s.flags.chapterDone) {
    blocks.push({ id: 'end', layer: 'site', segs: ['第一章完。第二章《回声》整理中。'] });
  }
  return blocks;
}

export function comments(s: GameState): Comment[] {
  return [
    { user: '夜航船', when: '2 天前', text: '三厘米那段我起鸡皮疙瘩了。一个孩子侧身贴墙……为什么要这么比喻啊' },
    {
      user: 'moss_and_ash',
      when: '1 天前',
      text: '考据了一下：梣林巷 7 号九十年代初就拆了，现在那里是停车场。所以普拉姆量的到底是哪栋房子？',
    },
    { user: '不睡觉的猫', when: '5 小时前', text: '有人跟我一样吗，读到数门那段，下意识回头看了一眼自己的房门。' },
    { user: '137', when: s.lastSteps > 0 ? '刚刚' : '3 小时前', text: String(s.lastSteps > 0 ? s.lastSteps : 137) },
  ];
}

export function suggestions(s: GameState): string[] {
  const list: string[] = [];
  if (s.measuredLength && Math.abs(s.measuredLength - (s.recordedLength ?? 4.2)) > 0.3) {
    list.push(`走廊不是${s.recordedLength ? cnMeters(s.recordedLength) : '四米二十'}，我量到 ${s.measuredLength.toFixed(1)} 米。`);
  }
  if (s.door.status === 'denied') {
    list.push('门还在那里，只是没人看见。');
  } else {
    list.push('门上写着 7。', '那里根本没有门。');
  }
  list.push('门后是什么？');
  if (s.door.status === 'described' && !s.door.color) list.push('门是红色的。');
  return list;
}
