import * as THREE from 'three';

export interface GameScene {
  readonly scene: THREE.Scene;
  readonly camera: THREE.PerspectiveCamera;
  update(dt: number): void;
  resize(w: number, h: number): void;
}

export const WHITE = 0xe6e3dc;

/** 白模材质：未被描述的部分 */
export function whiteMat(): THREE.MeshStandardMaterial {
  return new THREE.MeshStandardMaterial({ color: WHITE, roughness: 0.95, metalness: 0 });
}

const edgeMat = new THREE.LineBasicMaterial({ color: 0x1a1a1a, transparent: true, opacity: 0.6 });

/** 给网格加上模型轮廓线 */
export function withEdges<T extends THREE.Mesh>(mesh: T): T {
  mesh.add(new THREE.LineSegments(new THREE.EdgesGeometry(mesh.geometry, 20), edgeMat));
  return mesh;
}

/** 以中心点放置的盒体 */
export function box(
  w: number,
  h: number,
  d: number,
  mat: THREE.Material,
  x: number,
  y: number,
  z: number,
  edges = true,
): THREE.Mesh {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
  m.position.set(x, y, z);
  return edges ? withEdges(m) : m;
}

/** 平面上的模型网格线，用于白模地面 */
export function gridLines(w: number, d: number, step: number, y: number, z0: number): THREE.LineSegments {
  const pts: number[] = [];
  for (let z = 0; z <= d + 1e-6; z += step) pts.push(-w / 2, y, z0 - z, w / 2, y, z0 - z);
  pts.push(-w / 2, y, z0, -w / 2, y, z0 - d, w / 2, y, z0, w / 2, y, z0 - d);
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pts, 3));
  return new THREE.LineSegments(g, new THREE.LineBasicMaterial({ color: 0x2a2a2a, transparent: true, opacity: 0.35 }));
}

export function disposeTree(obj: THREE.Object3D): void {
  obj.traverse((o) => {
    const m = o as THREE.Mesh;
    if (m.geometry) m.geometry.dispose();
  });
}

// ───────────── 程序化贴图：被描述过的部分才有材质 ─────────────

function canvasTex(w: number, h: number, draw: (g: CanvasRenderingContext2D) => void): THREE.CanvasTexture {
  const c = document.createElement('canvas');
  c.width = w;
  c.height = h;
  draw(c.getContext('2d')!);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.anisotropy = 8;
  return t;
}

function rand(seed: number): () => number {
  let s = seed;
  return () => {
    s = (s * 16807) % 2147483647;
    return s / 2147483647;
  };
}

/** 人字拼橡木地板，周期 8W×8W，可无缝平铺 */
export function parquetTexture(): THREE.CanvasTexture {
  const W = 32;
  const L = 4 * W;
  const P = 8 * W;
  const r = rand(7);
  return canvasTex(P, P, (g) => {
    g.fillStyle = '#2b1d12';
    g.fillRect(0, 0, P, P);
    const plank = (x: number, y: number, w: number, h: number) => {
      const shade = 0.75 + r() * 0.35;
      g.fillStyle = `rgb(${Math.round(118 * shade)},${Math.round(82 * shade)},${Math.round(52 * shade)})`;
      for (const ox of [-P, 0, P]) for (const oy of [-P, 0, P]) g.fillRect(x + ox + 1, y + oy + 1, w - 2, h - 2);
    };
    for (let b = -4; b <= 4; b++) {
      for (let n = -12; n <= 12; n++) {
        const bx = b * L + n * W;
        const by = -b * L + n * W;
        if (bx < -L || bx > P + L || by < -L || by > P + L) continue;
        plank(bx, by, L, W);
        plank(bx - W, by, W, L);
      }
    }
  });
}

/** 褪色藤蔓纹墙纸 */
export function wallpaperTexture(): THREE.CanvasTexture {
  const S = 256;
  return canvasTex(S, S, (g) => {
    g.fillStyle = '#9aa391';
    g.fillRect(0, 0, S, S);
    g.strokeStyle = 'rgba(70,88,66,0.55)';
    g.fillStyle = 'rgba(70,88,66,0.45)';
    g.lineWidth = 3;
    for (const cx of [64, 192]) {
      const phase = cx === 64 ? 0 : Math.PI;
      g.beginPath();
      for (let y = 0; y <= S; y += 4) {
        const x = cx + Math.sin((y / S) * Math.PI * 2 + phase) * 18;
        if (y === 0) g.moveTo(x, y);
        else g.lineTo(x, y);
      }
      g.stroke();
      for (let k = 0; k < 4; k++) {
        const y = 32 + k * 64;
        const x = cx + Math.sin((y / S) * Math.PI * 2 + phase) * 18;
        const dir = k % 2 ? 1 : -1;
        g.save();
        g.translate(x + dir * 12, y);
        g.rotate(dir * 0.7);
        g.beginPath();
        g.ellipse(0, 0, 13, 6, 0, 0, Math.PI * 2);
        g.fill();
        g.restore();
      }
    }
    // 褪色与污渍
    const r = rand(3);
    for (let i = 0; i < 40; i++) {
      g.fillStyle = `rgba(60,50,30,${r() * 0.05})`;
      g.beginPath();
      g.arc(r() * S, r() * S, 10 + r() * 40, 0, Math.PI * 2);
      g.fill();
    }
  });
}

/** 木门纹理 */
export function woodTexture(base = '#5a3b26'): THREE.CanvasTexture {
  const r = rand(11);
  return canvasTex(128, 256, (g) => {
    g.fillStyle = base;
    g.fillRect(0, 0, 128, 256);
    for (let i = 0; i < 60; i++) {
      g.strokeStyle = `rgba(0,0,0,${0.05 + r() * 0.12})`;
      g.lineWidth = 1 + r() * 2;
      const x = r() * 128;
      g.beginPath();
      g.moveTo(x, 0);
      g.bezierCurveTo(x + r() * 8 - 4, 80, x + r() * 8 - 4, 170, x + r() * 6 - 3, 256);
      g.stroke();
    }
    g.strokeStyle = 'rgba(0,0,0,0.35)';
    g.lineWidth = 3;
    g.strokeRect(14, 18, 100, 96);
    g.strokeRect(14, 138, 100, 100);
  });
}

/** 门牌 */
export function plateTexture(text: string): THREE.CanvasTexture {
  return canvasTex(128, 64, (g) => {
    g.fillStyle = '#8c7442';
    g.fillRect(0, 0, 128, 64);
    g.strokeStyle = '#3d301a';
    g.lineWidth = 4;
    g.strokeRect(4, 4, 120, 56);
    g.fillStyle = '#231b0e';
    g.font = 'bold 40px Georgia, serif';
    g.textAlign = 'center';
    g.textBaseline = 'middle';
    g.fillText(text, 64, 34);
  });
}
