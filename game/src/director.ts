import * as THREE from 'three';
import { audio } from './audio';
import { Hud } from './hud';
import { RuleResolver } from './intent/ruleResolver';
import type { IntentResolver } from './intent/types';
import { Reader } from './reader/reader';
import { CorridorScene, type VisitResult } from './scenes/corridor';
import type { GameScene } from './scenes/common';
import { StudyScene } from './scenes/study';
import { hasProgress, restart, save, state } from './state';
import { wait } from './util';

const FP_HELP = 'WASD 移动　鼠标 转向　F 丈量　E 互动　Esc 暂停';

/** 负责场景切换和第一章的事件流程 */
export class Director {
  private renderer: THREE.WebGLRenderer;
  private hud = new Hud();
  private resolver: IntentResolver = new RuleResolver();
  private reader: Reader;
  private study: StudyScene;
  private corridor: CorridorScene;
  private current: GameScene;
  private busy = false;
  private leavingCorridor = false;
  private timer = new THREE.Timer();

  constructor(app: HTMLElement) {
    this.renderer = new THREE.WebGLRenderer({ antialias: true });
    this.renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.15;
    const canvas = this.renderer.domElement;
    app.append(canvas);

    this.reader = new Reader(
      {
        onLookUp: () => this.lookUp(),
        onSubmit: (slot, text) => this.submit(slot, text),
        onEnterSpace: () => void this.goCorridor(),
      },
      this.resolver.label,
    );
    app.append(this.reader.root, this.hud.root);

    this.study = new StudyScene(canvas);
    this.study.onScreenRect = (r) => {
      this.reader.setRect(r.x, r.y, r.w, r.h);
      this.reader.setVisible(r.visible && this.current === this.study && !this.busy);
    };
    this.study.onClickMonitor = () => void this.backToReading();
    this.study.onLookedAtScratches = () => this.sawScratches();
    this.study.setScratches(!!state.flags.scratches);

    this.corridor = new CorridorScene(canvas, this.hud);
    this.corridor.onExit = (r) => void this.leaveCorridor(r);
    this.corridor.controls.onUnlock = () => {
      if (this.current === this.corridor && !this.leavingCorridor) this.pause();
    };

    this.current = this.study;
    addEventListener('resize', () => this.resize());
    this.resize();
    this.study.setMode('reading', false);
    this.renderer.setAnimationLoop(() => this.frame());
  }

  start(): void {
    void this.reader.render();
    const begin = () => {
      audio.init();
      audio.setDrone(0.12);
      this.hud.hideOverlay();
      void this.hud.fade(0, 1400);
    };
    void this.hud.fade(1, 0);
    const buttons = hasProgress()
      ? [
          { label: '继续阅读', primary: true, onClick: begin },
          { label: '从头开始', onClick: restart },
        ]
      : [{ label: '开始阅读', primary: true, onClick: begin }];
    this.hud.showOverlay('ERRATA', ['一个连载阅读网站。一份夹着很多人笔迹的手稿。', '建议佩戴耳机，在安静的房间里游玩。'], buttons);
  }

  private resize(): void {
    const w = innerWidth;
    const h = innerHeight;
    this.renderer.setSize(w, h);
    this.study.resize(w, h);
    this.corridor.resize(w, h);
  }

  private frame(): void {
    this.timer.update();
    const dt = Math.min(0.05, this.timer.getDelta());
    this.current.update(dt);
    this.renderer.render(this.current.scene, this.current.camera);
  }

  // ───────────── 书房 ─────────────

  private lookUp(): void {
    this.reader.closeSlot();
    this.reader.pulseLookUp(false);
    this.study.setMode('looking');
    this.hud.setHint('拖动鼠标环顾四周　·　点击显示器继续阅读');
  }

  private async backToReading(): Promise<void> {
    this.hud.setHint('');
    this.study.setMode('reading');
    await wait(950);
    if (state.flags.sawScratches && !state.flags.ghostNote) await this.ghostNote();
  }

  private sawScratches(): void {
    if (state.flags.sawScratches) return;
    state.flags.sawScratches = true;
    save();
    audio.sting();
    audio.setDrone(0.4, 1);
    this.hud.setHint('');
    setTimeout(() => {
      if (this.study.mode === 'looking') this.hud.setHint('点击显示器继续阅读');
    }, 4000);
  }

