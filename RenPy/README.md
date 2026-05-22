# Ren'Py 弹幕系统解决方案

这是一个可分发的 Ren'Py 弹幕系统包，包含：

- `danmaku_system.rpy`：可复制到 Ren'Py 游戏的单文件客户端模块。
- `Renpy-Webgal-Danmaku-WordPressPlugin.zip`：WordPress 多项目弹幕插件安装包。
- `SDLActivity.java.mod`：安卓版中文输入与高刷新率补丁参考文件。
- `安卓键盘补丁安装说明.md`：安卓版中文输入与高刷新率补丁说明。
- `agent for install.md`：给用户的 AI/编程智能体使用的接入说明。
- 本 README 和其他根目录说明文档。

所有需要用户使用的文件都放在分发包根目录。

## 1. 安装 WordPress 插件

1. 准备一个 WordPress 网站。
2. 在 WordPress 后台进入 `插件` -> `安装插件` -> `上传插件`，选择本包提供的 `Renpy-Danmaku-WordPressPlugin.zip` 并点击安装。
3. 安装完成后启用 `Ren'Py Danmaku` 插件。
4. 打开左侧菜单 `RenPy Danmaku`。
5. 按首次配置向导创建项目，设置项目管理入口的管理用户名和管理密码，并选择审核策略：
   - `先审后发`：推荐公开发布使用，玩家本地能立即看到自己发的弹幕，其他玩家需审核后看到。
   - `直接公开`：适合小范围测试。
6. 管理用户名只能使用 3-32 位英文字母、数字、下划线和短横线，不允许中文；英文字母大小写按你输入的样子保存。
7. 复制后台显示的 `API Base` 和 `Project Key`。

如果你的服务器限制了后台上传，也可以先解压 `Renpy-Danmaku-WordPressPlugin.zip`，再用 FTP/SFTP 把解压出的插件文件夹上传到 WordPress 的 `wp-content/plugins/`，最后回到后台启用插件。

插件会自动创建数据库表，使用 WordPress 自己的 `$wpdb` 和 REST API，不需要读取 `wp-config.php`，也不需要手动配置数据库密码。

## 2. 接入 Ren'Py 游戏

1. 将本包的 `danmaku_system.rpy` 复制到你的游戏 `game/` 目录。
2. 打开你游戏里的 `game/danmaku_system.rpy`，填写 WordPress 后台给出的配置：

```renpy
define renpy_danmaku_api_base = "https://example.com/wp-json/renpy-danmaku/v1"
define renpy_danmaku_project_key = "你的ProjectKey"
```

3. 打开你的游戏的 `script.rpy` 文件，必须将以下代码放进 `label splashscreen`。

```renpy
$ renpy_danmaku_prefetch()
```

如果你的项目没有 `label splashscreen`，请新建一个放在`label start`前面；不要直接放在 `label start` 里面，因为玩家读档时不会执行 `label start`：

```renpy
label splashscreen:
    $ renpy_danmaku_prefetch()
    return
```

这个调用会后台联网，不会阻塞剧情或读档。默认会在启动/主菜单阶段的右上角短暂显示 `正在连接弹幕...`、`弹幕已连接`、`弹幕服务暂时不可用` 或 `弹幕服务端尚未配置`。

4. 打开你的游戏的 `screens.rpy` 文件，在桌面版 `screen quick_menu()` 中加入：

```renpy
textbutton ("弹幕：开" if persistent.renpy_danmaku_enabled else "弹幕：关") action ToggleField(persistent, "renpy_danmaku_enabled")
textbutton _("发弹幕") action Function(renpy_danmaku_open_input):
    sensitive renpy_danmaku_is_send_allowed()
```

5. 如果你的 `screens.rpy` 里还有触屏版 `screen quick_menu(): variant "touch"`，也加入：

```renpy
textbutton ("弹幕开" if persistent.renpy_danmaku_enabled else "弹幕关") action ToggleField(persistent, "renpy_danmaku_enabled")
textbutton _("发弹幕") action Function(renpy_danmaku_open_input):
    sensitive renpy_danmaku_is_send_allowed()
```

