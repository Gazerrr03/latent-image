import type { DoorStatus } from '../state';

/**
 * 玩家批注的意图。
 * describe：补充描述，让事物成立；deny：否认，让事物消失；
 * measure：把测量结果写进记录；ask：提问；note：只作为读者记录保留。
 */
export type IntentKind = 'describe' | 'deny' | 'measure' | 'ask' | 'note';

export interface IntentRequest {
  slotId: string;
  text: string;
  context: {
    doorStatus: DoorStatus;
    measuredLength: number | null;
  };
}

export interface IntentResult {
  kinds: IntentKind[];
  door?: { status: DoorStatus; number?: string | null; color?: string | null };
  recordedLength?: number;
  /** 编剧以场景提示回应玩家 */
  stage: string;
}

/** 意图解析接口。MVP 使用规则实现，之后可替换为模型实现。 */
export interface IntentResolver {
  readonly label: string;
  resolve(req: IntentRequest): Promise<IntentResult>;
}
