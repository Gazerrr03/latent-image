import { chapter1, comments, LEGEND, suggestions, type Block } from '../content/chapter1';
import { state } from '../state';
import { clock, typeText } from '../util';

export interface ReaderHooks {
  onLookUp(): void;
  /** 提交批注，返回编剧的场景提示（可能为空） */
  onSubmit(slotId: string, text: string): Promise<string>;
  onEnterSpace(slotId: string): void;
}

function el<K extends keyof HTMLElementTagNameMap>(tag: K, cls?: string, text?: string): HTMLElementTagNameMap[K] {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined) e.textContent = text;
  return e;
}

export class Reader {
  readonly root: HTMLElement;
  private doc: HTMLElement;
  private commentsEl: HTMLElement;
  private scroller: HTMLElement;
  private lookUpBtn: HTMLButtonElement;
  private panel: HTMLElement;
  private seen = new Set<string>();
  private lastRender = 0;
  private firstRender = true;

  constructor(
    private hooks: ReaderHooks,
    private resolverLabel: string,
  ) {
    this.root = el('div', 'screen');
    this.root.id = 'screen';

    this.scroller = el('div', 'site');
    const bar = el('header', 'site-bar');
    bar.append(el('span', 'logo', 'ERRATA'), el('span', 'crumb', '连载 / 梣林巷 7 号 / 第一章　门'));
    this.lookUpBtn = el('button', 'look-up', '抬头');
    this.lookUpBtn.title = '从屏幕前抬起头';
    this.lookUpBtn.onclick = () => this.hooks.onLookUp();
    bar.append(this.lookUpBtn);

    const legend = el('div', 'legend');
    legend.append(el('span', 'legend-title', '图例'));
    for (const l of LEGEND) legend.append(el('span', `legend-item layer-${l.layer}`, l.label));

    this.doc = el('article', 'doc');
    this.commentsEl = el('section', 'comments');
    this.scroller.append(bar, legend, this.doc, this.commentsEl);

    this.panel = el('div', 'slot-panel');
    this.panel.hidden = true;
    this.root.append(this.scroller, this.panel);
  }

  setVisible(v: boolean): void {
    this.root.classList.toggle('hidden', !v);
  }

  setRect(x: number, y: number, w: number, h: number): void {
    const s = this.root.style;
    s.left = `${x}px`;
    s.top = `${y}px`;
    s.width = `${w}px`;
    s.height = `${h}px`;
  }

  pulseLookUp(on: boolean): void {
    this.lookUpBtn.classList.toggle('pulse', on);
  }

  scrollToBottom(): void {
    this.scroller.scrollTo({ top: this.scroller.scrollHeight, behavior: 'smooth' });
  }

  /** 重新渲染阅读内容；新出现的 typed 段落逐字显示 */
  async render(): Promise<void> {
    const blocks = chapter1(state);
    this.doc.replaceChildren();
    const toType: [HTMLElement, string][] = [];

    for (const b of blocks) {
      const node = this.renderBlock(b);
      this.doc.append(node);
      const fresh = !this.seen.has(b.id);
      if (b.typed && fresh && !this.firstRender) {
        const body = node.querySelector<HTMLElement>('.body')!;
        toType.push([body, body.textContent ?? '']);
        body.textContent = '';
      }
      const rev = state.revisions[b.id];
      if (rev && rev > this.lastRender && !this.firstRender) node.classList.add('revised-flash');
      this.seen.add(b.id);
    }

    this.renderComments();
    this.firstRender = false;
    this.lastRender = Date.now();

    for (const [body, text] of toType) {
      this.scrollToBottom();
      await typeText(body, text, 55);
    }
  }

  private renderBlock(b: Block): HTMLElement {
    const node = el('div', `block layer-${b.layer}`);
    node.dataset.id = b.id;
    if (b.meta && b.layer === 'record') node.append(el('div', 'meta', b.meta));
    const body = el('div', 'body');
    for (const seg of b.segs) {
      if (typeof seg === 'string') {
        body.append(document.createTextNode(seg));
      } else {
        const a = el('span', 'slot', seg.text);
        a.tabIndex = 0;
        a.onclick = () => this.openSlot(seg.slot, a.textContent ?? '');
        body.append(a);
      }
    }
    node.append(body);
    if (b.meta && b.layer !== 'record') node.append(el('div', 'sign', b.meta));
    const rev = state.revisions[b.id];
    if (rev) node.append(el('div', 'revision', `本段于 ${clock(rev)} 修订。修订人：未知。`));
    return node;
  }

  private renderComments(): void {
    this.commentsEl.replaceChildren(el('h3', '', `评论（${comments(state).length}）`));
    for (const c of comments(state)) {
      const row = el('div', 'comment');
      row.append(el('span', 'c-user', c.user), el('span', 'c-when', c.when), el('div', 'c-text', c.text));
      this.commentsEl.append(row);
    }
    const box = el('textarea', 'c-input');
    box.placeholder = '评论功能维护中。';
    box.disabled = true;
    this.commentsEl.append(box);
  }

  openSlot(slotId: string, quoted: string): void {
    const p = this.panel;
    p.replaceChildren();
    p.hidden = false;

    const close = el('button', 'panel-close', '×');
    close.onclick = () => (p.hidden = true);
    p.append(close, el('div', 'panel-quote', `"走廊尽头有${quoted}。"`));
    p.append(el('div', 'panel-hint', '在这一段旁边写下你的批注，或者自己去看看。'));

    const mine = state.annotations.filter((a) => a.slotId === slotId);
    if (mine.length) {
      const list = el('div', 'panel-mine');
      for (const a of mine) list.append(el('div', 'layer-reader mine-item', a.text));
      p.append(list);
    }

    const chips = el('div', 'chips');
    const input = el('textarea', 'panel-input layer-reader');
    input.placeholder = '写下你的批注……';
    const fillChips = () => {
      chips.replaceChildren();
      for (const s of suggestions(state)) {
        const c = el('button', 'chip', s);
        c.onclick = () => {
          input.value = s;
          input.focus();
        };
        chips.append(c);
      }
    };
    fillChips();

    const result = el('div', 'panel-result layer-stage');
    const actions = el('div', 'panel-actions');
    const submit = el('button', 'btn primary', '写下批注');
    const enter = el('button', 'btn', '走进去看看');

    submit.onclick = async () => {
      const text = input.value.trim();
      if (!text) {
        input.focus();
        return;
      }
      submit.disabled = true;
      input.disabled = true;
      result.textContent = '……';
      const stage = await this.hooks.onSubmit(slotId, text);
      input.value = '';
      input.disabled = false;
      fillChips();
      submit.disabled = false;
      if (stage) await typeText(result, stage, 50);
      else result.textContent = '';
      enter.classList.add('pulse');
    };
    enter.onclick = () => {
      p.hidden = true;
      this.hooks.onEnterSpace(slotId);
    };
    actions.append(submit, enter);

    p.append(chips, input, actions, result, el('div', 'panel-foot', this.resolverLabel));
    input.focus();
  }

  closeSlot(): void {
    this.panel.hidden = true;
  }
}
