# -*- coding: utf-8 -*-
################################################################################
## Ren'Py 弹幕系统
##
## 将本文件复制到其他 Ren'Py 项目的 game/ 目录后，修改下方配置区。
## WordPress 插件后台会生成正确的 API Base 和 Project Key。
################################################################################

# ===== 用户配置 =====

# 示例："https://example.com/wp-json/renpy-danmaku/v1"
define renpy_danmaku_api_base = ""

# 示例："ABCD1234EFGH5678"
define renpy_danmaku_project_key = ""

# 可选字体文件，路径相对于 game/。留空则使用项目默认界面字体。
define renpy_danmaku_font = ""

define renpy_danmaku_default_color = "#ff80b8"
define renpy_danmaku_max_content_len = 50
define renpy_danmaku_fetch_on_start_tip = True

# 部分 Ren'Py 8.x 桌面/移动端环境缺少可用的 CA 证书链。
# False 会沿用原游戏行为，避免 CERTIFICATE_VERIFY_FAILED。
# 如果你的发布环境能正常校验 HTTPS，可改成 True。
define renpy_danmaku_verify_ssl = False

# 如果你认为有些剧情不适合发弹幕，可以把它们台词的 say_id 加入黑名单。
# 可根据具体剧情来调整，或者直接留空。
# 每行一个 say_id。以 # 开头的行会被忽略。
define RENPY_DANMAKU_BLACKLIST_PASTE = """
# 在这里粘贴 say_id，每行一个
"""

# ===== 玩家偏好 =====

default persistent.renpy_danmaku_enabled = True
default persistent.renpy_danmaku_style = "list"
default persistent.renpy_danmaku_notice_missing_config = True


