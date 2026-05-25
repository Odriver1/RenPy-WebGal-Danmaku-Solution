# WebGAL 弹幕系统 - 分发包

## 文件结构

```
danmaku-package/
├── built/                          ← 编译好的引擎文件（给普通用户，复制到 Terre 模板）
│   ├── index.html
│   └── assets/
├── src/                          ← 新增源码（复制到 WebGAL src/ 下对应位置）
│   ├── Core/Modules/danmaku/     ← 弹幕核心模块
│   ├── UI/Danmaku/               ← 弹幕 UI 组件
│   └── store/danmakuReducer.ts   ← 弹幕 Redux 状态
├── modified/                     ← 修改过的文件（替换 WebGAL 原文件）
│   ├── App.tsx
│   ├── vite.config.ts
│   ├── Core/
│   │   ├── initializeScript.ts
│   │   ├── webgalCore.ts
│   │   ├── gameScripts/say.ts
│   │   ├── controller/storage/storageController.ts
│   │   ├── util/coreInitialFunction/infoFetcher.ts
│   │   └── Modules/stage/
│   └── store/
│       ├── store.ts
│       ├── userDataInterface.ts
│       └── userDataReducer.ts
├── game/config.txt               ← 游戏配置模板（含弹幕参数）
├── README.md                     ← 开发者集成文档（本文件）
└── INSTALL.md                    ← 普通用户安装指南（安装到 Terre 编辑器）
```

## 开发者集成步骤

### 方式 A：直接替换文件（推荐）

适合 WebGAL 版本与当前包匹配的情况。

#### 1. 复制新增文件

将 `src/` 下的所有内容复制到 WebGAL 项目的 `packages/webgal/src/` 目录下，保持目录结构一致。

#### 2. 替换修改过的文件

将 `modified/` 下的文件替换 WebGAL 项目中对应位置的文件。

#### 3. 配置弹幕 API

编辑 `public/game/config.txt`，添加两行：

```
Danmaku_apiBase:https://你的服务器/wp-json/renpy-danmaku/v1;
Danmaku_projectKey:你的项目密钥;
```

#### 4. 构建

```bash
cd packages/parser && yarn build
cd ../webgal && npx vite build
```

---

### 方式 B：手动添加代码

适合 WebGAL 版本更新后、替换文件可能不兼容的情况。以下按文件列出每处改动的具体位置和代码。

---

#### 1. `vite.config.ts`

在 `defineConfig({...})` 对象中添加一行：

```ts
base: './',
```

---

#### 2. `store/userDataInterface.ts`

在 `IOptionData` 接口末尾添加三个字段（约第 49 行，`skipAll` 之后）：

```ts
danmakuEnabled: boolean;
danmakuStyle: 'scroll' | 'list';
danmakuVersion: number;
```

---

#### 3. `store/userDataReducer.ts`

在 `initialOptionSet` 对象末尾添加三个默认值（约第 38 行，`skipAll` 之后）：

```ts
danmakuEnabled: true,
danmakuStyle: 'scroll' as const,
danmakuVersion: 1 as const,
```

---

#### 4. `store/store.ts`

在文件顶部 `import savesReducer` 之后添加 import：

```ts
import danmakuReducer from '@/store/danmakuReducer';
```

在 `reducer` 对象中添加一行（约第 14 行，`saveData` 之后）：

```ts
danmaku: danmakuReducer,
```

---

#### 5. `Core/webgalCore.ts`

在 `import` 区域添加（约第 11 行，`stageStateManager` import 之后）：

```ts
import type { DanmakuCore } from '@/Core/Modules/danmaku/DanmakuCore';
```

在 `WebgalCore` 类中添加字段（约第 27 行，`styleObjects` 之后）：

```ts
public danmakuCore: DanmakuCore | null = null;
```

---

#### 6. `Core/Modules/stage/stageInterface.ts`

在 `IStageState` 接口中添加字段（约第 248 行，`currentConcatDialogPrev` 之后）：

```ts
danmakuSayId: string;
```

---

#### 7. `Core/Modules/stage/stageStateManager.ts`

在 `initState` 对象中添加初始值（约第 76 行，`currentConcatDialogPrev: ''` 之后）：

```ts
danmakuSayId: '',
```

---

#### 8. `Core/initializeScript.ts`

**8a.** 在 `import` 区域末尾（约第 18 行，`stageStateManager` import 之后）添加：

```ts
import { DanmakuCore } from '@/Core/Modules/danmaku/DanmakuCore';
import { webgalStore } from '@/store/store';
```

