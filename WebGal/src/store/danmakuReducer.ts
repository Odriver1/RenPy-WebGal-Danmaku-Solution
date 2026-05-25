import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export type DanmakuConnectionStatus = 'idle' | 'loading' | 'ready' | 'error' | 'local';

export interface DanmakuState {
  inputModalVisible: boolean;
  connectionStatus: DanmakuConnectionStatus;
  connectionMessage: string;
}

const initState: DanmakuState = {
  inputModalVisible: false,
  connectionStatus: 'idle',
  connectionMessage: '',
};

const danmakuSlice = createSlice({
  name: 'danmaku',
  initialState: initState,
  reducers: {
    setInputModalVisible: (state, action: PayloadAction<boolean>) => {
      state.inputModalVisible = action.payload;
    },
    setConnectionStatus: (
      state,
      action: PayloadAction<{ status: DanmakuConnectionStatus; message?: string }>,
    ) => {
      state.connectionStatus = action.payload.status;
      state.connectionMessage = action.payload.message ?? '';
    },
    resetDanmakuState: () => initState,
  },
});

export const { setInputModalVisible, setConnectionStatus, resetDanmakuState } = danmakuSlice.actions;
export default danmakuSlice.reducer;
