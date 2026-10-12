import * as THREE from 'three';
import { box, whiteMat, woodTexture, type GameScene } from './common';

type Mode = 'reading' | 'looking';

const SCREEN_W = 0.62;
const SCREEN_H = 0.38;
const SCREEN_CENTER = new THREE.Vector3(0, 1.1, -1.575);
const SEAT = new THREE.Vector3(0, 1.18, -0.7);

/**
 * 基础书房：读者坐在桌前。
 * reading：镜头贴近显示器，阅读器覆盖在屏幕区域上；
 * looking：抬起头，拖动鼠标环顾房间，点击显示器回到阅读。
 */
export class StudyScene implements GameScene {
  readonly scene = new THREE.Scene();
  readonly camera = new THREE.PerspectiveCamera(55, 1, 0.02, 50);
  mode: Mode = 'reading';

  onScreenRect: (rect: { x: number; y: number; w: number; h: number; visible: boolean }) => void = () => {};
  onLookedAtScratches: () => void = () => {};
  onClickMonitor: () => void = () => {};

  private monitor = new THREE.Group();
  private scratches = new THREE.Group();
  private lamp: THREE.PointLight;
  private yaw = 0;
  private pitch = -0.08;
  private tween: { from: THREE.Vector3; fromQ: THREE.Quaternion; t: number; dur: number } | null = null;
  private readPos = new THREE.Vector3();
  private aspect = 1;
  private gazeTime = 0;
  private flicker = 0;
  private drag: { x: number; y: number; moved: number } | null = null;

  constructor(private dom: HTMLElement) {
    this.scene.background = new THREE.Color(0x0b0b0c);
    this.scene.fog = new THREE.Fog(0x0b0b0c, 3, 9);
    this.build();
    this.lamp = this.scene.getObjectByName('lamp') as THREE.PointLight;
    this.bindInput();
  }