**8b.** 在 `initializeScript` 函数中，将：

```ts
infoFetcher('./game/config.txt');
```

改为：

```ts
infoFetcher('./game/config.txt').then(() => initDanmaku());
```

**8c.** 在文件末尾（`initializeScript` 函数闭合之后）添加整个函数：

```ts
function initDanmaku() {
  try {
    const state = webgalStore.getState().userData;
    const vars = state.globalGameVar;
    const apiBase = (vars.Danmaku_apiBase as string) ?? '';
    const projectKey = (vars.Danmaku_projectKey as string) ?? '';

    if (!apiBase || !projectKey) {
      logger.info('[Danmaku] 未配置 Danmaku_apiBase / Danmaku_projectKey，跳过初始化');
      return;
    }

    const danmakuCore = new DanmakuCore();
    danmakuCore.initialize(apiBase, projectKey);
    WebGAL.danmakuCore = danmakuCore;
    danmakuCore.fetchDanmakuData();
    logger.info('[Danmaku] 初始化完成');
  } catch (e) {
    logger.error('[Danmaku] 初始化失败:', e);
  }
}
```

---

---

#### 9. `Core/util/coreInitialFunction/infoFetcher.ts`

找到 `export const infoFetcher` 函数定义（约第 33 行），将函数改为返回 Promise：

```ts
export const infoFetcher = (url: string): Promise<void> => {
  const dispatch = webgalStore.dispatch;
  return axios.get(url).then(async (r) => {
    // ... 原有逻辑不变 ...
  });
};
```

> 改动要点：给函数加上 `: Promise<void>` 返回类型，用 `return` 返回 axios 的 promise chain。这样 `initializeScript.ts` 才能用 `.then()` 链式调用 `initDanmaku()`。

---

#### 10. `Core/controller/storage/storageController.ts`

在 `normalizeUserData` 函数的 `optionData: { ...defaultUserData.optionData, ...optionData }` 处（约第 47 行），将简单的展开改为带版本迁移的逻辑：

```ts
optionData: {
  ...defaultUserData.optionData,
  ...optionData,
  // danmakuVersion < 1 时强制使用新默认值 danmakuEnabled: true
  danmakuEnabled: ((optionData.danmakuVersion as number) ?? 0) < 1
    ? defaultUserData.optionData.danmakuEnabled
    : (optionData.danmakuEnabled as boolean),
},
```

> 原因：用户设备上的 IndexedDB 可能存了旧版 `danmakuEnabled: false`。通过版本号迁移，首次安装或升级时自动启用弹幕。

---

#### 11. `Core/gameScripts/say.ts`

在 `stageStateManager.setStage('currentDialogKey', dialogKey);` 之后（原版约第 54 行）添加：

```ts
// 设置弹幕sayId（场景名_行号）
const danmakuSayId = `${WebGAL.sceneManager.sceneData.currentScene.sceneName}_${WebGAL.sceneManager.sceneData.currentSentenceId}`;
stageStateManager.setStage('danmakuSayId', danmakuSayId);
```

---

#### 12. `App.tsx`

**12a.** 在 `import` 区域末尾添加：

```ts
import { DanmakuDisplay } from '@/UI/Danmaku/DanmakuDisplay';
import { DanmakuInputModal } from '@/UI/Danmaku/DanmakuInputModal';
```

**12b.** 在 `App` 函数体内第一行（约第 21 行，`useEffect` 之前）添加：

```ts
const danmakuState = useSelector((state: RootState) => state.danmaku);
```

**12c.** 在 JSX 中（`<DevPanel />` 之后、`</div>` 闭合之前）添加：

```tsx
<DanmakuDisplay />
<div id="danmaku-modal-portal" />
{danmakuState.inputModalVisible && <DanmakuInputModal />}
{danmakuState.connectionStatus !== 'idle' && (
  <div style={{
    position: 'fixed', top: 10, right: 10, zIndex: 14,
    fontSize: 12, padding: '2px 8px', borderRadius: 4,
    background: danmakuState.connectionStatus === 'ready' ? 'rgba(0,200,0,0.7)' : 'rgba(200,200,0,0.7)',
    color: '#fff', pointerEvents: 'none',
  }}>
    {danmakuState.connectionStatus === 'ready' ? '弹幕已连接' : danmakuState.connectionMessage}
  </div>
)}
```

---

#### 13. `UI/BottomControlPanel/BottomControlPanel.tsx`

**13a.** 在 `import` 区域末尾添加：