  /** 第一章收尾：一条用你的字体写下、你却没写过的批注 */
  private async ghostNote(): Promise<void> {
    state.flags.ghostNote = true;
    save();
    await wait(600);
    await this.reader.render();
    await wait(1600);
    state.flags.chapterDone = true;
    save();
    await this.reader.render();
    this.reader.scrollToBottom();
    await wait(2200);
    this.hud.showOverlay('第一章　门', ['（原型到此为止）'], [
      { label: '留在这里', primary: true, onClick: () => this.hud.hideOverlay() },
      { label: '从头开始', onClick: restart },
    ]);
  }

  private async submit(slotId: string, text: string): Promise<string> {
    const res = await this.resolver.resolve({
      slotId,
      text,
      context: { doorStatus: state.door.status, measuredLength: state.measuredLength },
    });
    const now = Date.now();
    state.annotations.push({ id: String(now), slotId, text, intent: res.kinds[0] ?? 'note', createdAt: now });

    if (res.door) {
      const prev = state.door;
      const keep = res.door.status === 'described';
      const next = {
        status: res.door.status,
        number: res.door.number ?? (keep ? prev.number : null),
        color: res.door.color ?? (keep ? prev.color : null),
      };
      if (JSON.stringify(prev) !== JSON.stringify(next)) {
        state.revisions['r-door'] = now;
        state.revisions['stage-1'] = now;
        if ((prev.status === 'denied') !== (next.status === 'denied')) {
          state.revisions['r-door2'] = now;
          state.revisions['s-door'] = now;
        }
      }
      state.door = next;
    }
    if (res.recordedLength) {
      state.recordedLength = res.recordedLength;
      state.revisions['r-hall'] = now;
      state.revisions['stage-1'] = now;
    }
    save();
    await this.reader.render();
    return res.stage;
  }

  // ───────────── 走廊 ─────────────

  private async goCorridor(): Promise<void> {
    if (this.busy) return;
    this.busy = true;
    this.reader.setVisible(false);
    await this.hud.fade(1, 900);
    this.leavingCorridor = false;
    this.corridor.enter(state);
    this.current = this.corridor;
    this.hud.setFirstPerson(true, FP_HELP);
    audio.setDrone(0.45, 3);
    this.hud.showOverlay('梣林巷 7 号　二楼走廊', ['点击进入。'], [{ label: '进入', primary: true, onClick: () => this.resume() }]);
    await this.hud.fade(0, 1200);
    this.busy = false;
  }

  private resume(): void {
    this.hud.hideOverlay();
    this.corridor.controls.lock();
  }

  private pause(): void {
    this.hud.showOverlay('暂停', [], [
      { label: '继续', primary: true, onClick: () => this.resume() },
      {
        label: '回到书桌前',
        onClick: () => {
          this.hud.hideOverlay();
          this.corridor.exit(false);
        },
      },
    ]);
  }

  private async leaveCorridor(r: VisitResult): Promise<void> {
    this.leavingCorridor = true;
    this.busy = true;
    await this.hud.fade(1, r.reachedBeyond ? 1800 : 800);
    this.corridor.leave();
    this.hud.setFirstPerson(false);
    this.hud.hideOverlay();

    state.corridorVisits++;
    state.lastSteps = r.steps;
    state.lastDoorDist = Math.round(r.doorDist * 100) / 100;
    if (r.measured) state.measuredLength = Math.max(state.measuredLength ?? 0, r.measured);
    const anomaly = r.reachedBeyond && !state.flags.scratches;
    if (anomaly) state.flags.scratches = true;
    save();

    this.current = this.study;
    this.study.setScratches(!!state.flags.scratches);
    this.study.setMode('reading', false);
    audio.setDrone(anomaly ? 0.25 : 0.12, 3);
    await wait(anomaly ? 1200 : 300);
    this.busy = false;
    await this.hud.fade(0, 1200);
    await this.reader.render();
    if (anomaly) {
      this.reader.scrollToBottom();
      this.reader.pulseLookUp(true);
    }
  }
}