6. 在 `screen preferences()` 里加入显示模式、连接状态和重新连接按钮。为了让后台连接完成后状态文字刷新，请在 `screen preferences()` 内加入这个轻量 timer：
写在screen preferences()里面的tag menu下面

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

## 3. Android 中文输入与高刷新率补丁

如果你的游戏要发布安卓版，这个补丁是必装项。否则安卓用户可能无法发送中文弹幕。补丁安装步骤也会默认加入高刷新率请求代码，让支持 90/120/144Hz 的设备优先使用更高刷新率。

本补丁面向 Ren'Py 8.5.0。分发包根目录提供 `SDLActivity.java.mod`，它是完整补丁参考文件。更详细的步骤见根目录 `安卓键盘补丁安装说明.md`。

```text
Ren'Py SDK/rapt/prototype/renpyandroid/src/main/java/org/libsdl/app/SDLActivity.java
```

一般只需要改 `rapt/prototype`，不用改 `rapt/project`。改完后，在 Ren'Py Launcher 里点一次“清理安卓临时文件”，让安卓项目重新生成，再重新构建安卓包。

如果你的 Ren'Py 版本就是 8.5.0，可以先备份目标文件，再把 `SDLActivity.java.mod` 复制到目标位置并改名/覆盖为 `SDLActivity.java`。

如果你的 Ren'Py 版本不是 8.5.0，默认建议不要手动逐段合并，因为 Java 修改比较繁琐。请把下面两份文件一起交给 AI（包括网页版 AI）或熟悉 Android 的开发者，让它按 `.mod` 文件里的补丁实现合并：

- 分发包根目录的 `SDLActivity.java.mod`
- 你自己的 Ren'Py SDK 原始文件：`rapt/prototype/renpyandroid/src/main/java/org/libsdl/app/SDLActivity.java`

不需要上传整个游戏项目。AI 合并后，把修改后的 `SDLActivity.java` 放回原位置，并在 Ren'Py Launcher 里清理安卓临时文件。

升级 Ren'Py SDK 后必须重新核对并重新应用补丁。若你的 SDK 版本不是 8.5.0，不要盲目整文件覆盖。

## 4. 使用网页版 AI 帮你接入

如果你没有本地编程智能体，也可以把必要文件交给网页版 AI，让它帮你合并 `screens.rpy` 和 `script.rpy`。

建议上传或粘贴：

- 你自己游戏的 `game/screens.rpy`
- 你自己游戏的 `game/script.rpy`
- 分发包根目录的 `danmaku_system.rpy`
- 分发包根目录的 `agent for install.md`
- WordPress 插件后台复制出的 `API Base` 和 `Project Key`

如果网页版 AI 上传文件数量有限，就分步处理，一次一个文件

不要上传这些内容：存档、`.rpyc`、私钥、WordPress 管理员密码、商业敏感剧情全文或其它与弹幕接入无关的私密文件。除非你明确接受网页版 AI 看到这些内容。

可以直接复制下面这段提示词：

