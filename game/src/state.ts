import type { IntentKind } from './intent/types';

export type DoorStatus = 'bare' | 'described' | 'denied';

export interface ReaderAnnotation {
  id: string;
  slotId: string;
  text: string;
  intent: IntentKind;
  createdAt: number;
}

export interface GameState {
  version: 1;
  corridorVisits: number;
  /** 玩家用卷尺量到的最远距离（米） */
  measuredLength: number | null;
  /** 被写进记录的走廊长度；写进去之后，这段走廊就"被描述"了 */
  recordedLength: number | null;
  /** 上一次探索结束时尽头门所在的距离 */
  lastDoorDist: number | null;
  door: { status: DoorStatus; number: string | null; color: string | null };
  annotations: ReaderAnnotation[];
  /** blockId -> 修订时间戳，供站务修订记录使用 */
  revisions: Record<string, number>;
  lastSteps: number;
  flags: {
    scratches?: boolean;
    anomalyTyped?: boolean;
    sawScratches?: boolean;
    ghostNote?: boolean;
    chapterDone?: boolean;
  };
}

const KEY = 'errata.save.v1';

function defaultState(): GameState {
  return {
    version: 1,
    corridorVisits: 0,
    measuredLength: null,
    recordedLength: null,
    lastDoorDist: null,
    door: { status: 'bare', number: null, color: null },
    annotations: [],
    revisions: {},
    lastSteps: 0,
    flags: {},
  };
}

function load(): GameState {
  if (new URLSearchParams(location.search).has('reset')) localStorage.removeItem(KEY);
  try {
    const raw = localStorage.getItem(KEY);
    if (raw) {
      const parsed = JSON.parse(raw) as GameState;
      if (parsed.version === 1) return { ...defaultState(), ...parsed };
    }
  } catch {
    // 存档损坏时从头开始
  }
  return defaultState();
}

export const state: GameState = load();

export function hasProgress(): boolean {
  return state.corridorVisits > 0 || state.annotations.length > 0;
}

export function save(): void {
  localStorage.setItem(KEY, JSON.stringify(state));
}

export function restart(): void {
  localStorage.removeItem(KEY);
  location.href = location.pathname;
}