  private build(): void {
    const s = this.scene;
    const white = whiteMat();
    const W = 3.2;
    const D = 3.6;
    const H = 2.7;

    s.add(new THREE.AmbientLight(0xffffff, 0.12));
    const hemi = new THREE.HemisphereLight(0xd8dce6, 0x2a2420, 0.18);
    s.add(hemi);

    // 地面、天花、墙
    s.add(box(W, 0.02, D, white, 0, -0.01, 0));
    s.add(box(W, 0.02, D, white, 0, H + 0.01, 0));
    s.add(box(0.02, H, D, white, -W / 2, H / 2, 0));
    s.add(box(0.02, H, D, white, W / 2, H / 2, 0));
    s.add(box(W, H, 0.02, white, 0, H / 2, -D / 2));

    // 身后墙上的门（读者回头才会看到）
    const dz = D / 2;
    const dx0 = 0.25;
    const dx1 = 1.15;
    const dh = 2.05;
    s.add(box(dx0 + W / 2, H, 0.02, white, (-W / 2 + dx0) / 2, H / 2, dz));
    s.add(box(W / 2 - dx1, H, 0.02, white, (dx1 + W / 2) / 2, H / 2, dz));
    s.add(box(dx1 - dx0, H - dh, 0.02, white, (dx0 + dx1) / 2, (H + dh) / 2, dz));
    const casing = new THREE.MeshStandardMaterial({ color: 0xd9d4c9, roughness: 0.8 });
    s.add(box(0.07, dh + 0.07, 0.04, casing, dx0 - 0.035, (dh + 0.07) / 2, dz - 0.02));
    s.add(box(0.07, dh + 0.07, 0.04, casing, dx1 + 0.035, (dh + 0.07) / 2, dz - 0.02));
    s.add(box(dx1 - dx0 + 0.14, 0.07, 0.04, casing, (dx0 + dx1) / 2, dh + 0.035, dz - 0.02));
    const doorMat = new THREE.MeshStandardMaterial({ map: woodTexture('#6b5240'), roughness: 0.7 });
    s.add(box(dx1 - dx0 - 0.01, dh - 0.01, 0.04, doorMat, (dx0 + dx1) / 2, dh / 2, dz + 0.01));

    // 门框上的三道划痕，默认隐藏
    const scratchMat = new THREE.MeshBasicMaterial({ color: 0x2a1610 });
    for (let i = 0; i < 3; i++) {
      const m = new THREE.Mesh(new THREE.BoxGeometry(0.007, 0.34, 0.004), scratchMat);
      m.position.set(dx0 - 0.055 + i * 0.016, 1.2 - i * 0.02, dz - 0.043);
      m.rotation.z = 0.18;
      this.scratches.add(m);
    }
    this.scratches.visible = false;
    s.add(this.scratches);

    // 书桌
    const desk = new THREE.MeshStandardMaterial({ color: 0x6d5a48, roughness: 0.7 });
    s.add(box(1.5, 0.04, 0.72, desk, 0, 0.74, -1.42));
    for (const [x, z] of [
      [-0.7, -1.1],
      [0.7, -1.1],
      [-0.7, -1.74],
      [0.7, -1.74],
    ]) {
      s.add(box(0.04, 0.72, 0.04, desk, x, 0.36, z));
    }

    // 显示器
    const dark = new THREE.MeshStandardMaterial({ color: 0x1b1b1d, roughness: 0.5 });
    this.monitor.add(box(0.68, 0.44, 0.035, dark, 0, 1.1, -1.595, false));
    this.monitor.add(box(0.05, 0.3, 0.05, dark, 0, 0.9, -1.62, false));
    this.monitor.add(box(0.24, 0.015, 0.18, dark, 0, 0.765, -1.6, false));
    const screen = new THREE.Mesh(
      new THREE.PlaneGeometry(SCREEN_W, SCREEN_H),
      new THREE.MeshBasicMaterial({ color: 0xe9e4d6 }),
    );
    screen.position.copy(SCREEN_CENTER);
    this.monitor.add(screen);
    s.add(this.monitor);
    const glow = new THREE.PointLight(0xdfe6ff, 0.9, 3, 2);
    glow.position.set(0, 1.1, -1.35);
    s.add(glow);

    // 键盘、台灯
    s.add(box(0.44, 0.02, 0.14, dark, 0, 0.77, -1.25, false));
    const brass = new THREE.MeshStandardMaterial({ color: 0x7c6a45, roughness: 0.4, metalness: 0.6 });
    s.add(box(0.12, 0.02, 0.12, brass, 0.55, 0.77, -1.55, false));
    s.add(box(0.015, 0.4, 0.015, brass, 0.55, 0.97, -1.55, false));
    const shade = new THREE.Mesh(new THREE.ConeGeometry(0.11, 0.14, 24, 1, true), brass);
    shade.position.set(0.55, 1.18, -1.52);
    s.add(shade);
    const lamp = new THREE.PointLight(0xffc98a, 2.2, 6, 1.6);
    lamp.name = 'lamp';
    lamp.position.set(0.55, 1.1, -1.5);
    s.add(lamp);

    // 左墙书架与书
    const shelf = new THREE.MeshStandardMaterial({ color: 0x5b4a3b, roughness: 0.8 });
    for (let i = 0; i < 4; i++) s.add(box(0.3, 0.025, 1.2, shelf, -1.43, 0.5 + i * 0.45, -0.2));
    const bookColors = [0x7a3b2e, 0x2f4a5c, 0x8a7a5a, 0x3e3e3e, 0x5a6b4a, 0x9b8f7a];
    let seed = 5;
    for (let i = 0; i < 3; i++) {
      let z = -0.75;
      while (z < 0.35) {
        seed = (seed * 9301 + 49297) % 233280;
        const t = 0.03 + (seed / 233280) * 0.04;
        const h = 0.24 + (seed % 7) * 0.02;
        const mat = new THREE.MeshStandardMaterial({ color: bookColors[seed % bookColors.length], roughness: 0.9 });
        s.add(box(0.2, h, t, mat, -1.45, 0.515 + i * 0.45 + h / 2, z + t / 2, false));
        z += t + 0.004;
      }
    }

    // 右墙：一幅钉起来的平面图（读者自己的书房）
    const plan = new THREE.Mesh(new THREE.PlaneGeometry(0.6, 0.45), new THREE.MeshStandardMaterial({ map: planTexture() }));
    plan.position.set(1.585, 1.5, -0.3);
    plan.rotation.y = -Math.PI / 2;
    s.add(plan);
  }

  private bindInput(): void {
    this.dom.addEventListener('pointerdown', (e) => {
      if (this.mode !== 'looking' || this.tween) return;
      this.drag = { x: e.clientX, y: e.clientY, moved: 0 };
    });
    window.addEventListener('pointermove', (e) => {
      if (!this.drag) return;
      const dx = e.clientX - this.drag.x;
      const dy = e.clientY - this.drag.y;
      this.drag.moved += Math.abs(dx) + Math.abs(dy);
      this.drag.x = e.clientX;
      this.drag.y = e.clientY;
      this.yaw -= dx * 0.004;
      this.pitch = Math.max(-1.1, Math.min(1.1, this.pitch - dy * 0.004));
    });
    window.addEventListener('pointerup', (e) => {
      const d = this.drag;
      this.drag = null;
      if (!d || d.moved > 6 || this.mode !== 'looking') return;
      const ray = new THREE.Raycaster();
      const ndc = new THREE.Vector2((e.clientX / innerWidth) * 2 - 1, -(e.clientY / innerHeight) * 2 + 1);
      ray.setFromCamera(ndc, this.camera);
      if (ray.intersectObject(this.monitor, true).length) this.onClickMonitor();
    });
  }

  setScratches(v: boolean): void {
    if (v && !this.scratches.visible) this.flicker = 1.2;
    this.scratches.visible = v;
  }