```ts
import { setInputModalVisible } from '@/store/danmakuReducer';
import { webgalStore } from '@/store/store';
import { WebGAL } from '@/Core/WebGAL';
```

**11b.** 在 `BottomControlPanel` 函数体内，`useDispatch()` 之后添加 danmaku 状态读取（约第 57 行之后）：

```ts
const danmakuState = useSelector((state: RootState) => state.danmaku);
const userData = useSelector((state: RootState) => state.userData);

const toggleDanmaku = () => {
  if (WebGAL.danmakuCore) {
    WebGAL.danmakuCore.enabled = !WebGAL.danmakuCore.enabled;
  }
  dispatch(setOptionData({ key: 'danmakuEnabled', value: !userData.optionData.danmakuEnabled }));
};

const toggleDanmakuStyle = () => {
  if (WebGAL.danmakuCore) {
    WebGAL.danmakuCore.displayStyle = WebGAL.danmakuCore.displayStyle === 'scroll' ? 'list' : 'scroll';
  }
  const newStyle = userData.optionData.danmakuStyle === 'scroll' ? 'list' : 'scroll';
  dispatch(setOptionData({ key: 'danmakuStyle', value: newStyle }));
};
```

**11c.** 在按钮区域（`读档` 按钮之后、`选项` 按钮之前，约第 286 行）添加三个按钮：

```tsx
{/* 弹幕开关 */}
<span
  className={styles.singleButton}
  style={{ fontSize }}
  onClick={() => { toggleDanmaku(); playSeClick(); }}
  onMouseEnter={playSeEnter}
>
  <span className={styles.button} style={{ fontSize: '120%' }}>
    {userData.optionData.danmakuEnabled ? '弹' : '✕'}
  </span>
  <span className={styles.button_text}>
    {userData.optionData.danmakuEnabled ? '弹幕-开' : '弹幕-关'}
  </span>
</span>
{/* 弹幕模式切换 */}
{userData.optionData.danmakuEnabled && (
  <span
    className={styles.singleButton}
    style={{ fontSize }}
    onClick={() => { toggleDanmakuStyle(); playSeClick(); }}
    onMouseEnter={playSeEnter}
  >
    <span className={styles.button} style={{ fontSize: '120%' }}>
      {userData.optionData.danmakuStyle === 'scroll' ? '滚' : '列'}
    </span>
    <span className={styles.button_text}>模式</span>
  </span>
)}
{/* 发弹幕 */}
{userData.optionData.danmakuEnabled && (
  <span
    className={styles.singleButton}
    style={{ fontSize }}
    onClick={() => { dispatch(setInputModalVisible(true)); playSeClick(); }}
    onMouseEnter={playSeEnter}
  >
    <span className={styles.button} style={{ fontSize: '120%' }}>✎</span>
    <span className={styles.button_text}>发弹幕</span>
  </span>
)}
```

> 注意：如果原来的 `BottomControlPanel.tsx` 还没有导入 `useSelector`，需要在 `import { useDispatch } from 'react-redux'` 处改为 `import { useDispatch, useSelector } from 'react-redux'`。

---

### 依赖关系一览

| 文件 | 改动量 | 修改内容 |
|------|--------|----------|
| `vite.config.ts` | 1 行 | `base: './'` 相对路径 |
| `store/userDataInterface.ts` | 3 行 | IOptionData 添加弹幕字段 + danmakuVersion |
| `store/userDataReducer.ts` | 3 行 | 弹幕默认值 + danmakuVersion |
| `store/store.ts` | 2 行 | 注册 danmaku reducer |
| `Core/webgalCore.ts` | 2 行 | WebgalCore 添加 danmakuCore 字段 |
| `Core/Modules/stage/stageInterface.ts` | 1 行 | IStageState 添加 danmakuSayId |
| `Core/Modules/stage/stageStateManager.ts` | 1 行 | initState 添加 danmakuSayId |
| `Core/initializeScript.ts` | ~30 行 | initDanmaku 初始化函数（链式调用 infoFetcher） |
| `Core/util/coreInitialFunction/infoFetcher.ts` | ~3 行 | 返回 Promise 以支持链式调用 |
| `Core/controller/storage/storageController.ts` | ~8 行 | danmakuVersion 迁移，强制新默认值 |
| `Core/gameScripts/say.ts` | 3 行 | 生成 danmakuSayId |
| `App.tsx` | ~15 行 | 渲染 DanmakuDisplay + DanmakuInputModal + 状态指示器 |
| `UI/BottomControlPanel/BottomControlPanel.tsx` | ~40 行 | 弹幕开关/模式/发送按钮 |
