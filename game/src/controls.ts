import type * as THREE from 'three';

/** 第一人称视角：鼠标锁定转视角，WASD 移动 */
export class FirstPersonControls {
  yaw = 0;
  pitch = 0;
  enabled = false;
  locked = false;
  onUnlock: () => void = () => {};
  private keys = new Set<string>();

  constructor(private dom: HTMLElement) {
    document.addEventListener('pointerlockchange', () => {
      const was = this.locked;
      this.locked = document.pointerLockElement === this.dom;
      if (was && !this.locked) {
        this.keys.clear();
        this.onUnlock();
      }
    });
    document.addEventListener('mousemove', (e) => {
      if (!this.enabled || !this.locked) return;
      this.yaw -= e.movementX * 0.0022;
      this.pitch -= e.movementY * 0.0022;
      this.pitch = Math.max(-1.3, Math.min(1.3, this.pitch));
    });
    window.addEventListener('keydown', (e) => this.keys.add(e.code));
    window.addEventListener('keyup', (e) => this.keys.delete(e.code));
    window.addEventListener('blur', () => this.keys.clear());
  }

  lock(): void {
    void this.dom.requestPointerLock();
  }

  unlock(): void {
    if (document.pointerLockElement) document.exitPointerLock();
  }

  /** 水平面上的期望位移方向（未归一化前的输入，返回单位向量或零） */
  moveDir(): { x: number; z: number } {
    if (!this.enabled || !this.locked) return { x: 0, z: 0 };
    const k = this.keys;
    const f = (k.has('KeyW') || k.has('ArrowUp') ? 1 : 0) - (k.has('KeyS') || k.has('ArrowDown') ? 1 : 0);
    const s = (k.has('KeyD') || k.has('ArrowRight') ? 1 : 0) - (k.has('KeyA') || k.has('ArrowLeft') ? 1 : 0);
    if (!f && !s) return { x: 0, z: 0 };
    const sin = Math.sin(this.yaw);
    const cos = Math.cos(this.yaw);
    let x = -sin * f + cos * s;
    let z = -cos * f - sin * s;
    const len = Math.hypot(x, z);
    x /= len;
    z /= len;
    return { x, z };
  }

  apply(camera: THREE.Camera): void {
    camera.rotation.set(this.pitch, this.yaw, 0, 'YXZ');
  }
}