  /** 切换到阅读或环顾 */
  setMode(mode: Mode, animate = true): void {
    this.mode = mode;
    if (mode === 'looking') {
      this.yaw = 0;
      this.pitch = -0.08;
    }
    const target = this.targetPose();
    if (!animate) {
      this.camera.position.copy(target.pos);
      this.camera.quaternion.copy(target.quat);
      this.tween = null;
      return;
    }
    this.tween = { from: this.camera.position.clone(), fromQ: this.camera.quaternion.clone(), t: 0, dur: 0.9 };
  }

  private targetPose(): { pos: THREE.Vector3; quat: THREE.Quaternion } {
    if (this.mode === 'reading') {
      return { pos: this.readPos.clone(), quat: new THREE.Quaternion() };
    }
    const q = new THREE.Quaternion().setFromEuler(new THREE.Euler(this.pitch, this.yaw, 0, 'YXZ'));
    return { pos: SEAT.clone(), quat: q };
  }

  resize(w: number, h: number): void {
    this.aspect = w / h;
    this.camera.aspect = this.aspect;
    this.camera.updateProjectionMatrix();
    // 让屏幕在阅读模式下占据视口约 92%
    const t = Math.tan(THREE.MathUtils.degToRad(this.camera.fov / 2));
    const fill = 0.92;
    const dist = Math.max(SCREEN_H / 2 / (t * fill), SCREEN_W / 2 / (t * this.aspect * fill));
    this.readPos.set(SCREEN_CENTER.x, SCREEN_CENTER.y, SCREEN_CENTER.z + dist);
    if (this.mode === 'reading' && !this.tween) this.camera.position.copy(this.readPos);
  }

  update(dt: number): void {
    const target = this.targetPose();
    if (this.tween) {
      this.tween.t += dt;
      const k = Math.min(1, this.tween.t / this.tween.dur);
      const e = k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2;
      this.camera.position.lerpVectors(this.tween.from, target.pos, e);
      this.camera.quaternion.slerpQuaternions(this.tween.fromQ, target.quat, e);
      if (k >= 1) this.tween = null;
    } else {
      this.camera.position.copy(target.pos);
      this.camera.quaternion.copy(target.quat);
    }

    // 台灯在异变出现时闪烁
    if (this.flicker > 0) {
      this.flicker -= dt;
      this.lamp.intensity = Math.random() < 0.5 ? 0.3 : 2.2;
      if (this.flicker <= 0) this.lamp.intensity = 2.2;
    }

    this.emitScreenRect();
    this.checkGaze(dt);
  }

  private emitScreenRect(): void {
    const corners = [
      new THREE.Vector3(-SCREEN_W / 2, SCREEN_H / 2, 0),
      new THREE.Vector3(SCREEN_W / 2, -SCREEN_H / 2, 0),
    ].map((v) => v.add(SCREEN_CENTER).project(this.camera));
    const x0 = ((corners[0].x + 1) / 2) * innerWidth;
    const y0 = ((1 - corners[0].y) / 2) * innerHeight;
    const x1 = ((corners[1].x + 1) / 2) * innerWidth;
    const y1 = ((1 - corners[1].y) / 2) * innerHeight;
    const visible = this.mode === 'reading' && !this.tween;
    this.onScreenRect({ x: x0, y: y0, w: x1 - x0, h: y1 - y0, visible });
  }

  private checkGaze(dt: number): void {
    if (!this.scratches.visible || this.mode !== 'looking') {
      this.gazeTime = 0;
      return;
    }
    const target = new THREE.Vector3();
    this.scratches.children[1].getWorldPosition(target);
    const toward = target.sub(this.camera.position).normalize();
    const forward = new THREE.Vector3(0, 0, -1).applyQuaternion(this.camera.quaternion);
    if (forward.dot(toward) > 0.96) {
      this.gazeTime += dt;
      if (this.gazeTime > 0.8) {
        this.gazeTime = -Infinity;
        this.onLookedAtScratches();
      }
    } else if (this.gazeTime > 0) {
      this.gazeTime = 0;
    }
  }
}

function planTexture(): THREE.CanvasTexture {
  const c = document.createElement('canvas');
  c.width = 384;
  c.height = 288;
  const g = c.getContext('2d')!;
  g.fillStyle = '#efeadf';
  g.fillRect(0, 0, 384, 288);
  g.strokeStyle = '#22252b';
  g.lineWidth = 6;
  g.strokeRect(70, 40, 240, 200);
  g.clearRect(230, 236, 50, 8);
  g.fillStyle = '#efeadf';
  g.fillRect(228, 234, 54, 12);
  g.lineWidth = 1.5;
  g.beginPath();
  g.arc(230, 240, 50, -Math.PI / 2, 0);
  g.stroke();
  g.strokeRect(120, 46, 140, 50);
  g.font = '14px Georgia, serif';
  g.fillStyle = '#22252b';
  g.fillText('STUDY  3200 × 3600', 120, 270);
  g.fillText('N ↑', 330, 60);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}