init python:
    import time as _renpy_danmaku_time
    import math as _renpy_danmaku_math
    import random as _renpy_danmaku_random
    import builtins as _renpy_danmaku_builtins
    _real_dict = _renpy_danmaku_builtins.dict
    _real_list = _renpy_danmaku_builtins.list

    renpy_danmaku_data = {}
    renpy_danmaku_fetch_state = "idle"
    renpy_danmaku_fetch_message = ""
    renpy_danmaku_status_message = ""
    renpy_danmaku_status_kind = "info"
    renpy_danmaku_status_until = 0.0
    renpy_danmaku_status_duration = 0.0
    renpy_danmaku_status_started = False
    _renpy_danmaku_fetch_show_tip = True
    _renpy_danmaku_missing_config_notified = False

    def renpy_danmaku_parse_blacklist(raw_text):
        result = set()
        for line in raw_text.splitlines():
            item = line.strip()
            if not item or item.startswith("#"):
                continue
            if item.endswith(","):
                item = item[:-1].strip()
            if (item.startswith('"') and item.endswith('"')) or (item.startswith("'") and item.endswith("'")):
                item = item[1:-1].strip()
            if item:
                result.add(item)
        return result

    RENPY_DANMAKU_SAYID_BLACKLIST = renpy_danmaku_parse_blacklist(RENPY_DANMAKU_BLACKLIST_PASTE)

    def renpy_danmaku_get_config():
        base = str(getattr(renpy.store, "renpy_danmaku_api_base", "") or "").strip().rstrip("/")
        project_key = str(getattr(renpy.store, "renpy_danmaku_project_key", "") or "").strip()
        return base, project_key

    def renpy_danmaku_is_configured():
        base, project_key = renpy_danmaku_get_config()
        return bool(base and project_key)

    def renpy_danmaku_set_fetch_status(state, message=None, duration=3.0, show_tip=True):
        global renpy_danmaku_fetch_state
        global renpy_danmaku_fetch_message
        global renpy_danmaku_status_message
        global renpy_danmaku_status_kind
        global renpy_danmaku_status_until
        global renpy_danmaku_status_duration
        global renpy_danmaku_status_started

        renpy_danmaku_fetch_state = state

        default_messages = {
            "loading": "正在连接弹幕...",
            "ready": "弹幕已连接",
            "error": "弹幕服务暂时不可用",
            "local": "弹幕服务端尚未配置",
            "idle": "",
        }
        if message is None:
            message = default_messages.get(state, "")

        renpy_danmaku_fetch_message = message

        if not show_tip or not getattr(renpy.store, "renpy_danmaku_fetch_on_start_tip", True):
            renpy_danmaku_status_message = ""
            renpy_danmaku_status_until = 0.0
            renpy_danmaku_status_duration = 0.0
            renpy_danmaku_status_started = False
            return

        renpy_danmaku_status_message = message
        if state == "loading":
            renpy_danmaku_status_kind = "loading"
            renpy_danmaku_status_until = 0.0
            renpy_danmaku_status_duration = 0.0
            renpy_danmaku_status_started = True
        elif state == "ready":
            renpy_danmaku_status_kind = "ready"
            renpy_danmaku_status_until = 0.0
            renpy_danmaku_status_duration = duration
            renpy_danmaku_status_started = False
        else:
            renpy_danmaku_status_kind = "error"
            renpy_danmaku_status_until = 0.0
            renpy_danmaku_status_duration = max(duration, 4.0)
            renpy_danmaku_status_started = False

    def renpy_danmaku_connection_status_text():
        if renpy_danmaku_fetch_message:
            return renpy_danmaku_fetch_message
        if renpy_danmaku_fetch_state == "idle":
            if renpy_danmaku_is_configured():
                return "尚未连接弹幕"
            return "弹幕服务端尚未配置"
        return {
            "loading": "正在连接弹幕...",
            "ready": "弹幕已连接",
            "error": "弹幕服务暂时不可用",
            "local": "弹幕服务端尚未配置",
        }.get(renpy_danmaku_fetch_state, "弹幕状态未知")

    def renpy_danmaku_connection_status_color():
        if renpy_danmaku_fetch_state == "ready":
            return "#278a5d"
        if renpy_danmaku_fetch_state == "loading":
            return "#2f5fbd"
        if renpy_danmaku_fetch_state == "idle":
            return "#666666"
        return "#b32d2e"

    def renpy_danmaku_show_status_screen(show_tip=True):
        if not show_tip or not getattr(renpy.store, "renpy_danmaku_fetch_on_start_tip", True):
            return
        try:
            renpy.show_screen("renpy_danmaku_status_overlay")
        except Exception:
            pass

    def renpy_danmaku_status_screen_active():
        return bool(renpy_danmaku_status_message)

    def renpy_danmaku_status_visible():
        if not renpy_danmaku_status_message:
            return False
        if renpy_danmaku_fetch_state == "loading":
            return True
        if not renpy_danmaku_status_started:
            return True
        return _renpy_danmaku_time.time() < renpy_danmaku_status_until

    def renpy_danmaku_status_mark_visible():
        global renpy_danmaku_status_until
        global renpy_danmaku_status_started

        if not renpy_danmaku_status_message or renpy_danmaku_fetch_state == "loading":
            return
        if renpy_danmaku_status_started:
            return
        renpy_danmaku_status_started = True
        renpy_danmaku_status_until = _renpy_danmaku_time.time() + max(0.1, renpy_danmaku_status_duration)

    def renpy_danmaku_status_background():
        if renpy_danmaku_status_kind == "ready":
            return "#278a5ddd"
        if renpy_danmaku_status_kind == "loading":
            return "#2f5fbdde"
        return "#333333dd"

    def renpy_danmaku_status_tick():
        global renpy_danmaku_status_message
        global renpy_danmaku_status_until
        global renpy_danmaku_status_duration
        global renpy_danmaku_status_started

        if renpy_danmaku_status_message and not renpy_danmaku_status_visible():
            renpy_danmaku_status_message = ""
            renpy_danmaku_status_until = 0.0
            renpy_danmaku_status_duration = 0.0
            renpy_danmaku_status_started = False
            try:
                renpy.hide_screen("renpy_danmaku_status_overlay")
            except Exception:
                pass
        return None

    def renpy_danmaku_notify_missing_config(force=False):
        global _renpy_danmaku_missing_config_notified
        if not force and _renpy_danmaku_missing_config_notified:
            return
        if not getattr(persistent, "renpy_danmaku_notice_missing_config", True):
            return
        _renpy_danmaku_missing_config_notified = True
        renpy.notify("弹幕服务端尚未配置。")

    def renpy_danmaku_endpoint(kind):
        base, project_key = renpy_danmaku_get_config()
        if not base or not project_key:
            return ""
        try:
            import urllib.parse as _renpy_danmaku_urlparse
            safe_key = _renpy_danmaku_urlparse.quote(project_key, safe="")
        except Exception:
            safe_key = project_key
        if kind == "health":
            return base + "/projects/" + safe_key + "/health"
        return base + "/projects/" + safe_key + "/comments"

    def renpy_danmaku_get_current_say_id():
        """返回当前台词稳定的 Ren'Py 翻译标识。"""
        try:
            return renpy.game.context().translate_identifier or ""
        except Exception:
            return ""

    def renpy_danmaku_is_send_allowed():
        sid = renpy_danmaku_get_current_say_id()
        blacklist = globals().get("RENPY_DANMAKU_SAYID_BLACKLIST", set())
        if not sid:
            return True
        return sid not in blacklist

    def renpy_danmaku_wrap_text(text, max_chars=15):
        if len(text) <= max_chars:
            return text
        lines = []
        while text:
            lines.append(text[:max_chars])
            text = text[max_chars:]
        return "\n".join(lines)

    def renpy_danmaku_normalize_items(raw):
        if not isinstance(raw, _real_dict):
            return {}
        if "items" in raw and isinstance(raw.get("items"), _real_dict):
            raw = raw.get("items", {})

        normalized = {}
        max_len = int(getattr(renpy.store, "renpy_danmaku_max_content_len", 50) or 50)
        for sid, items in raw.items():
            if not isinstance(sid, str) or not isinstance(items, _real_list):
                continue
            cleaned = []
            for item in items:
                if not isinstance(item, _real_dict):
                    continue
                text = str(item.get("c", item.get("content", "")) or "").strip()
                color = str(item.get("o", item.get("color", renpy_danmaku_default_color)) or renpy_danmaku_default_color)
                if not text:
                    continue
                if len(text) > max_len:
                    text = text[:max_len]
                if not renpy_danmaku_is_valid_color(color):
                    color = renpy_danmaku_default_color
                cleaned.append({"c": text, "o": color})
            if cleaned:
                normalized[sid] = cleaned
        return normalized

    def renpy_danmaku_is_valid_color(color):
        if not isinstance(color, str) or len(color) != 7 or not color.startswith("#"):
            return False
        try:
            int(color[1:], 16)
            return True
        except Exception:
            return False

    def renpy_danmaku_urlopen(target, timeout=10):
        import urllib.request as _renpy_danmaku_request
        kwargs = {"timeout": timeout}
        url = getattr(target, "full_url", target)
        url = str(url or "")
        verify_ssl = bool(getattr(renpy.store, "renpy_danmaku_verify_ssl", False))

        if url.lower().startswith("https://") and not verify_ssl:
            try:
                import ssl as _renpy_danmaku_ssl
                ctx = _renpy_danmaku_ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = _renpy_danmaku_ssl.CERT_NONE
                kwargs["context"] = ctx
            except Exception:
                pass

        return _renpy_danmaku_request.urlopen(target, **kwargs)

    def renpy_danmaku_fetch_all(show_tip=True):
        """
        拉取所有已通过审核的弹幕。
        桌面/移动端在后台线程中使用 urllib；Web 版使用异步 XHR，
        再由 Displayable 轮询 window.__renpy_danmaku_json。
        """
        global renpy_danmaku_data
        url = renpy_danmaku_endpoint("comments")
        if not url:
            renpy_danmaku_set_fetch_status("local", show_tip=show_tip)
            return

        try:
            if renpy.variant("web"):
                import json as _renpy_danmaku_json
                import emscripten
                js_url = _renpy_danmaku_json.dumps(url)
                emscripten.run_script(
                    "(function(){"
                    "var xhr=new XMLHttpRequest();"
                    "xhr.timeout=10000;"
                    "xhr.open('GET'," + js_url + ",true);"
                    "xhr.onload=function(){"
                    " if(xhr.status>=200&&xhr.status<300){window.__renpy_danmaku_json=xhr.responseText;}"
                    " else{window.__renpy_danmaku_fetch_err='弹幕服务暂时不可用';}"
                    "};"
                    "xhr.onerror=function(){window.__renpy_danmaku_fetch_err='弹幕服务暂时不可用';};"
                    "xhr.ontimeout=function(){window.__renpy_danmaku_fetch_err='弹幕连接超时';};"
                    "xhr.send(null);"
                    "})()"
                )
            else:
                import json as _renpy_danmaku_json
                with renpy_danmaku_urlopen(url, timeout=10) as resp:
                    payload = _renpy_danmaku_json.loads(resp.read().decode("utf-8"))
                if isinstance(payload, _real_dict) and payload.get("ok") is False:
                    raise Exception(str(payload.get("msg", "fetch failed")))
                renpy_danmaku_data.update(renpy_danmaku_normalize_items(payload))
                renpy_danmaku_set_fetch_status("ready", show_tip=show_tip)
        except Exception:
            renpy_danmaku_set_fetch_status("error", show_tip=show_tip)

    def renpy_danmaku_prefetch(show_tip=True, force=False):
        global _renpy_danmaku_fetch_show_tip
        _renpy_danmaku_fetch_show_tip = show_tip
        renpy_danmaku_show_status_screen(show_tip=show_tip)
        if not renpy_danmaku_is_configured():
            renpy_danmaku_set_fetch_status("local", show_tip=show_tip)
            return
        if renpy_danmaku_fetch_state == "loading" and not force:
            return
        renpy_danmaku_set_fetch_status("loading", show_tip=show_tip)
        if renpy.variant("web"):
            renpy_danmaku_fetch_all(show_tip=show_tip)
        else:
            renpy.invoke_in_thread(lambda: renpy_danmaku_fetch_all(show_tip=show_tip))

    def renpy_danmaku_post(say_id, content, color="#ff80b8"):
        global renpy_danmaku_data
        url = renpy_danmaku_endpoint("comments")
        if not url:
            renpy_danmaku_notify_missing_config(force=True)
            return
        if not say_id or not content:
            return

        max_len = int(getattr(renpy.store, "renpy_danmaku_max_content_len", 50) or 50)
        content = str(content).strip()[:max_len]
        if not renpy_danmaku_is_valid_color(color):
            color = renpy_danmaku_default_color

        try:
            import json as _renpy_danmaku_json
            payload = _renpy_danmaku_json.dumps({
                "say_id": say_id,
                "content": content,
                "color": color,
            })

            if renpy.variant("web"):
                import emscripten
                js_url = _renpy_danmaku_json.dumps(url)
                js_payload = _renpy_danmaku_json.dumps(payload)
                emscripten.run_script(
                    "(function(){"
                    "var xhr=new XMLHttpRequest();"
                    "xhr.open('POST'," + js_url + ",true);"
                    "xhr.setRequestHeader('Content-Type','application/json');"
                    "xhr.onload=function(){"
                    " try{var r=JSON.parse(xhr.responseText||'{}');"
                    " if(!r.ok){window.__renpy_danmaku_err=r.msg||'发送失败';}"
                    " else if(r.status==='pending'){window.__renpy_danmaku_msg='弹幕已提交，审核后会向其他玩家展示';}"
                    " }catch(e){window.__renpy_danmaku_err='发送失败';}"
                    "};"
                    "xhr.onerror=function(){window.__renpy_danmaku_err='网络错误';};"
                    "xhr.send(" + js_payload + ");"
                    "})()"
                )
            else:
                import urllib.request as _renpy_danmaku_request
                req = _renpy_danmaku_request.Request(
                    url,
                    data=payload.encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with renpy_danmaku_urlopen(req, timeout=8) as resp:
                    result = _renpy_danmaku_json.loads(resp.read().decode("utf-8"))
                if not result.get("ok"):
                    renpy.notify(result.get("msg", "发送失败"))
                elif result.get("status") == "pending":
                    renpy.notify("弹幕已提交，审核后会向其他玩家展示")
        except Exception:
            if not renpy.variant("web"):
                renpy.notify("发送失败，请检查网络")

    class RenPyDanmakuManager(object):
        MAX_PER_LINE = 6
        MAX_ACTIVE = 30

        def __init__(self):
            self._is_mobile = renpy.variant("mobile")
            self._is_web_phone = renpy.variant("web") and renpy.variant("small")
            mobile = self._is_mobile

            _h = float(renpy.config.screen_height)
            self._scale = max(0.5, min(2.0, _h / 1080.0))

            self.NUM_LANES = 8 if mobile else 15
            self.SCROLL_FONT_SIZE = int(round((54 if mobile else 45) * self._scale))
            self.LANE_SPACING_RATIO = 1.33 if mobile else 1.15
            self.LANE_SPACING = int(round(self.SCROLL_FONT_SIZE * self.LANE_SPACING_RATIO))
            self.LANE_TOP = int(round(20 * self._scale))
            self.SCROLL_DURATION_BASE = 12.0
            self.SCROLL_DURATION_STEP = 0.8
            self.SCROLL_DURATION_VARIANTS = 5
            self.SCROLL_SINGLE_DURATION = 13.0
            self.SCROLL_LANE_HOLD_TIME = 4.5
            self.SCROLL_TRAVEL_FACTOR = 1.5

            self.active = []
            self.lane_free_at = [0.0] * self.NUM_LANES
            self.last_say_id = ""
            self.pending_queue = []

            self.LIST_FONT_SIZE = int(round((41 if mobile else 34) * self._scale))
            self.LIST_LINE_HEIGHT_RATIO = 1.22
            self.LIST_ITEM_PADDING_RATIO = 0.20
            self.LIST_STACK_GAP_RATIO = 0.10
            self.LIST_LINE_HEIGHT = int(round(self.LIST_FONT_SIZE * self.LIST_LINE_HEIGHT_RATIO))
            self.LIST_ITEM_PADDING = max(6, int(round(self.LIST_FONT_SIZE * self.LIST_ITEM_PADDING_RATIO)))
            self.LIST_STACK_GAP = max(2, int(round(self.LIST_FONT_SIZE * self.LIST_STACK_GAP_RATIO)))

            self.LIST_START_Y = int(round((600 if mobile else 720) * self._scale))
            self.LIST_DURATION = 10.0
            self.LIST_SLIDE_IN_TIME = 0.36 if not mobile else 0.30
            self.LIST_SLIDE_FROM_X = int(round(-300 * self._scale))
            self.LIST_FINAL_X = int(round((60 if mobile else 40) * self._scale))
            self.LIST_FADE_OUT_TIME = 0.5

            self.SCROLL_OUTLINE_WIDTH = max(1, int(round(1 * self._scale)))
            self.SCROLL_OUTLINE_COLOR = "#ffffffff"
            self.LIST_OUTLINE_WIDTH = max(1, int(round((2 if mobile else 1) * self._scale)))
            self.LIST_OUTLINE_COLOR = "#ffffffff"

        def get_font_size(self, style):
            if style == "scroll":
                return self.SCROLL_FONT_SIZE
            return self.LIST_FONT_SIZE

        def get_item_outlines(self, style):
            if style == "list":
                return [(self.LIST_OUTLINE_WIDTH, self.LIST_OUTLINE_COLOR, 0, 0)]
            return [(self.SCROLL_OUTLINE_WIDTH, self.SCROLL_OUTLINE_COLOR, 0, 0)]

        def _calc_list_item_height(self, text):
            num_lines = text.count("\n") + 1
            return num_lines * self.LIST_LINE_HEIGHT + self.LIST_ITEM_PADDING

        def _get_list_push_distance(self, new_item_h):
            bottom_item_h = new_item_h
            bottom_y = float("-inf")
            for item in self.active:
                if item.get("style", "scroll") == "list" and item["target_y"] > bottom_y:
                    bottom_y = item["target_y"]
                    bottom_item_h = item.get("h", new_item_h)
            return bottom_item_h + self.LIST_STACK_GAP

        def _push_existing_list_items(self, new_item_h):
            push_h = self._get_list_push_distance(new_item_h)
            for item in self.active:
                if item.get("style", "scroll") == "list":
                    item["target_y"] -= push_h
                    if self._is_web_phone:
                        item["y"] = item["target_y"]

        def check_new_line(self):
            sid = renpy_danmaku_get_current_say_id()
            if sid and sid != self.last_say_id:
                self.last_say_id = sid
                if renpy.config.skipping:
                    return
                if len(self.active) + len(self.pending_queue) >= self.MAX_ACTIVE:
                    return
                items = renpy_danmaku_data.get(sid, [])
                if items:
                    self._add_batch(items)

        def _add_batch(self, items):
            now = _renpy_danmaku_time.time()
            style = getattr(persistent, "renpy_danmaku_style", "list")

            if style == "list":
                if len(items) > 7:
                    items = _renpy_danmaku_random.sample(items, 7)
                start_time = now + 2.0
                if self.pending_queue:
                    start_time = max(start_time, self.pending_queue[-1]["pop_time"] + 0.3)
                for i, item in enumerate(items):
                    wrapped = renpy_danmaku_wrap_text(item["c"])
                    h = self._calc_list_item_height(wrapped)
                    self.pending_queue.append({
                        "c": wrapped,
                        "o": item["o"],
                        "pop_time": start_time + i * 0.3,
                        "h": h,
                    })
            else:
                remaining = self.MAX_ACTIVE - len(self.active)
                count = min(self.MAX_PER_LINE, remaining)
                if count <= 0:
                    return
                for i, item in enumerate(items[:count]):
                    lane = self._find_free_lane(now + i * 0.3)
                    duration = self.SCROLL_DURATION_BASE + (i % self.SCROLL_DURATION_VARIANTS) * self.SCROLL_DURATION_STEP
                    start = now + i * 0.3
                    self.active.append({
                        "t": item["c"],
                        "o": item["o"],
                        "l": lane,
                        "s": start,
                        "d": duration,
                        "style": "scroll",
                    })
                    self.lane_free_at[lane] = start + self.SCROLL_LANE_HOLD_TIME

        def update(self, now):
            while self.pending_queue and now >= self.pending_queue[0]["pop_time"]:
                item = self.pending_queue.pop(0)
                item_h = item.get("h", self._calc_list_item_height(item["c"]))
                self._push_existing_list_items(item_h)
                self.active.append({
                    "t": item["c"],
                    "o": item["o"],
                    "s": now,
                    "d": self.LIST_DURATION,
                    "style": "list",
                    "y": self.LIST_START_Y,
                    "target_y": self.LIST_START_Y,
                    "h": item_h,
                })

        def add_single(self, text, color):
            now = _renpy_danmaku_time.time()
            style = getattr(persistent, "renpy_danmaku_style", "list")

            if style == "list":
                wrapped = renpy_danmaku_wrap_text(text)
                item_h = self._calc_list_item_height(wrapped)
                self._push_existing_list_items(item_h)
                self.active.append({
                    "t": wrapped,
                    "o": color,
                    "s": now,
                    "d": self.LIST_DURATION,
                    "style": "list",
                    "y": self.LIST_START_Y,
                    "target_y": self.LIST_START_Y,
                    "h": item_h,
                })
            else:
                lane = self._find_free_lane(now)
                self.active.append({
                    "t": text,
                    "o": color,
                    "l": lane,
                    "s": now,
                    "d": self.SCROLL_SINGLE_DURATION,
                    "style": "scroll",
                })
                self.lane_free_at[lane] = now + self.SCROLL_LANE_HOLD_TIME

        def _find_free_lane(self, at_time):
            for i in range(self.NUM_LANES):
                if self.lane_free_at[i] <= at_time:
                    return i
            return min(range(self.NUM_LANES), key=lambda i: self.lane_free_at[i])

        def cleanup(self, now):
            self.active = [item for item in self.active if now - item["s"] < item["d"]]

    renpy_danmaku_mgr = RenPyDanmakuManager()

    class RenPyDanmakuDisplayable(renpy.Displayable):
        def __init__(self, **kwargs):
            super(RenPyDanmakuDisplayable, self).__init__(**kwargs)
            self._text_cache = {}
            self._is_web_phone = renpy.variant("web") and renpy.variant("small")
            self._last_web_poll_time = 0.0
            self._last_render_time = 0.0
            self._last_cache_clean = 0.0

        def _poll_web(self, st, at):
            try:
                import emscripten
                pending = emscripten.run_script_string(
                    "typeof window.__renpy_danmaku_json!=='undefined'?window.__renpy_danmaku_json:''"
                )
                if pending:
                    import json as _renpy_danmaku_json
                    try:
                        payload = _renpy_danmaku_json.loads(pending)
                        if isinstance(payload, _real_dict) and payload.get("ok") is False:
                            raise Exception(str(payload.get("msg", "fetch failed")))
                        renpy_danmaku_data.update(renpy_danmaku_normalize_items(payload))
                        renpy_danmaku_set_fetch_status("ready", show_tip=_renpy_danmaku_fetch_show_tip)
                    except Exception:
                        renpy_danmaku_set_fetch_status("error", show_tip=_renpy_danmaku_fetch_show_tip)
                    finally:
                        emscripten.run_script("delete window.__renpy_danmaku_json;")

                fetch_err = emscripten.run_script_string(
                    "typeof window.__renpy_danmaku_fetch_err!=='undefined'?window.__renpy_danmaku_fetch_err:''"
                )
                if fetch_err:
                    renpy_danmaku_set_fetch_status("error", fetch_err, show_tip=_renpy_danmaku_fetch_show_tip)
                    emscripten.run_script("delete window.__renpy_danmaku_fetch_err;")

                err = emscripten.run_script_string(
                    "typeof window.__renpy_danmaku_err!=='undefined'?window.__renpy_danmaku_err:''"
                )
                if err:
                    renpy.notify(err)
                    emscripten.run_script("delete window.__renpy_danmaku_err;")

                msg = emscripten.run_script_string(
                    "typeof window.__renpy_danmaku_msg!=='undefined'?window.__renpy_danmaku_msg:''"
                )
                if msg:
                    renpy.notify(msg)
                    emscripten.run_script("delete window.__renpy_danmaku_msg;")
            except Exception:
                pass

        def _poll_web_if_due(self, now, st, at):
            if not renpy.variant("web"):
                return
            if self._last_web_poll_time <= 0.0 or (now - self._last_web_poll_time) >= 0.25:
                self._last_web_poll_time = now
                self._poll_web(st, at)

        def _render_text_with_alpha(self, txt, alpha, width, height, st, at):
            if renpy.variant("web") and alpha >= 0.999:
                return renpy.render(txt, width, height, st, at)
            txt_d = Transform(txt, alpha=alpha)
            return renpy.render(txt_d, width, height, st, at)

        def _web_phone_list_redraw_delay(self, now):
            delay = 0.25
            if renpy_danmaku_mgr.pending_queue:
                delay = min(delay, max(0.0, renpy_danmaku_mgr.pending_queue[0]["pop_time"] - now))
            for item in renpy_danmaku_mgr.active:
                if item.get("style", "scroll") != "list":
                    continue
                remaining = item["d"] - (now - item["s"])
                if remaining > 0.0:
                    delay = min(delay, remaining)
            return max(0.0, delay)

        def _make_text(self, item, font_size, style):
            item_outlines = renpy_danmaku_mgr.get_item_outlines(style)
            font_name = str(getattr(renpy.store, "renpy_danmaku_font", "") or "").strip()
            if not font_name:
                try:
                    font_name = gui.text_font
                except Exception:
                    font_name = ""
            cache_key = (item["t"], item["o"], font_size, style, tuple(item_outlines), font_name)
            if cache_key not in self._text_cache:
                kwargs = {
                    "color": item["o"],
                    "size": font_size,
                    "outlines": item_outlines,
                }
                if font_name:
                    kwargs["font"] = font_name
                self._text_cache[cache_key] = renpy.text.text.Text(item["t"], **kwargs)
            return self._text_cache[cache_key], cache_key

        def render(self, width, height, st, at):
            rv = renpy.Render(width, min(height, int(round(840 * renpy_danmaku_mgr._scale))))
            now = _renpy_danmaku_time.time()

            if self._last_render_time > 0 and now - self._last_render_time > 30:
                renpy_danmaku_mgr.active = []
                renpy_danmaku_mgr.lane_free_at = [0.0] * renpy_danmaku_mgr.NUM_LANES
                renpy_danmaku_mgr.last_say_id = ""
                renpy_danmaku_mgr.pending_queue = []
                self._text_cache.clear()

            dt = now - self._last_render_time if self._last_render_time > 0 else 0.016
            self._last_render_time = now
            self._poll_web_if_due(now, st, at)
            renpy_danmaku_mgr.cleanup(now)

            if persistent.renpy_danmaku_enabled:
                renpy_danmaku_mgr.check_new_line()
                renpy_danmaku_mgr.update(now)

                for item in renpy_danmaku_mgr.active:
                    elapsed = now - item["s"]
                    if elapsed < 0:
                        continue
                    progress = elapsed / item["d"]
                    if progress >= 1.0:
                        continue

                    style = item.get("style", "scroll")
                    if style == "scroll":
                        font_size = renpy_danmaku_mgr.get_font_size("scroll")
                        x = int(width * (1.0 - progress * renpy_danmaku_mgr.SCROLL_TRAVEL_FACTOR))
                        y = item["l"] * renpy_danmaku_mgr.LANE_SPACING + renpy_danmaku_mgr.LANE_TOP
                        alpha = 1.0
                    else:
                        font_size = renpy_danmaku_mgr.get_font_size("list")
                        if self._is_web_phone:
                            item["y"] = item["target_y"]
                            y = int(item["target_y"])
                            x = renpy_danmaku_mgr.LIST_FINAL_X
                            alpha = 1.0
                        else:
                            item["y"] += (item["target_y"] - item["y"]) * (1.0 - _renpy_danmaku_math.exp(-15.0 * dt))
                            y = int(item["y"])
                            slide_in_time = renpy_danmaku_mgr.LIST_SLIDE_IN_TIME
                            final_x = renpy_danmaku_mgr.LIST_FINAL_X
                            slide_from_x = renpy_danmaku_mgr.LIST_SLIDE_FROM_X
                            if elapsed < slide_in_time:
                                slide_progress = elapsed / slide_in_time
                                ease = 1.0 - (1.0 - slide_progress) ** 3
                                x = int(slide_from_x + (final_x - slide_from_x) * ease)
                            else:
                                x = final_x
                            alpha = 1.0
                            if elapsed < slide_in_time:
                                alpha = elapsed / slide_in_time
                            elif renpy_danmaku_mgr.LIST_FADE_OUT_TIME > 0 and item["d"] - elapsed < renpy_danmaku_mgr.LIST_FADE_OUT_TIME:
                                alpha = (item["d"] - elapsed) / renpy_danmaku_mgr.LIST_FADE_OUT_TIME

                    txt, cache_key = self._make_text(item, font_size, style)
                    txt_render = self._render_text_with_alpha(txt, alpha, width, height, st, at)
                    rv.blit(txt_render, (x, y))

            if now - self._last_cache_clean > 60:
                self._last_cache_clean = now
                active_keys = set()
                for item in renpy_danmaku_mgr.active:
                    style = item.get("style", "scroll")
                    font_size = renpy_danmaku_mgr.get_font_size(style)
                    _, cache_key = self._make_text(item, font_size, style)
                    active_keys.add(cache_key)
                for key in list(self._text_cache):
                    if key not in active_keys:
                        del self._text_cache[key]

            if renpy_danmaku_mgr.active or renpy_danmaku_mgr.pending_queue:
                if self._is_web_phone:
                    has_scroll = False
                    for item in renpy_danmaku_mgr.active:
                        if item.get("style", "scroll") == "scroll":
                            has_scroll = True
                            break
                    renpy.redraw(self, 0.033 if has_scroll else self._web_phone_list_redraw_delay(now))
                else:
                    needs_high_fps = False
                    for item in renpy_danmaku_mgr.active:
                        style = item.get("style", "scroll")
                        if style == "list":
                            if now - item["s"] < renpy_danmaku_mgr.LIST_SLIDE_IN_TIME or abs(item["y"] - item["target_y"]) > 1.0:
                                needs_high_fps = True
                                break
                        elif style == "scroll":
                            needs_high_fps = True
                            break
                    renpy.redraw(self, 0.0 if needs_high_fps else 0.016)
            elif persistent.renpy_danmaku_enabled:
                renpy.redraw(self, 0.5)
            else:
                renpy.redraw(self, 1.0)
            return rv

        def event(self, ev, x, y, st):
            return None

        def visit(self):
            return []

    def renpy_danmaku_send_action():
        text = str(getattr(renpy.store, "_renpy_danmaku_send_text", "") or "").strip()
        color = str(getattr(renpy.store, "_renpy_danmaku_send_color", renpy_danmaku_default_color) or renpy_danmaku_default_color)
        max_len = int(getattr(renpy.store, "renpy_danmaku_max_content_len", 50) or 50)
        sid = renpy_danmaku_get_current_say_id()

        if not text:
            renpy.notify("请输入弹幕内容")
            return
        text = text[:max_len]
        if not renpy_danmaku_is_valid_color(color):
            color = renpy_danmaku_default_color

        renpy_danmaku_mgr.add_single(text, color)
        if sid:
            renpy_danmaku_data.setdefault(sid, []).append({"c": text, "o": color})
        else:
            renpy.notify("当前台词缺少 say_id，无法发送弹幕")
            return

        if renpy_danmaku_is_configured():
            if renpy.variant("web"):
                renpy_danmaku_post(sid, text, color)
            else:
                renpy.invoke_in_thread(lambda: renpy_danmaku_post(sid, text, color))
            renpy.notify("弹幕已发送")
        else:
            renpy_danmaku_notify_missing_config(force=True)

    def renpy_danmaku_open_input():
        if not renpy_danmaku_is_send_allowed():
            renpy.notify("这句台词已禁用弹幕发送")
            return
        if renpy.variant("web"):
            try:
                import json as _renpy_danmaku_json
                import emscripten
                prompt = _renpy_danmaku_json.dumps("发送弹幕（最多%d字）" % int(getattr(renpy.store, "renpy_danmaku_max_content_len", 50) or 50))
                text = emscripten.run_script_string("window.prompt(" + prompt + ",'') || ''")
                if text and text.strip() and text != "null":
                    renpy.store._renpy_danmaku_send_text = text.strip()
                    renpy.store._renpy_danmaku_send_color = renpy_danmaku_default_color
                    renpy_danmaku_send_action()
            except Exception:
                pass
        else:
            renpy.show_screen("renpy_danmaku_input_screen")

    def renpy_danmaku_show_android_keyboard():
        try:
            import pygame
            pygame.key.start_text_input()
        except Exception:
            pass

    if "renpy_danmaku_overlay" not in config.overlay_screens:
        config.overlay_screens.append("renpy_danmaku_overlay")
    if "renpy_danmaku_status_overlay" not in config.overlay_screens:
        config.overlay_screens.append("renpy_danmaku_status_overlay")


screen renpy_danmaku_overlay():
    zorder 201
    add RenPyDanmakuDisplayable()


screen renpy_danmaku_status_overlay():
    zorder 202

    if renpy_danmaku_status_screen_active():
        timer 0.25 repeat True action Function(renpy_danmaku_status_tick)

        if renpy_danmaku_status_visible():
            $ renpy_danmaku_status_mark_visible()
            $ scale = renpy_danmaku_mgr._scale
            frame:
                xalign 1.0
                yalign 0.0
                xoffset int(round(-24 * scale))
                yoffset int(round(24 * scale))
                padding (int(round(18 * scale)), int(round(10 * scale)))
                background Solid(renpy_danmaku_status_background())

                text renpy_danmaku_status_message:
                    color "#ffffff"
                    size int(round(22 * scale))
                    outlines [(max(1, int(round(1 * scale))), "#00000066", 0, 0)]


screen renpy_danmaku_input_screen():
    predict False
    modal True
    zorder 200

    add Solid("#00000088")

    default danmaku_text = ""
    default danmaku_color = renpy_danmaku_default_color

    $ is_mobile = renpy.variant("small") or renpy.variant("mobile")
    $ scale = renpy_danmaku_mgr._scale
    $ panel_margin = int(round((40 if is_mobile else 120) * scale))
    $ panel_max_w = int(round((1180 if is_mobile else 980) * scale))
    $ panel_w = min(config.screen_width - panel_margin, panel_max_w)
    $ send_btn_w = int(round((230 if is_mobile else 180) * scale))
    $ input_row_spacing = int(round((24 if is_mobile else 18) * scale))
    $ content_w = panel_w - int(round(80 * scale))
    $ input_box_w = max(int(round(300 * scale)), content_w - send_btn_w - input_row_spacing)

    frame:
        xalign 0.5
        yalign (0.0 if renpy.variant("mobile") else 0.5)
        yoffset (int(round(20 * scale)) if renpy.variant("mobile") else 0)
        xsize panel_w
        ysize int(round((600 if is_mobile else 450) * scale))
        background Solid("#fffffffa")
        padding (int(round(40 * scale)), int(round(30 * scale)))

        vbox:
            spacing int(round((35 if is_mobile else 25) * scale))
            xalign 0.5

            hbox:
                xfill True
                text "发送弹幕":
                    size int(round((48 if is_mobile else 36) * scale))
                    color "#ff80b8"
                    yalign 0.5
                    bold True
                textbutton "×":
                    text_size int(round((40 if is_mobile else 30) * scale))
                    text_color "#ff80c8"
                    text_hover_color "#ff80b8"
                    xalign 1.0
                    action Hide("renpy_danmaku_input_screen")

            hbox:
                xfill True
                spacing input_row_spacing

                button:
                    xsize input_box_w
                    ysize int(round((100 if is_mobile else 80) * scale))
                    background Solid("#f0f2f5")
                    padding (int(round(20 * scale)), int(round(15 * scale)))
                    action Function(renpy_danmaku_show_android_keyboard)

                    input:
                        value ScreenVariableInputValue("danmaku_text")
                        length renpy_danmaku_max_content_len
                        color "#ff80c0"
                        size int(round((40 if is_mobile else 30) * scale))
                        pixel_width (input_box_w - int(round(40 * scale)))

                textbutton "发送":
                    xsize send_btn_w
                    ysize int(round((100 if is_mobile else 80) * scale))
                    yalign 0.5
                    background "#ff80b8"
                    hover_background "#ff90c8"
                    text_size int(round((40 if is_mobile else 30) * scale))
                    text_color "#ffffff"
                    text_xalign 0.5
                    text_yalign 0.5
                    action [
                        SetVariable("_renpy_danmaku_send_text", danmaku_text),
                        SetVariable("_renpy_danmaku_send_color", danmaku_color),
                        Function(renpy_danmaku_send_action),
                        Hide("renpy_danmaku_input_screen")
                    ]

            text "弹幕可能需要审核后才会向其他玩家展示" size int(round((30 if is_mobile else 28) * scale)) color "#f080b0" xalign 0.5 text_align 0.5

            hbox:
                spacing int(round((50 if is_mobile else 30) * scale))
                xalign 0.5
                for _cname, _cval in [("粉", "#ff80b8"), ("黑", "#333333"), ("蓝", "#2059d4"), ("黄", "#ffe066"), ("白", "#ffffff")]:
                    $ _btn_size = int(round((80 if is_mobile else 60) * scale))
                    $ _sel_pad = int(round(9 * scale))
                    $ _norm_pad = int(round(2 * scale))
                    button:
                        xysize (_btn_size, _btn_size)
                        margin (0, 0)
                        padding ((_sel_pad, _sel_pad) if danmaku_color == _cval else (_norm_pad, _norm_pad))
                        background (Solid("#b3b3b3") if danmaku_color == _cval else Solid("#cccccc"))
                        hover_background (Solid("#555555") if danmaku_color == _cval else Solid("#888888"))
                        action SetScreenVariable("danmaku_color", _cval)

                        add Solid(_cval)
