import { configureStore, getDefaultMiddleware } from '@reduxjs/toolkit';
import GUIReducer from '@/store/GUIReducer';
import userDataReducer from '@/store/userDataReducer';
import savesReducer from '@/store/savesReducer';
import danmakuReducer from '@/store/danmakuReducer';

/**
 * WebGAL 全局状态管理
 */
export const webgalStore = configureStore({
  reducer: {
    GUI: GUIReducer,
    userData: userDataReducer,
    saveData: savesReducer,
    danmaku: danmakuReducer,
  },
  middleware: getDefaultMiddleware({
    serializableCheck: false,
  }),
  devTools: process.env.NODE_ENV !== 'production',
});

// 在 TS 中的类型声明
export type RootState = ReturnType<typeof webgalStore.getState>;
