/** 全部用 WebAudio 合成，不依赖音频素材 */
class GameAudio {
  private ctx?: AudioContext;
  private master?: GainNode;
  private droneGain?: GainNode;
  private noise?: AudioBuffer;

  /** 必须在用户操作中调用 */
  init(): void {
    if (this.ctx) {
      void this.ctx.resume();
      return;
    }
    const ctx = new AudioContext();
    this.ctx = ctx;
    this.master = ctx.createGain();
    this.master.gain.value = 0.9;
    this.master.connect(ctx.destination);

    const len = ctx.sampleRate * 1;
    this.noise = ctx.createBuffer(1, len, ctx.sampleRate);
    const data = this.noise.getChannelData(0);
    for (let i = 0; i < len; i++) data[i] = Math.random() * 2 - 1;

    // 低频嗡鸣
    this.droneGain = ctx.createGain();
    this.droneGain.gain.value = 0;
    const lp = ctx.createBiquadFilter();
    lp.type = 'lowpass';
    lp.frequency.value = 220;
    lp.connect(this.droneGain);
    this.droneGain.connect(this.master);
    for (const f of [55, 55.7, 82.4]) {
      const o = ctx.createOscillator();
      o.type = 'sawtooth';
      o.frequency.value = f;
      const g = ctx.createGain();
      g.gain.value = 0.05;
      o.connect(g).connect(lp);
      o.start();
    }
    const hiss = ctx.createBufferSource();
    hiss.buffer = this.noise;
    hiss.loop = true;
    const hp = ctx.createBiquadFilter();
    hp.type = 'bandpass';
    hp.frequency.value = 900;
    hp.Q.value = 0.4;
    const hg = ctx.createGain();
    hg.gain.value = 0.012;
    hiss.connect(hp).connect(hg).connect(this.droneGain);
    hiss.start();
  }

  /** 0–1 */
  setDrone(level: number, seconds = 2): void {
    if (!this.ctx || !this.droneGain) return;
    const t = this.ctx.currentTime;
    this.droneGain.gain.cancelScheduledValues(t);
    this.droneGain.gain.setValueAtTime(this.droneGain.gain.value, t);
    this.droneGain.gain.linearRampToValueAtTime(level * 0.6, t + seconds);
  }

  step(volume = 1): void {
    if (!this.ctx || !this.noise || !this.master) return;
    const ctx = this.ctx;
    const t = ctx.currentTime;
    const src = ctx.createBufferSource();
    src.buffer = this.noise;
    const f = ctx.createBiquadFilter();
    f.type = 'lowpass';
    f.frequency.value = 500 + Math.random() * 250;
    const g = ctx.createGain();
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(0.35 * volume, t + 0.012);
    g.gain.exponentialRampToValueAtTime(0.0001, t + 0.16);
    src.connect(f).connect(g).connect(this.master);
    src.start(t, Math.random() * 0.5, 0.2);
  }

  /** 异变出现时的一声 */
  sting(): void {
    if (!this.ctx || !this.noise || !this.master) return;
    const ctx = this.ctx;
    const t = ctx.currentTime;
    const o = ctx.createOscillator();
    o.type = 'sine';
    o.frequency.setValueAtTime(70, t);
    o.frequency.exponentialRampToValueAtTime(38, t + 1.6);
    const g = ctx.createGain();
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(0.5, t + 0.05);
    g.gain.exponentialRampToValueAtTime(0.0001, t + 2.2);
    o.connect(g).connect(this.master);
    o.start(t);
    o.stop(t + 2.3);

    // 刮擦声
    for (let i = 0; i < 3; i++) {
      const s = ctx.createBufferSource();
      s.buffer = this.noise;
      const bp = ctx.createBiquadFilter();
      bp.type = 'bandpass';
      bp.Q.value = 6;
      const st = t + 0.25 + i * 0.32;
      bp.frequency.setValueAtTime(2400, st);
      bp.frequency.linearRampToValueAtTime(1200, st + 0.22);
      const sg = ctx.createGain();
      sg.gain.setValueAtTime(0.0001, st);
      sg.gain.exponentialRampToValueAtTime(0.18, st + 0.03);
      sg.gain.exponentialRampToValueAtTime(0.0001, st + 0.24);
      s.connect(bp).connect(sg).connect(this.master);
      s.start(st, Math.random() * 0.5, 0.26);
    }
  }
}

export const audio = new GameAudio();
