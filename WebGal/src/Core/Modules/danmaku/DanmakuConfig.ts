export interface DanmakuServerConfig {
  apiBase: string;
  projectKey: string;
  fontFamily?: string;
  defaultColor?: string;
  maxContentLength?: number;
  fetchOnStartTip?: boolean;
}

export interface DanmakuRawItem {
  c: string;
  o: string;
}

export interface DanmakuDataMap {
  [sayId: string]: DanmakuRawItem[];
}

export const DANMAKU_DEFAULTS = {
  apiBase: '',
  projectKey: '',
  defaultColor: '#ff80b8',
  maxContentLength: 50,
  fetchOnStartTip: true,
} as const;

export const DANMAKU_COLOR_PRESETS = [
  { name: '粉', value: '#ff80b8' },
  { name: '黑', value: '#333333' },
  { name: '蓝', value: '#2059d4' },
  { name: '黄', value: '#ffe066' },
  { name: '白', value: '#ffffff' },
] as const;

export function danmakuIsValidColor(color: string): boolean {
  return /^#[0-9a-fA-F]{6}$/.test(color);
}

export function danmakuNormalizeColor(color: string, fallback: string): string {
  return danmakuIsValidColor(color) ? color : fallback;
}

export function danmakuClampContent(text: string, maxLen: number): string {
  if (text.length > maxLen) return text.slice(0, maxLen);
  return text;
}
