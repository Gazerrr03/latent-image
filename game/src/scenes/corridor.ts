import * as THREE from 'three';
import { audio } from '../audio';
import { FirstPersonControls } from '../controls';
import type { Hud } from '../hud';
import { COLOR_HEX } from '../intent/ruleResolver';
import type { GameState } from '../state';
import { cn } from '../util';
import {
  box,
  disposeTree,
  gridLines,
  parquetTexture,
  plateTexture,
  wallpaperTexture,
  whiteMat,
  withEdges,
  woodTexture,
  type GameScene,
} from './common';

const WIDTH = 1.4;
const HEIGHT = 2.5;
const LONG = 60;
const EYE = 1.6;
const SPEED = 1.5;
const STRIDE = 0.72;
/** 录音里记下的走廊长度 */
const RECORDED = 4.2;
/** 门未被描述时，玩家每前进 1 米，门后退的距离 */
const RETREAT = 0.6;
const DOOR_W = 0.9;
const DOOR_H = 2.05;
/** 门后黑暗中能走的距离 */
const BEYOND = 14;
/** 进入黑暗后，走到第几步时声音停下 */
const COUNT_TO = 12;

export interface VisitResult {
  steps: number;
  doorDist: number;
  /** 是否走完了门后（或门原本所在处之后）的那段黑暗 */
  reachedBeyond: boolean;
  measured: number | null;
}

interface SideDoor {
  group: THREE.Group;
  center: THREE.Vector3;
  unseen: number;
  flipped: boolean;
}

/**
 * 沉浸空间：梣林巷 7 号二楼走廊。
 * 被描述过的部分有材质，其余是白模。
 */
export class CorridorScene implements GameScene {
  readonly scene = new THREE.Scene();
  readonly camera = new THREE.PerspectiveCamera(70, 1, 0.05, 80);
  readonly controls: FirstPersonControls;
  onExit: (r: VisitResult) => void = () => {};

  private root = new THREE.Group();
  private end = new THREE.Group();
  private panelPivot = new THREE.Group();
  private sideDoors: SideDoor[] = [];
  private playerLight = new THREE.PointLight(0xffe2bc, 3, 9, 1.6);
  private frustum = new THREE.Frustum();
  private mat4 = new THREE.Matrix4();

  private s!: GameState;
  private pos = new THREE.Vector3();
  private doorDist = RECORDED;
  private maxProgress = 0;
  private doorOpen = 0;
  private opening = false;
  private steps = 0;
  private strideAcc = 0;
  private measured: number | null = null;
  private seq: { startSteps: number; phase: 'walk' | 'silence' | 'done'; timer: number } | null = null;
  private exiting = false;
  private active = false;

  constructor(
    dom: HTMLElement,
    private hud: Hud,
  ) {
    this.controls = new FirstPersonControls(dom);
    this.scene.background = new THREE.Color(0x000000);
    this.scene.fog = new THREE.Fog(0x000000, 1.5, 13);
    this.scene.add(new THREE.AmbientLight(0xffffff, 0.05));
    this.scene.add(this.playerLight);
    this.scene.add(this.root);
    window.addEventListener('keydown', (e) => this.onKey(e));
  }

  // ───────────── 进入时按当前状态搭建 ─────────────

  enter(s: GameState): void {
    this.s = s;
    disposeTree(this.root);
    this.root.clear();
    this.end = new THREE.Group();
    this.panelPivot = new THREE.Group();
    this.sideDoors = [];
    this.pos.set(0, EYE, -0.2);
    this.controls.yaw = 0;
    this.controls.pitch = 0;
    this.maxProgress = 0;
    this.doorOpen = 0;
    this.opening = false;
    this.steps = 0;
    this.strideAcc = 0;
    this.measured = null;
    this.seq = null;
    this.exiting = false;
    this.active = true;
    this.playerLight.intensity = 3;

    if (s.door.status === 'bare') this.doorDist = RECORDED;
    else this.doorDist = s.recordedLength ?? s.lastDoorDist ?? RECORDED + 5;

    // 门被描述过时，走廊止于门；门后只有黑暗
    const total = s.door.status === 'described' ? this.doorDist : LONG;
    const described = Math.min(s.recordedLength ?? RECORDED, total);
    this.buildShell(described, total);
    this.buildEntrance();
    this.buildSideDoors(described, total);
    if (s.door.status !== 'denied') this.buildEnd(s);
    this.root.add(this.end);
    this.controls.enabled = true;
  }

  leave(): void {
    this.active = false;
    this.controls.enabled = false;
    this.controls.unlock();
  }

