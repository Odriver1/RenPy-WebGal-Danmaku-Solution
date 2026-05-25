/**
 * Pure logic port of Ren'Py RenPyDanmakuManager.
 * Handles lane allocation, timing, queue management, and text wrapping.
 * No I/O, no rendering — completely independent of Pixi/React.
 */
let _danmakuIdCounter = 0;

interface DanmakuItem {
  id: number;
  text: string;
  color: string;
  startTime: number;
  duration: number;
  style: 'scroll' | 'list';
  lane?: number;
  y?: number;
  targetY?: number;
  height?: number;
}

interface PendingItem {
  text: string;
  color: string;
  popTime: number;
  height: number;
}

interface DanmakuRawItem {
  c: string; // content
  o: string; // color
}

export class DanmakuManager {
  readonly MAX_PER_LINE = 6;
  readonly MAX_ACTIVE = 30;

  readonly SCROLL_DURATION_BASE = 12.0;
  readonly SCROLL_DURATION_STEP = 0.8;
  readonly SCROLL_DURATION_VARIANTS = 5;
  readonly SCROLL_SINGLE_DURATION = 13.0;
  readonly SCROLL_LANE_HOLD_TIME = 4.5;
  readonly SCROLL_TRAVEL_FACTOR = 1.5;

  readonly LIST_DURATION = 10.0;
  readonly LIST_FADE_OUT_TIME = 0.5;

  readonly numLanes: number;
  readonly scrollFontSize: number;
  readonly laneSpacing: number;
  readonly laneTop: number;

  readonly listFontSize: number;
  readonly listStartY: number;
  readonly listSlideInTime: number;
  readonly listSlideFromX: number;
  readonly listFinalX: number;

  readonly scrollOutlineWidth: number;
  readonly listOutlineWidth: number;

  readonly listLineHeight: number;
  readonly listItemPadding: number;
  readonly listStackGap: number;

  readonly scale: number;
  readonly isMobile: boolean;

  active: DanmakuItem[] = [];
  laneFreeAt: number[] = [];
  lastSayId = '';
  pendingQueue: PendingItem[] = [];
  currentStyle: 'scroll' | 'list' = 'list';

  constructor(canvasWidth: number, canvasHeight: number, isMobile: boolean) {
    this.isMobile = isMobile;
    this.scale = Math.max(0.5, Math.min(2.0, canvasHeight / 1080));

    // Scroll mode params
    this.numLanes = isMobile ? 8 : 15;
    this.scrollFontSize = Math.round((isMobile ? 54 : 45) * this.scale);
    const laneSpacingRatio = isMobile ? 1.33 : 1.15;
    this.laneSpacing = Math.round(this.scrollFontSize * laneSpacingRatio);
    this.laneTop = Math.round(20 * this.scale);
    this.scrollOutlineWidth = Math.max(1, Math.round(1 * this.scale));

    // List mode params
    this.listFontSize = Math.round((isMobile ? 41 : 34) * this.scale);
    const lineHeightRatio = 1.22;
    const itemPaddingRatio = 0.20;
    const stackGapRatio = 0.10;
    this.listLineHeight = Math.round(this.listFontSize * lineHeightRatio);
    this.listItemPadding = Math.max(6, Math.round(this.listFontSize * itemPaddingRatio));
    this.listStackGap = Math.max(2, Math.round(this.listFontSize * stackGapRatio));
    this.listStartY = Math.round((isMobile ? 600 : 720) * this.scale);
    this.listSlideInTime = isMobile ? 0.30 : 0.36;
    this.listSlideFromX = Math.round(-300 * this.scale);
    this.listFinalX = Math.round((isMobile ? 60 : 40) * this.scale);
    this.listOutlineWidth = Math.max(1, Math.round((isMobile ? 2 : 1) * this.scale));

    this.laneFreeAt = new Array(this.numLanes).fill(0);
  }

  getFontSize(style: 'scroll' | 'list'): number {
    return style === 'scroll' ? this.scrollFontSize : this.listFontSize;
  }

  wrapText(text: string, maxChars = 15): string {
    if (text.length <= maxChars) return text;
    const lines: string[] = [];
    let remaining = text;
    while (remaining) {
      lines.push(remaining.slice(0, maxChars));
      remaining = remaining.slice(maxChars);
    }
    return lines.join('\n');
  }

  calcListItemHeight(text: string): number {
    const numLines = text.split('\n').length;
    return numLines * this.listLineHeight + this.listItemPadding;
  }

