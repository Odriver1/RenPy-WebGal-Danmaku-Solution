import { webgalStore } from '@/store/store';
import { setConnectionStatus } from '@/store/danmakuReducer';
import {
  DanmakuDataMap,
  DanmakuRawItem,
  DANMAKU_DEFAULTS,
  danmakuIsValidColor,
} from './DanmakuConfig';

// Re-export for convenience
export type { DanmakuDataMap, DanmakuRawItem } from './DanmakuConfig';

export class DanmakuApi {
  private apiBase: string;
  private projectKey: string;

  constructor(apiBase: string, projectKey: string) {
    this.apiBase = apiBase.replace(/\/+$/, '');
    this.projectKey = projectKey;
  }

  private getEndpoint(kind: 'health' | 'comments'): string {
    const safeKey = encodeURIComponent(this.projectKey);
    if (kind === 'health') {
      return `${this.apiBase}/projects/${safeKey}/health`;
    }
    return `${this.apiBase}/projects/${safeKey}/comments`;
  }

  async fetchAll(): Promise<DanmakuDataMap> {
    const url = this.getEndpoint('comments');
    console.log('[DanmakuApi] GET', url);
    const resp = await fetch(url, { signal: AbortSignal.timeout(10000) });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const payload = await resp.json();
    console.log('[DanmakuApi] GET response:', payload);
    if (payload?.ok === false) throw new Error(payload.msg ?? 'fetch failed');
    const result = this.normalizeItems(payload);
    console.log('[DanmakuApi] normalized:', result);
    return result;
  }

  async submit(sayId: string, content: string, color: string): Promise<{ status: string }> {
    const url = this.getEndpoint('comments');
    const body = { say_id: sayId, content, color };
    console.log('[DanmakuApi] POST', url, body);
    const resp = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(8000),
    });
    const result = await resp.json();
    console.log('[DanmakuApi] POST response:', result);
    if (!result.ok) throw new Error(result.msg ?? 'submit failed');
    return { status: result.status ?? 'approved' };
  }

  normalizeItems(raw: any): DanmakuDataMap {
    if (!raw || typeof raw !== 'object') return {};

    // Unwrap common API wrappers
    let source = raw;
    if (raw.data && typeof raw.data === 'object' && !Array.isArray(raw.data)) {
      source = raw.data;
    }
    if (raw.items && typeof raw.items === 'object' && !Array.isArray(raw.items)) {
      source = raw.items;
    }

    const maxLen = DANMAKU_DEFAULTS.maxContentLength;
    const normalized: DanmakuDataMap = {};

    for (const [sid, items] of Object.entries(source)) {
      if (typeof sid !== 'string' || !Array.isArray(items)) continue;
      const cleaned: DanmakuRawItem[] = [];
      for (const item of items) {
        if (!item || typeof item !== 'object') continue;
        const text = String(item.c ?? item.content ?? '').trim();
        const color = String(item.o ?? item.color ?? DANMAKU_DEFAULTS.defaultColor);
        if (!text) continue;
        if (!danmakuIsValidColor(color)) continue;
        cleaned.push({
          c: text.length > maxLen ? text.slice(0, maxLen) : text,
          o: color,
        });
      }
      if (cleaned.length) normalized[sid] = cleaned;
    }
    return normalized;
  }
}

export function updateConnectionStatus(
  status: 'idle' | 'loading' | 'ready' | 'error' | 'local',
  message?: string,
): void {
  const defaultMessages: Record<string, string> = {
    loading: '正在连接弹幕...',
    ready: '弹幕已连接',
    error: '弹幕服务暂时不可用',
    local: '弹幕服务端尚未配置',
    idle: '',
  };
  webgalStore.dispatch(
    setConnectionStatus({
      status,
      message: message ?? defaultMessages[status] ?? '',
    }),
  );
}