  private buildShell(describedLen: number, totalLen: number): void {
    const white = whiteMat();
    const floorTex = parquetTexture();
    floorTex.repeat.set(WIDTH / 0.9, describedLen / 0.9);
    const floorMat = new THREE.MeshStandardMaterial({ map: floorTex, roughness: 0.75 });
    const paperTex = wallpaperTexture();
    paperTex.repeat.set(describedLen / 0.7, HEIGHT / 0.7);
    const paperMat = new THREE.MeshStandardMaterial({ map: paperTex, roughness: 0.9 });
    const ceilMat = new THREE.MeshStandardMaterial({ color: 0xcfc8b8, roughness: 1 });

    const r = this.root;
    const restLen = totalLen - describedLen;

    // 被描述的部分：从入口到 describedLen
    r.add(box(WIDTH, 0.02, describedLen, floorMat, 0, -0.01, -describedLen / 2, false));
    r.add(box(0.02, HEIGHT, describedLen, paperMat, -WIDTH / 2, HEIGHT / 2, -describedLen / 2, false));
    r.add(box(0.02, HEIGHT, describedLen, paperMat, WIDTH / 2, HEIGHT / 2, -describedLen / 2, false));
    r.add(box(WIDTH, 0.02, describedLen, ceilMat, 0, HEIGHT + 0.01, -describedLen / 2, false));
    // 踢脚线
    const base = new THREE.MeshStandardMaterial({ color: 0x3b2a1d, roughness: 0.7 });
    r.add(box(0.03, 0.1, describedLen, base, -WIDTH / 2 + 0.015, 0.05, -describedLen / 2, false));
    r.add(box(0.03, 0.1, describedLen, base, WIDTH / 2 - 0.015, 0.05, -describedLen / 2, false));

    if (totalLen < LONG) {
      const voidFloor = new THREE.MeshStandardMaterial({ color: 0x1c1b19, roughness: 1 });
      r.add(box(4, 0.02, BEYOND + 2, voidFloor, 0, -0.01, -totalLen - (BEYOND + 2) / 2, false));
    }
    if (restLen <= 0.01) return;

    // 未被描述的部分：白模
    const zc = -describedLen - restLen / 2;
    r.add(box(WIDTH, 0.02, restLen, white, 0, -0.01, zc));
    r.add(box(0.02, HEIGHT, restLen, white, -WIDTH / 2, HEIGHT / 2, zc));
    r.add(box(0.02, HEIGHT, restLen, white, WIDTH / 2, HEIGHT / 2, zc));
    r.add(box(WIDTH, 0.02, restLen, white, 0, HEIGHT + 0.01, zc));
    r.add(gridLines(WIDTH, restLen, 0.6, 0.002, -describedLen));
  }

  private buildEntrance(): void {
    // 身后是回到书房的门洞，透出一点暖光
    const white = whiteMat();
    const z = 0.3;
    this.root.add(box(WIDTH, HEIGHT - DOOR_H, 0.05, white, 0, (HEIGHT + DOOR_H) / 2, z));
    this.root.add(box((WIDTH - DOOR_W) / 2, DOOR_H, 0.05, white, -(WIDTH + DOOR_W) / 4, DOOR_H / 2, z));
    this.root.add(box((WIDTH - DOOR_W) / 2, DOOR_H, 0.05, white, (WIDTH + DOOR_W) / 4, DOOR_H / 2, z));
    const glow = new THREE.Mesh(new THREE.PlaneGeometry(DOOR_W, DOOR_H), new THREE.MeshBasicMaterial({ color: 0xffd9a6 }));
    glow.position.set(0, DOOR_H / 2, z + 0.03);
    glow.rotation.y = Math.PI;
    this.root.add(glow);
    const spill = new THREE.PointLight(0xffc98a, 1.2, 4, 2);
    spill.position.set(0, 1.4, 0);
    this.root.add(spill);
  }

  private buildSideDoors(describedLen: number, totalLen: number): void {
    const white = whiteMat();
    const wood = new THREE.MeshStandardMaterial({ map: woodTexture('#4d3524'), roughness: 0.75 });
    for (let z = -1.3; z > Math.max(-20, -totalLen + 0.7); z -= 1.35) {
      for (const side of [-1, 1]) {
        const g = new THREE.Group();
        const mat = -z < describedLen ? wood : white;
        const x = side * (WIDTH / 2 - 0.02);
        g.add(box(0.03, DOOR_H - 0.3, 0.72, mat, x, (DOOR_H - 0.3) / 2, z, mat === white));
        g.add(box(0.05, 0.06, 0.82, mat, x, DOOR_H - 0.27, z, mat === white));
        g.visible = Math.random() < 0.5;
        this.root.add(g);
        this.sideDoors.push({ group: g, center: new THREE.Vector3(x, 1, z), unseen: 0, flipped: false });
      }
    }
  }

