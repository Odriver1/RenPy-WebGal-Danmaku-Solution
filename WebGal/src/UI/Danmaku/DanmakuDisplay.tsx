import React, { FC, useEffect, useRef } from 'react';
import { WebGAL } from '@/Core/WebGAL';
import { DanmakuItem } from '@/Core/Modules/danmaku/DanmakuManager';

interface ItemDom {
  div: HTMLDivElement;
  itemId: number;
}

export const DanmakuDisplay: FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const itemDoms = useRef<Map<number, ItemDom>>(new Map());
  const lastTimeRef = useRef<number>(0);
  const rafRef = useRef<number>(0);

  useEffect(() => {
    const loop = (timestamp: number) => {
      const core = WebGAL.danmakuCore;
      if (!core) {
        rafRef.current = requestAnimationFrame(loop);
        return;
      }

      const now = timestamp / 1000;
      if (lastTimeRef.current === 0) lastTimeRef.current = now;
      const dt = Math.min(now - lastTimeRef.current, 0.1);
      lastTimeRef.current = now;

      core.tick(now, dt);

      const container = containerRef.current;
      if (!container) {
        rafRef.current = requestAnimationFrame(loop);
        return;
      }

      const active = core.manager.active;
      const mgr = core.manager;
      const activeIds = new Set<number>();
      const sx = container.clientWidth / core.stageWidth;
      const sy = container.clientHeight / core.stageHeight;

      for (let i = 0; i < active.length; i++) {
        const item = active[i];
        activeIds.add(item.id);

        let entry = itemDoms.current.get(item.id);
        if (!entry) {
          const div = document.createElement('div');
          div.style.cssText =
            'position:absolute;white-space:pre-wrap;pointer-events:none;' +
            'will-change:transform,opacity;font-family:OPPOSans-R,Arial,sans-serif;' +
            'text-shadow:0 0 3px #fff,0 0 3px #fff,1px 1px 2px #000;';
          div.textContent = item.text;
          container.appendChild(div);
          entry = { div, itemId: item.id };
          itemDoms.current.set(item.id, entry);
        }

        const div = entry.div;
        const elapsed = now - item.startTime;
        const fontSize = mgr.getFontSize(item.style);

        div.style.fontSize = `${fontSize * sy}px`;
        div.style.color = item.color;

        if (item.style === 'scroll') {
          const x = core.stageWidth * (1.0 - (elapsed / item.duration) * mgr.SCROLL_TRAVEL_FACTOR);
          const y = (item.lane ?? 0) * mgr.laneSpacing + mgr.laneTop;
          div.style.transform = `translate(${x * sx}px, ${y * sy}px)`;
          div.style.opacity = '1';
        } else {
          const targetY = item.targetY ?? mgr.listStartY;
          if (item.y === undefined) item.y = mgr.listStartY;
          item.y += (targetY - item.y) * (1.0 - Math.exp(-15.0 * dt));

          let x: number;
          if (elapsed < mgr.listSlideInTime) {
            const sp = elapsed / mgr.listSlideInTime;
            const ease = 1.0 - (1.0 - sp) ** 3;
            x = mgr.listSlideFromX + (mgr.listFinalX - mgr.listSlideFromX) * ease;
          } else {
            x = mgr.listFinalX;
          }

          let alpha = 1.0;
          if (elapsed < mgr.listSlideInTime) {
            alpha = elapsed / mgr.listSlideInTime;
          } else if (
            mgr.LIST_FADE_OUT_TIME > 0 &&
            item.duration - elapsed < mgr.LIST_FADE_OUT_TIME
          ) {
            alpha = (item.duration - elapsed) / mgr.LIST_FADE_OUT_TIME;
          }

          div.style.transform = `translate(${x * sx}px, ${item.y * sy}px)`;
          div.style.opacity = String(Math.max(0, Math.min(1, alpha)));
        }
      }

      // Remove stale elements
      for (const [id, entry] of itemDoms.current) {
        if (!activeIds.has(id)) {
          entry.div.remove();
          itemDoms.current.delete(id);
        }
      }

      rafRef.current = requestAnimationFrame(loop);
    };

    rafRef.current = requestAnimationFrame(loop);

    return () => {
      cancelAnimationFrame(rafRef.current);
      for (const [, entry] of itemDoms.current) {
        entry.div.remove();
      }
      itemDoms.current.clear();
    };
  }, []);

  return (
    <div
      ref={containerRef}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
        zIndex: 20,
        overflow: 'hidden',
      }}
    />
  );
};
