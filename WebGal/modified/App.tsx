import { useEffect } from 'react';
import { useSelector } from 'react-redux';
import { initializeScript } from '@/Core/initializeScript';
import Translation from '@/UI/Translation/Translation';
import { Stage } from '@/Stage/Stage';
import { BottomControlPanel } from '@/UI/BottomControlPanel/BottomControlPanel';
import { BottomControlPanelFilm } from '@/UI/BottomControlPanel/BottomControlPanelFilm';
import { Backlog } from '@/UI/Backlog/Backlog';
import Title from '@/UI/Title/Title';
import Logo from '@/UI/Logo/Logo';
import { Extra } from '@/UI/Extra/Extra';
import Menu from '@/UI/Menu/Menu';
import GlobalDialog from '@/UI/GlobalDialog/GlobalDialog';
import PanicOverlay from '@/UI/PanicOverlay/PanicOverlay';
import DevPanel from '@/UI/DevPanel/DevPanel';
import { DanmakuDisplay } from '@/UI/Danmaku/DanmakuDisplay';
import { DanmakuInputModal } from '@/UI/Danmaku/DanmakuInputModal';
import { RootState } from '@/store/store';

export default function App() {
  const danmakuState = useSelector((state: RootState) => state.danmaku);

  useEffect(() => {
    initializeScript();
  }, []);
  return (
    <div className="App">
      <Translation />
      <Stage />
      <BottomControlPanel />
      <BottomControlPanelFilm />
      <Backlog />
      <Title />
      <Logo />
      <Extra />
      <Menu />
      <GlobalDialog />
      <PanicOverlay />
      <DevPanel />
      <DanmakuDisplay />
      {danmakuState.inputModalVisible && <DanmakuInputModal />}
      {danmakuState.connectionStatus !== 'disconnected' && (
        <div style={{
          position: 'fixed', top: 10, right: 10, zIndex: 14,
          fontSize: 12, padding: '2px 8px', borderRadius: 4,
          background: danmakuState.connectionStatus === 'connected' ? 'rgba(0,200,0,0.7)' : 'rgba(200,200,0,0.7)',
          color: '#fff', pointerEvents: 'none',
        }}>
          {danmakuState.connectionStatus === 'connected' ? '弹幕已连接' : danmakuState.connectionMessage}
        </div>
      )}
    </div>
  );
}