  private buildEnd(s: GameState): void {
    const described = s.door.status === 'described';
    const white = whiteMat();
    const wallMat = described ? new THREE.MeshStandardMaterial({ map: wallpaperTexture(), roughness: 0.9 }) : white;
    const e = this.end;
    // 尽头墙，中间留门洞
    e.add(box(WIDTH, HEIGHT - DOOR_H, 0.06, wallMat, 0, (HEIGHT + DOOR_H) / 2, 0, !described));
    e.add(box((WIDTH - DOOR_W) / 2, DOOR_H, 0.06, wallMat, -(WIDTH + DOOR_W) / 4, DOOR_H / 2, 0, !described));
    e.add(box((WIDTH - DOOR_W) / 2, DOOR_H, 0.06, wallMat, (WIDTH + DOOR_W) / 4, DOOR_H / 2, 0, !described));

    // 门扇绕左侧铰链旋转
    let panelMat: THREE.Material = white;
    if (described) {
      const hex = s.door.color ? COLOR_HEX[s.door.color] : '#5a3b26';
      panelMat = new THREE.MeshStandardMaterial({ map: woodTexture(hex), roughness: 0.65 });
    }
    this.panelPivot.position.set(-DOOR_W / 2, 0, 0);
    const panel = box(DOOR_W, DOOR_H, 0.045, panelMat, DOOR_W / 2, DOOR_H / 2, 0.01, !described);
    this.panelPivot.add(panel);
    if (described) {
      const brass = new THREE.MeshStandardMaterial({ color: 0xb09358, roughness: 0.35, metalness: 0.8 });
      const knob = new THREE.Mesh(new THREE.SphereGeometry(0.035, 16, 12), brass);
      knob.position.set(DOOR_W - 0.09, 1.0, 0.07);
      this.panelPivot.add(knob);
      if (s.door.number) {
        const plate = new THREE.Mesh(
          new THREE.PlaneGeometry(0.16, 0.08),
          new THREE.MeshStandardMaterial({ map: plateTexture(s.door.number), roughness: 0.4, metalness: 0.5 }),
        );
        plate.position.set(DOOR_W / 2, 1.6, 0.036);
        this.panelPivot.add(plate);
      }
    } else {
      // 白模门：把手的位置是平的
      const ghost = withEdges(new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.06, 0.005), white));
      ghost.position.set(DOOR_W - 0.09, 1.0, 0.037);
      this.panelPivot.add(ghost);
    }
    e.add(this.panelPivot);

    // 门后：只有黑暗
    e.position.z = -this.doorDist;
  }

  // ───────────── 交互 ─────────────

  private onKey(e: KeyboardEvent): void {
    if (!this.active || !this.controls.locked || this.exiting) return;
    if (e.code === 'KeyF') this.measure();
    if (e.code === 'KeyE') this.interact();
  }

  private measure(): void {
    const d = Math.max(0, -this.pos.z);
    this.hud.showReadout(`卷尺：距入口 ${d.toFixed(2)} 米`);
    if (d > 1) this.measured = Math.max(this.measured ?? 0, Math.round(d * 100) / 100);
  }

  private interact(): void {
    const near = this.nearWhat();
    if (near === 'entrance') this.exit(false);
    else if (near === 'door') {
      if (this.s.door.status === 'described') {
        if (!this.opening) {
          this.opening = true;
          audio.step(0.5);
        }
      } else {
        this.hud.showReadout('门把手的位置是平的，像还没画上去。', 3200);
      }
    }
  }

  private nearWhat(): 'entrance' | 'door' | null {
    if (this.pos.z > -0.6) return 'entrance';
    if (this.s.door.status !== 'denied' && !this.opening && Math.abs(this.pos.z + this.doorDist) < 1.1) return 'door';
    return null;
  }

  /** 离开走廊，回到书房 */
  exit(reachedBeyond: boolean): void {
    if (this.exiting) return;
    this.exiting = true;
    this.controls.enabled = false;
    this.onExit({
      steps: this.steps,
      doorDist: this.doorDist,
      reachedBeyond,
      measured: this.measured,
    });
  }

  // ───────────── 每帧 ─────────────

  resize(w: number, h: number): void {
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
  }

  update(dt: number): void {
    if (!this.active) return;
    this.move(dt);
    this.controls.apply(this.camera);
    this.camera.position.copy(this.pos);
    this.camera.position.y += Math.sin(this.strideAcc / STRIDE * Math.PI * 2) * 0.012;
    this.playerLight.position.set(this.pos.x, this.pos.y - 0.2, this.pos.z);

    this.updateDoor(dt);
    this.updateSideDoors(dt);
    this.updateSequence(dt);

    if (!this.exiting && !this.seq) {
      const near = this.nearWhat();
      this.hud.setHint(near === 'entrance' ? 'E　回到书桌前' : near === 'door' ? 'E　推门' : '');
    }
  }

  private move(dt: number): void {
    const frozen = this.seq && this.seq.phase !== 'walk';
    const dir = frozen ? { x: 0, z: 0 } : this.controls.moveDir();
    const speed = this.seq ? SPEED * 0.75 : SPEED;
    const nx = this.pos.x + dir.x * speed * dt;
    const nz = this.pos.z + dir.z * speed * dt;
    const before = this.pos.clone();

    const halfW = WIDTH / 2 - 0.25;
    this.pos.x = Math.max(-halfW, Math.min(halfW, nx));
    let minZ = -LONG + 1;
    if (this.s.door.status !== 'denied') {
      const doorPlane = -this.doorDist;
      const passable = this.doorOpen > 0.85 && Math.abs(this.pos.x) < DOOR_W / 2 - 0.2;
      if (this.pos.z > doorPlane + 0.3) minZ = passable ? doorPlane - BEYOND : doorPlane + 0.6;
      else minZ = doorPlane - BEYOND;
      if (this.pos.z <= doorPlane + 0.3) this.pos.x = Math.max(-0.25, Math.min(0.25, this.pos.x));
    }
    this.pos.z = Math.max(minZ, Math.min(0.1, nz));

    const moved = Math.hypot(this.pos.x - before.x, this.pos.z - before.z);
    this.strideAcc += moved;
    if (this.strideAcc >= STRIDE) {
      this.strideAcc -= STRIDE;
      this.steps++;
      audio.step(this.seq ? 0.7 : 1);
      this.onStep();
    }
    this.maxProgress = Math.max(this.maxProgress, -this.pos.z);
  }

  private updateDoor(dt: number): void {
    if (this.s.door.status === 'bare') {
      // 走廊比记录的要长：你往前走，门往后退
      this.doorDist = RECORDED + RETREAT * Math.max(0, this.maxProgress - 1);
      this.end.position.z = -this.doorDist;
    }
    if (this.opening && this.doorOpen < 1) {
      this.doorOpen = Math.min(1, this.doorOpen + dt / 1.6);
      const e = 1 - Math.pow(1 - this.doorOpen, 3);
      this.panelPivot.rotation.y = -e * 1.75;
    }
  }

  /** 两侧的门：你不看它的时候，它的数目会变 */
  private updateSideDoors(dt: number): void {
    this.camera.updateMatrixWorld();
    this.mat4.multiplyMatrices(this.camera.projectionMatrix, this.camera.matrixWorldInverse);
    this.frustum.setFromProjectionMatrix(this.mat4);
    const sphere = new THREE.Sphere();
    for (const d of this.sideDoors) {
      sphere.set(d.center, 1.1);
      const seen = this.frustum.intersectsSphere(sphere) && d.center.distanceTo(this.pos) < 14;
      if (seen) {
        d.unseen = 0;
        d.flipped = false;
      } else {
        d.unseen += dt;
        if (d.unseen > 0.6 && !d.flipped) {
          d.flipped = true;
          if (Math.random() < 0.5) d.group.visible = !d.group.visible;
        }
      }
    }
  }

  private beyondLine(): number {
    return -this.doorDist - 0.6;
  }

  private onStep(): void {
    if (!this.seq && this.s.door.status !== 'bare' && this.pos.z < this.beyondLine()) {
      this.seq = { startSteps: this.steps, phase: 'walk', timer: 0 };
      audio.setDrone(0.9, 4);
    }
    if (this.seq && this.seq.phase === 'walk') {
      const n = this.steps - this.seq.startSteps + 1;
      // 黑暗里有人在数，比你慢一拍
      if (n >= 2) this.hud.setSubtitle(`[录音转写]　……${cn(n - 1)}……`);
      this.playerLight.intensity = Math.max(0.4, 3 - n * 0.22);
      if (n >= COUNT_TO || this.pos.z < -this.doorDist - BEYOND + 0.8) {
        this.seq.phase = 'silence';
        this.seq.timer = 0;
        this.hud.setSubtitle('[约 40 秒静音]');
      }
    }
  }

  private updateSequence(dt: number): void {
    const q = this.seq;
    if (!q || q.phase === 'walk') return;
    q.timer += dt;
    if (q.phase === 'silence' && q.timer > 3) {
      q.phase = 'done';
      q.timer = 0;
      const n = this.steps - q.startSteps + 1;
      // 最后一声，比你快了一拍
      this.hud.setSubtitle(`[录音转写]　……${cn(n + 1)}。`);
      this.playerLight.intensity = 0;
    }
    if (q.phase === 'done' && q.timer > 2.4) {
      this.seq = null;
      this.exit(true);
    }
  }
}
