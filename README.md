# RenPy / WebGAL 弹幕系统解决方案

为 Ren'Py 和 WebGAL 两款视觉小说引擎提供弹幕功能，支持滚动/列表两种显示模式，后端基于 WordPress REST API。

> 本次开发针对 **Ren'Py 8.5.0** / **WebGAL Terre 4.6.0**。其他版本可能需要调整代码。

## 项目结构

```
├── RenPy/                          # Ren'Py 引擎弹幕模块
│   ├── danmaku_system.rpy          #   单文件客户端（复制到 game/ 即可）
│   ├── SDLActivity.java.mod        #   安卓中文输入 + 高刷补丁（Ren'Py 8.5.0）
│   ├── README.md                   #   详细接入文档
│   ├── agent for install.md        #   AI 智能体接入指引
│   └── 安卓键盘补丁安装说明.md       #   安卓补丁安装步骤
│
├── WebGal/                         # WebGAL 引擎弹幕模块
│   ├── built/                      #   编译好的引擎文件（普通用户用）
│   ├── src/                        #   新增源码（开发者集成用）
│   ├── modified/                   #   需要替换的修改文件
│   ├── INSTALL.md                  #   普通用户安装指南（Terre 编辑器）
│   └── README.md                   #   开发者集成文档
│
├── Renpy-Webgal-Danmaku-WordPressPlugin.zip   # WordPress 弹幕后端插件
└── RenPyWebGal_DanmakuSolution0.01.zip        # 完整分发包
```

## 快速开始

### 后端（WordPress 插件）

1. 在 WordPress 后台上传 `Renpy-Webgal-Danmaku-WordPressPlugin.zip` 并启用
2. 在 `RenPy Danmaku` 菜单创建项目，获取 `API Base` 和 `Project Key`

### Ren'Py 接入

1. 复制 `RenPy/danmaku_system.rpy` 到游戏 `game/` 目录
2. 在 `script.rpy` 的 `label splashscreen` 中加入 `$ renpy_danmaku_prefetch()`
3. 在 `screens.rpy` 的 quick_menu 和 preferences 中加入开关/发送/设置控件
4. 安卓版需额外安装 `SDLActivity.java` 补丁

详细步骤见 [RenPy/README.md](RenPy/README.md)。

### WebGAL 接入

**普通用户（Terre 编辑器）：** 将 `WebGal/built/` 覆盖到 Terre 的模板目录即可，详见 [WebGal/INSTALL.md](WebGal/INSTALL.md)。

**开发者：** 将 `WebGal/src/` 复制到 WebGAL 源码，将 `WebGal/modified/` 替换对应文件，详见 [WebGal/README.md](WebGal/README.md)。

## 功能特性

- 滚动弹幕 / 列表弹幕两种显示模式
- 弹幕开关、发送弹幕、模式切换
- WordPress 多项目管理（独立 Project Key、审核策略、限流）
- 先审后发 / 直接公开两种审核策略
- 屏蔽词过滤
- 安卓中文输入支持

## 需要协助

按文档操作后仍有问题，或需要接入协助：

- QQ：519968509
- 同人游戏社团/组织可提供免费技术支持（在制作人员名单中署名即可）

## License

本项目基于 MIT 协议开源，详见 [LICENSE](LICENSE)。
