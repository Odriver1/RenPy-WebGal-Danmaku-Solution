import React, { useState, useCallback } from 'react';
import ReactDOM from 'react-dom';
import { useDispatch } from 'react-redux';
import { setInputModalVisible } from '@/store/danmakuReducer';
import { useStageState } from '@/hooks/useStageState';
import { WebGAL } from '@/Core/WebGAL';
import { DANMAKU_COLOR_PRESETS, DANMAKU_DEFAULTS } from '@/Core/Modules/danmaku';
import styles from './danmaku.module.scss';

export const DanmakuInputModal: React.FC = () => {
  const dispatch = useDispatch();
  const stageState = useStageState();
  const [text, setText] = useState('');
  const [color, setColor] = useState<string>(DANMAKU_DEFAULTS.defaultColor);

  const handleSubmit = useCallback(() => {
    const trimmed = text.trim();
    if (!trimmed) return;
    const sayId = stageState.danmakuSayId;
    if (!sayId) return;

    WebGAL.danmakuCore?.sendDanmaku(sayId, trimmed, color);
    dispatch(setInputModalVisible(false));
    setText('');
  }, [text, color, stageState.danmakuSayId, dispatch]);

  const handleClose = useCallback(() => {
    dispatch(setInputModalVisible(false));
  }, [dispatch]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter') handleSubmit();
      if (e.key === 'Escape') handleClose();
    },
    [handleSubmit, handleClose],
  );

  return ReactDOM.createPortal(
    <div className={styles.modalOverlay} onClick={handleClose}>
      <div className={styles.modalPanel} onClick={(e) => e.stopPropagation()}>
        <div className={styles.modalTitle}>
          <h3>发送弹幕</h3>
          <button className={styles.closeBtn} onClick={handleClose}>
            ×
          </button>
        </div>

        <div className={styles.inputRow}>
          <input
            className={styles.textInput}
            type="text"
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={`最多${DANMAKU_DEFAULTS.maxContentLength}字`}
            maxLength={DANMAKU_DEFAULTS.maxContentLength}
            autoFocus
          />
          <button className={styles.sendBtn} onClick={handleSubmit} disabled={!text.trim()}>
            发送
          </button>
        </div>

        <div className={styles.colorRow}>
          {DANMAKU_COLOR_PRESETS.map((preset) => (
            <button
              key={preset.value}
              className={`${styles.colorBtn} ${color === preset.value ? styles.selected : ''}`}
              style={{ background: preset.value }}
              onClick={() => setColor(preset.value)}
              title={preset.name}
            />
          ))}
        </div>

        <p className={styles.disclaimer}>弹幕可能需要审核后才会向其他玩家展示</p>
      </div>
    </div>,
    document.querySelector('#html-body__danmaku-modal')!,
  );
};
