import { wait } from './util';

function div(id: string, cls = ''): HTMLDivElement {
  const d = document.createElement('div');
  d.id = id;
  if (cls) d.className = cls;
  return d;
}

/** 覆盖在画面上的提示、字幕、淡入淡出与菜单 */
export class Hud {
  readonly root = div('hud');
  private hint = div('hint');
  private subtitle = div('subtitle');
  private readout = div('readout');
  private help = div('help');
  private crosshair = div('crosshair');
  private fadeEl = div('fade');
  private overlay = div('overlay');
  private readoutTimer = 0;

  constructor() {
    this.root.append(this.crosshair, this.hint, this.subtitle, this.readout, this.help, this.fadeEl, this.overlay);
    this.overlay.hidden = true;
  }

  setHint(text: string): void {
    if (this.hint.textContent !== text) this.hint.textContent = text;
    this.hint.classList.toggle('show', !!text);
  }

  setSubtitle(text: string): void {
    this.subtitle.textContent = text;
    this.subtitle.classList.toggle('show', !!text);
  }

  showReadout(text: string, ms = 2600): void {
    this.readout.textContent = text;
    this.readout.classList.add('show');
    clearTimeout(this.readoutTimer);
    this.readoutTimer = window.setTimeout(() => this.readout.classList.remove('show'), ms);
  }

  setFirstPerson(on: boolean, help = ''): void {
    this.crosshair.classList.toggle('show', on);
    this.help.textContent = help;
    this.help.classList.toggle('show', on && !!help);
    if (!on) {
      this.setHint('');
      this.setSubtitle('');
    }
  }

  async fade(to: 0 | 1, ms = 900): Promise<void> {
    this.fadeEl.style.transition = `opacity ${ms}ms ease`;
    this.fadeEl.style.opacity = String(to);
    await wait(ms);
  }

  /** 显示一个居中的菜单面板 */
  showOverlay(title: string, lines: string[], buttons: { label: string; primary?: boolean; onClick: () => void }[]): void {
    const o = this.overlay;
    o.replaceChildren();
    const card = document.createElement('div');
    card.className = 'card';
    const h = document.createElement('h1');
    h.textContent = title;
    card.append(h);
    for (const l of lines) {
      const p = document.createElement('p');
      p.textContent = l;
      card.append(p);
    }
    const row = document.createElement('div');
    row.className = 'card-actions';
    for (const b of buttons) {
      const btn = document.createElement('button');
      btn.className = b.primary ? 'btn primary' : 'btn';
      btn.textContent = b.label;
      btn.onclick = (e) => {
        e.stopPropagation();
        b.onClick();
      };
      row.append(btn);
    }
    card.append(row);
    o.append(card);
    o.hidden = false;
  }

  hideOverlay(): void {
    this.overlay.hidden = true;
  }
}