```text
你是一名熟悉 Ren'Py 的开发助手。请帮我把 Ren'Py 弹幕系统接入我的游戏。

我会提供：
1. 我自己的 game/screens.rpy
2. 我自己的 game/script.rpy，或其中现有 label splashscreen 附近的代码；如果没有 label splashscreen，请帮我新建
3. 弹幕系统文件 danmaku_system.rpy
4. WordPress 插件后台生成的 API Base 和 Project Key

请完成这些任务：
1. 告诉我把 danmaku_system.rpy 放到我游戏的 game/ 目录。
2. 在 danmaku_system.rpy 顶部填入：
   define renpy_danmaku_api_base = "这里填我的 API Base"
   define renpy_danmaku_project_key = "这里填我的 Project Key"
   如果 PC/安卓提示“弹幕服务暂时不可用”，但浏览器能打开 comments 接口看到 JSON，通常是 Ren'Py 证书校验问题；Web 版则必须使用浏览器认可的有效 HTTPS 证书。
3. 在合适的启动位置加入：
   label splashscreen:
       $ renpy_danmaku_prefetch()
       return
   必须放在 label splashscreen。如果我的游戏已经有 label splashscreen，就把 `$ renpy_danmaku_prefetch()` 合并进去；如果没有，请新建 label splashscreen。不要放在 label start，因为玩家读档时不会执行 label start。这个调用会后台连接弹幕。
4. 在桌面版 `screen quick_menu()` 中加入“弹幕开关”和“发弹幕”按钮：
   textbutton ("弹幕：开" if persistent.renpy_danmaku_enabled else "弹幕：关") action ToggleField(persistent, "renpy_danmaku_enabled")
   textbutton _("发弹幕") action Function(renpy_danmaku_open_input):
       sensitive renpy_danmaku_is_send_allowed()
5. 如果有触屏版 quick_menu，也加入对应按钮。
6. 在设置页 `preferences` 加入“弹幕形式”“显示弹幕”“连接状态”和“重新连接”设置，并在 `screen preferences()` 内加入 `timer 0.5 repeat True action NullAction()` 以刷新后台连接状态。
7. 不要修改我的剧情文本，不要改角色定义，不要改存档逻辑，不要改任何与弹幕接入无关的代码。
8. 如果我要发布安卓版，请提醒我必须安装 Android 中文输入与高刷新率补丁。Ren'Py 8.5.0 可以备份原文件后，用分发包根目录的 SDLActivity.java.mod 改名/覆盖为引擎里的 SDLActivity.java；如果 Ren'Py 版本不是 8.5.0，请建议我把 SDLActivity.java.mod 和 Ren'Py SDK 原始 SDLActivity.java 一起交给 AI 合并。默认只改 Ren'Py SDK 的 rapt/prototype/renpyandroid/src/main/java/org/libsdl/app/SDLActivity.java，改完后在 Ren'Py Launcher 里清理安卓临时文件。
9. 保留 README 中的联系方式和技术支持说明，不要删除。如果你帮我生成项目内安装说明，也请包含 QQ 联系方式和同人游戏社团/组织免费技术支持条件。

请返回修改后的完整文件，或者返回清晰的补丁。不要省略上下文到让我不知道插在哪里。
```

## 5. 需要更多协助

如果你按文档操作后仍然不会安装，或者需要更多接入协助，可以直接联系我：QQ 519968509。

如果你是同人游戏社团/组织，可以提供免费技术支持；只需要在游戏制作人员名单中加入我的名字即可。

## 6. 常见问题

### 未配置服务器时会怎样？

已接入的游戏仍可运行。玩家发送的弹幕只会本地显示，并提示“弹幕服务端尚未配置”。

### 提示“弹幕服务暂时不可用”是 WordPress 不支持 REST API 吗？

通常不是。先在浏览器打开后台给出的接口，例如：

```text
https://example.com/wp-json/renpy-danmaku/v1/projects/你的ProjectKey/comments
```

如果能看到 `{"ok":true,"items":...}`，说明 WordPress REST API 正常。PC/安卓里仍提示不可用时，常见原因是 Ren'Py 自带 Python 无法校验服务器 HTTPS 证书链。本模块默认 `renpy_danmaku_verify_ssl = False`，会用与原游戏一致的兼容方式请求 HTTPS。若你把它改成了 `True` 后出错，请先改回 `False`，或者修好服务器证书链。

如果是 Web 版，浏览器不会允许游戏绕过无效 HTTPS 证书；请给 WordPress 站点配置有效证书，并避免用 HTTPS 游戏页面请求 HTTP API。

### Project Key 是秘密吗？

不是。它是公开项目标识，会出现在游戏客户端里。防滥用主要依靠限流、审核、屏蔽词和后台管理。

### 弹幕绑定到哪里？

客户端使用 Ren'Py 的 `translate_identifier` 绑定当前台词。通常只要台词原文不变，ID 就稳定。

### 可以同时服务多个游戏吗？

可以。WordPress 插件支持多项目，每个项目有独立 Project Key、审核策略、限流和弹幕数据。

### 想清除所有弹幕相关数据怎么办？

不要依赖卸载插件自动清库。进入 WordPress 后台 `RenPy Danmaku`，在侧栏的 `危险区` 输入 `DELETE`，再点击 `清除所有数据`。

这个操作会删除插件里的所有项目、Project Key、审核设置和弹幕记录；不会删除 WordPress 文章、用户或插件文件。如果只想删除单个游戏项目，用该项目设置里的 `删除项目`。
