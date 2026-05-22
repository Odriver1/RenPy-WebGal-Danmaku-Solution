# WebGAL 弹幕系统 - 安装指南

本指南面向**普通用户**，帮助你将弹幕功能安装到 **WebGAL Terre 编辑器** 中。安装后，你用编辑器导出的所有游戏都会自带弹幕功能。

---

## 第一步：关闭编辑器

在操作之前，请先关闭 WebGAL Terre 编辑器。

---

## 第二步：找到模板目录

打开 WebGAL Terre 编辑器的安装目录（就是 `WebGAL_Terre.exe` 所在的文件夹），然后进入：

```
assets\templates\WebGAL_Template\
```

该目录的结构如下：

```
WebGAL_Template\
├── assets\          ← 引擎文件（JS、CSS等）
├── game\            ← 游戏数据（config.txt、场景等）
├── icons\
├── index.html       ← 入口页面
└── ...
```

---

## 第三步：替换引擎文件

将 `danmaku-package\built\` 目录下的所有内容复制到 `WebGAL_Template\` 目录中，**覆盖同名文件**：

| 源文件（built\） | 目标位置（WebGAL_Template\） |
|------|------|
| `built\index.html` | `index.html` |
| `built\assets\index-*.js` | `assets\` 下的同名文件 |
| `built\assets\index-*.css` | `assets\` 下的同名文件 |
| `built\assets\initRegister-*.js` | `assets\` 下的同名文件 |
| `built\assets\*.gz` | `assets\` 下的同名文件 |

> 直接将 `built\` 文件夹拖入 `WebGAL_Template\` 即可，Windows 会自动合并同名文件夹。

---

## 第四步：配置弹幕服务器（每个游戏单独操作）

1. 打开 WebGAL Terre 编辑器
2. 在游戏卡片上点击**选项按钮** → 选择「**在文件管理器中打开**」
3. 在打开的目录中找到 `game\config.txt`，用记事本打开
4. 在文件末尾添加两行：

```
Danmaku_apiBase:https://你的服务器地址/wp-json/renpy-danmaku/v1;
Danmaku_projectKey:你的项目密钥;
```

**参数说明：**
- `Danmaku_apiBase`：弹幕 API 服务器地址
- `Danmaku_projectKey`：项目密钥，用于区分不同游戏的弹幕数据

> 如果留空，弹幕功能不会启用。每个游戏需要单独配置一次。

---

## 使用说明

在游戏预览或导出后的游戏页面，底部的控制面板会出现三个弹幕按钮：

| 按钮 | 功能 |
|------|------|
| **弹幕-开 / 弹幕-关** | 切换弹幕显示开关（默认开启） |
| **模式** | 切换弹幕模式（滚动 / 列表） |
| **发弹幕** | 打开发送弹幕对话框 |

---

## 常见问题

**Q: 编辑器显示异常或白屏？**
A: 可能是文件替换不完整，请确认 `index.html` 和 `assets\` 目录下的所有 JS/CSS 文件都已替换。

**Q: 弹幕显示「未连接」？**
A: 检查 `config.txt` 中的服务器地址和项目密钥是否正确。如果未配置，弹幕按钮不会出现。

**Q: 发送弹幕失败？**
A: 确认 API 服务器可访问，且项目密钥正确。可打开浏览器开发者工具（F12）查看控制台错误信息。

**Q: 想还原到原始版本怎么办？**
A: 操作前建议备份 `WebGAL_Template\` 目录下的 `index.html` 和 `assets\` 文件夹，需要还原时覆盖回去即可。