  private getPushDistance(newItemH: number): number {
    let bottomItemH = newItemH;
    let bottomY = -Infinity;
    for (const item of this.active) {
      if (item.style === 'list' && (item.targetY ?? 0) > bottomY) {
        bottomY = item.targetY ?? 0;
        bottomItemH = item.height ?? newItemH;
      }
    }
    return bottomItemH + this.listStackGap;
  }

  private pushExistingListItems(newItemH: number): void {
    const pushH = this.getPushDistance(newItemH);
    for (const item of this.active) {
      if (item.style === 'list') {
        item.targetY = (item.targetY ?? this.listStartY) - pushH;
      }
    }
  }

  checkNewLine(sayId: string, danmakuData: Record<string, DanmakuRawItem[]>): void {
    if (!sayId || sayId === this.lastSayId) return;
    this.lastSayId = sayId;

    if (this.active.length + this.pendingQueue.length >= this.MAX_ACTIVE) return;

    const items = danmakuData[sayId];
    if (items?.length) {
      this.addBatch(items, this.currentStyle, performance.now() / 1000);
    }
  }

  addBatch(items: DanmakuRawItem[], style: 'scroll' | 'list', now: number): void {
    if (style === 'list') {
      let batchItems = items;
      if (batchItems.length > 7) {
        batchItems = shuffleArray([...batchItems]).slice(0, 7);
      }
      let startTime = now + 2.0;
      if (this.pendingQueue.length > 0) {
        startTime = Math.max(startTime, this.pendingQueue[this.pendingQueue.length - 1].popTime + 0.3);
      }
      for (let i = 0; i < batchItems.length; i++) {
        const wrapped = this.wrapText(batchItems[i].c);
        const h = this.calcListItemHeight(wrapped);
        this.pendingQueue.push({
          text: wrapped,
          color: batchItems[i].o,
          popTime: startTime + i * 0.3,
          height: h,
        });
      }
    } else {
      const remaining = this.MAX_ACTIVE - this.active.length;
      const count = Math.min(this.MAX_PER_LINE, remaining);
      if (count <= 0) return;
      for (let i = 0; i < Math.min(items.length, count); i++) {
        const lane = this.findFreeLane(now + i * 0.3);
        const duration =
          this.SCROLL_DURATION_BASE + (i % this.SCROLL_DURATION_VARIANTS) * this.SCROLL_DURATION_STEP;
        const start = now + i * 0.3;
        this.active.push({
          id: ++_danmakuIdCounter,
          text: items[i].c,
          color: items[i].o,
          lane,
          startTime: start,
          duration,
          style: 'scroll',
        });
        this.laneFreeAt[lane] = start + this.SCROLL_LANE_HOLD_TIME;
      }
    }
  }

  addSingle(text: string, color: string, style: 'scroll' | 'list', now: number): void {
    if (style === 'list') {
      const wrapped = this.wrapText(text);
      const itemH = this.calcListItemHeight(wrapped);
      this.pushExistingListItems(itemH);
      this.active.push({
        id: ++_danmakuIdCounter,
        text: wrapped,
        color,
        startTime: now,
        duration: this.LIST_DURATION,
        style: 'list',
        y: this.listStartY,
        targetY: this.listStartY,
        height: itemH,
      });
    } else {
      const lane = this.findFreeLane(now);
      this.active.push({
        id: ++_danmakuIdCounter,
        text,
        color,
        lane,
        startTime: now,
        duration: this.SCROLL_SINGLE_DURATION,
        style: 'scroll',
      });
      this.laneFreeAt[lane] = now + this.SCROLL_LANE_HOLD_TIME;
    }
  }

  update(now: number): void {
    while (this.pendingQueue.length > 0 && now >= this.pendingQueue[0].popTime) {
      const item = this.pendingQueue.shift()!;
      const h = item.height;
      this.pushExistingListItems(h);
      this.active.push({
        id: ++_danmakuIdCounter,
        text: item.text,
        color: item.color,
        startTime: now,
        duration: this.LIST_DURATION,
        style: 'list',
        y: this.listStartY,
        targetY: this.listStartY,
        height: h,
      });
    }
  }

  cleanup(now: number): void {
    this.active = this.active.filter((item) => now - item.startTime < item.duration);
  }

  findFreeLane(atTime: number): number {
    for (let i = 0; i < this.numLanes; i++) {
      if (this.laneFreeAt[i] <= atTime) return i;
    }
    let best = 0;
    for (let i = 1; i < this.numLanes; i++) {
      if (this.laneFreeAt[i] < this.laneFreeAt[best]) best = i;
    }
    return best;
  }
}

function shuffleArray<T>(arr: T[]): T[] {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}

export type { DanmakuItem, PendingItem, DanmakuRawItem };
