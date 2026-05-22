# 用户项目安装智能体指南

这份文档是给“用户自己的 AI/编程智能体”看的。你的任务只有一个：把分发包里的 Ren'Py 弹幕系统接入用户自己的 Ren'Py 游戏。

## 你会拿到的文件

用户提供的分发包根目录应包含：

- `danmaku_system.rpy`：Ren'Py 弹幕客户端模块。
- `Renpy-Danmaku-WordPressPlugin.zip`：WordPress 弹幕插件安装包。
- `SDLActivity.java.mod`：Android 中文输入与高刷新率补丁参考文件。
- `README.md` 和其他说明文档。

只按这些根目录文件工作。不要寻找或假设还有额外源码目录。

## 安装前确认

1. 先提醒用户备份自己的 Ren'Py 游戏项目。
2. 让用户提供自己的 `game/screens.rpy` 和 `game/script.rpy`，或提供其中需要合并的相关片段。
3. 让用户提供 WordPress 插件后台复制出的 `API Base` 和 `Project Key`。
4. 不要读取或上传用户没有主动提供的文件。

## Ren'Py 客户端接入

1. 将分发包根目录的 `danmaku_system.rpy` 复制到用户游戏的 `game/` 目录。
2. 修改用户游戏里的 `game/danmaku_system.rpy` 顶部配置：

```renpy
define renpy_danmaku_api_base = "这里填 API Base"
define renpy_danmaku_project_key = "这里填 Project Key"
```

3. 必须把弹幕预取放进 `label splashscreen`。如果用户项目没有 `label splashscreen`，就新建一个。不要放进 `label start`，因为玩家读档不会执行 `label start`。

```renpy
label splashscreen:
    $ renpy_danmaku_prefetch()
    return
```

如果用户已有 `label splashscreen`，只把这一行合并进去，不要破坏原有启动逻辑：

```renpy
$ renpy_danmaku_prefetch()
```

这个调用会后台连接弹幕，不应阻塞启动、读档或进入主菜单。

4. 在桌面版 `screen quick_menu()` 中加入：

```renpy
textbutton ("弹幕：开" if persistent.renpy_danmaku_enabled else "弹幕：关") action ToggleField(persistent, "renpy_danmaku_enabled")
textbutton _("发弹幕") action Function(renpy_danmaku_open_input):
    sensitive renpy_danmaku_is_send_allowed()
```

5. 如果项目有触屏版 `screen quick_menu(): variant "touch"`，也加入：

```renpy
textbutton ("弹幕开" if persistent.renpy_danmaku_enabled else "弹幕关") action ToggleField(persistent, "renpy_danmaku_enabled")
textbutton _("发弹幕") action Function(renpy_danmaku_open_input):
    sensitive renpy_danmaku_is_send_allowed()
```

6. 在 `screen preferences()` 里加入显示设置、连接状态和重新连接按钮。先在 `screen preferences()` 内加入轻量刷新 timer：

```renpy
timer 0.5 repeat True action NullAction()
```

然后加入弹幕设置区：

```renpy
vbox:
    style_prefix "radio"
    label _("弹幕形式")
    textbutton _("列表式") action SetField(persistent, "renpy_danmaku_style", "list")
    textbutton _("顶部飘动") action SetField(persistent, "renpy_danmaku_style", "scroll")

vbox:
    style_prefix "check"
    label _("弹幕")
    textbutton _("显示弹幕") action ToggleField(persistent, "renpy_danmaku_enabled")
    text ("连接状态：" + renpy_danmaku_connection_status_text()):
        color renpy_danmaku_connection_status_color()
    textbutton _("重新连接") action Function(renpy_danmaku_prefetch, True, True)
```

## WordPress 插件

用户应在 WordPress 后台进入 `插件` -> `安装插件` -> `上传插件`，上传分发包根目录的 `Renpy-Danmaku-WordPressPlugin.zip` 并启用。

插件启用后，在 WordPress 后台 `RenPy Danmaku` 创建项目，再复制 `API Base` 和 `Project Key` 填入 `danmaku_system.rpy`。

## Android 中文输入补丁

如果用户要发布安卓版，这一步是必装项。

Ren'Py 8.5.0 用户可以先备份引擎里的目标文件，然后用根目录的 `SDLActivity.java.mod` 作为完整补丁文件，把它复制/改名为目标位置的 `SDLActivity.java`。

目标文件通常是：

```text
Ren'Py SDK/rapt/prototype/renpyandroid/src/main/java/org/libsdl/app/SDLActivity.java
```

如果用户的 Ren'Py 版本不是 8.5.0，默认建议不要手动逐段合并。请让用户把这两份文件交给你：

- 分发包根目录的 `SDLActivity.java.mod`
- 用户 Ren'Py SDK 中的原始 `SDLActivity.java`

让 AI 按 `.mod` 文件中的补丁实现，把中文输入修复和高刷新率代码合并到原始 `SDLActivity.java`。合并后提醒用户在 Ren'Py Launcher 中执行“清理安卓临时文件”，重新构建 Android 包，并用真机测试中文输入。

## 不要做的事

- 不要修改用户的剧情文本、角色定义、存档逻辑或其它与弹幕接入无关的 UI。
- 不要把 `$ renpy_danmaku_prefetch()` 放进 `label start` 当默认方案。

## 完成后检查

- 启动游戏停在主菜单时，右上角能看到弹幕连接状态提示。
- 新开游戏和读档都不会漏掉弹幕预取。
- 快捷菜单有弹幕开关和发送按钮。
- 设置页有弹幕显示模式、显示开关、连接状态和重新连接按钮。
- 未配置或服务器不可用时，游戏不会卡住。
- 如果发布安卓版，真机中文输入可以正常提交弹幕。
