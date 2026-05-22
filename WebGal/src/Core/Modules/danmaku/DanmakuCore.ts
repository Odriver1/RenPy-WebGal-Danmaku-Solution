import { DanmakuManager } from './DanmakuManager';
import { DanmakuApi, DanmakuDataMap, updateConnectionStatus } from './DanmakuApi';
import { danmakuIsValidColor, DANMAKU_DEFAULTS } from './DanmakuConfig';
import { stageStateManager } from '@/Core/Modules/stage/stageStateManager';
import { webgalStore } from '@/store/store';
import { DanmakuConnectionStatus } from '@/store/danmakuReducer';

export class DanmakuCore {
  manager!: DanmakuManager;
  api!: DanmakuApi;

  /** Design resolution — used by the React renderer for coordinate mapping */
  stageWidth = 1600;
  stageHeight = 900;

  private danmakuData: DanmakuDataMap = {};
  private lastTickTime = 0;
  private unsubStage: (() => void) | null = null;
  private isInitialized = false;
  private apiBase = '';
  private projectKey = '';
  private _enabled = true;
  private _style: 'scroll' | 'list' = 'list';
  private isMobile = false;

  get enabled(): boolean {
    return this._enabled;
  }
  set enabled(v: boolean) {
    this._enabled = v;
  }

  get displayStyle(): 'scroll' | 'list' {
    return this._style;
  }
  set displayStyle(v: 'scroll' | 'list') {
    this._style = v;
    if (this.manager) this.manager.currentStyle = v;
  }

  initialize(apiBase: string, projectKey: string, stageWidth?: number, stageHeight?: number): void {
    if (this.isInitialized) return;
    this.isInitialized = true;

    this.apiBase = apiBase;
    this.projectKey = projectKey;

    // Detect mobile
    this.isMobile =
      (typeof window !== 'undefined' && 'ontouchstart' in window && window.innerWidth < 768) ||
      (typeof navigator !== 'undefined' && navigator.maxTouchPoints > 1);

    // Canvas dimensions
    this.stageWidth = stageWidth ?? 1600;
    this.stageHeight = stageHeight ?? 900;

    this.manager = new DanmakuManager(this.stageWidth, this.stageHeight, this.isMobile);

    // Load persisted user settings
    const userData = webgalStore.getState().userData;
    this._enabled = userData.optionData.danmakuEnabled ?? true;
    this._style = userData.optionData.danmakuStyle ?? 'list';
    this.manager.currentStyle = this._style;

    // Init API
    this.api = new DanmakuApi(apiBase, projectKey);

    // Subscribe to stage state for dialogue line changes
    this.unsubStage = stageStateManager.subscribe((stageState) => {
      if (!this._enabled) return;
      this.manager.checkNewLine(stageState.danmakuSayId, this.danmakuData);
    });

    console.log('[Danmaku] Initialized (DOM render mode):', {
      stageWidth: this.stageWidth, stageHeight: this.stageHeight,
      isMobile: this.isMobile, scale: this.manager.scale,
      numLanes: this.manager.numLanes, enabled: this._enabled, style: this._style,
    });
  }

  destroy(): void {
    if (this.unsubStage) {
      this.unsubStage();
      this.unsubStage = null;
    }
    this.isInitialized = false;
  }

  async fetchDanmakuData(): Promise<void> {
    if (!this.apiBase || !this.projectKey) {
      updateConnectionStatus('local');
      return;
    }
    updateConnectionStatus('loading');
    try {
      const data = await this.api.fetchAll();
      Object.assign(this.danmakuData, data);
      updateConnectionStatus('ready');
    } catch {
      updateConnectionStatus('error');
    }
  }

  async sendDanmaku(sayId: string, content: string, color: string): Promise<void> {
    const maxLen = DANMAKU_DEFAULTS.maxContentLength;
    const text = content.trim().slice(0, maxLen);
    if (!text || !sayId) return;

    const validColor = danmakuIsValidColor(color) ? color : DANMAKU_DEFAULTS.defaultColor;

    // Optimistic local add
    this.manager.addSingle(text, validColor, this._style, performance.now() / 1000);
    if (!this.danmakuData[sayId]) this.danmakuData[sayId] = [];
    this.danmakuData[sayId].push({ c: text, o: validColor });

    // Submit to server
    try {
      await this.api.submit(sayId, text, validColor);
    } catch (e: any) {
      console.warn('[Danmaku] submit failed:', e.message);
    }
  }

  setConnectionStatus(status: DanmakuConnectionStatus, message?: string): void {
    updateConnectionStatus(status, message);
  }

  /**
   * Called each animation frame by the React renderer.
   * Handles timing, cleanup, and queue processing.
   * Does NOT do any rendering — the React component reads manager.active directly.
   */
  tick(now: number, dt: number): void {
    // Tab sleep recovery: clear all if >30s gap
    if (this.lastTickTime > 0 && now - this.lastTickTime > 30) {
      this.manager.active = [];
      this.manager.laneFreeAt = new Array(this.manager.numLanes).fill(0);
      this.manager.lastSayId = '';
      this.manager.pendingQueue = [];
    }

    this.lastTickTime = now;

    this.manager.cleanup(now);
    if (this._enabled) {
      this.manager.update(now);
    }
  }
}
