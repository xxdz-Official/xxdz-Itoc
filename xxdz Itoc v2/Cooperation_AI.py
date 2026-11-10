# -*- coding: utf-8 -*-
"""
小電AI 工程协作模块
用于通过自然语言修改 .czemidi 工程文件
API 密钥和提示词内置于此
"""

import json
import os
import re
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import time


# ==================== 语言包支持（全局拦截版） ====================
import re

_GLOBAL_LANG_MAP = {}
_PATCH_INSTALLED = False

def _install_global_translator():
    global _PATCH_INSTALLED
    if _PATCH_INSTALLED:
        return

    import tkinter as tk
    from tkinter import ttk, messagebox

    def _t_str(s):
        if isinstance(s, str) and s and _GLOBAL_LANG_MAP:
            if s in _GLOBAL_LANG_MAP:
                return _GLOBAL_LANG_MAP[s]
            import re
            cleaned_s = re.sub(r'[^\w\s\u4e00-\u9fa5]', '', s).strip()
            if cleaned_s:
                for k, v in _GLOBAL_LANG_MAP.items():
                    cleaned_k = re.sub(r'[^\w\s\u4e00-\u9fa5]', '', k).strip()
                    if cleaned_s == cleaned_k:
                        return v

            pattern = re.compile(r'\d+')
            matches = pattern.findall(s)
            if matches:
                template_text = pattern.sub('{}', s)
                for k, v in _GLOBAL_LANG_MAP.items():
                    if pattern.sub('{}', k) == template_text:
                        try:
                            return v.format(*matches)
                        except Exception:
                            pass
        return s

    _orig_label_init = tk.Label.__init__
    def _new_label_init(self, master=None, cnf={}, **kw):
        if 'text' in kw: kw['text'] = _t_str(kw['text'])
        return _orig_label_init(self, master, cnf, **kw)
    tk.Label.__init__ = _new_label_init

    _orig_ttk_label_init = ttk.Label.__init__
    def _new_ttk_label_init(self, master=None, **kw):
        if 'text' in kw: kw['text'] = _t_str(kw['text'])
        return _orig_ttk_label_init(self, master, **kw)
    ttk.Label.__init__ = _new_ttk_label_init

    _orig_labelframe_init = ttk.LabelFrame.__init__
    def _new_labelframe_init(self, master=None, **kw):
        if 'text' in kw: kw['text'] = _t_str(kw['text'])
        return _orig_labelframe_init(self, master, **kw)
    ttk.LabelFrame.__init__ = _new_labelframe_init

    _orig_listbox_insert = tk.Listbox.insert
    def _new_listbox_insert(self, index, *elements):
        elements = tuple(_t_str(e) for e in elements)
        return _orig_listbox_insert(self, index, *elements)
    tk.Listbox.insert = _new_listbox_insert

    _orig_button_init = tk.Button.__init__
    def _new_button_init(self, master=None, cnf={}, **kw):
        if 'text' in kw: kw['text'] = _t_str(kw['text'])
        return _orig_button_init(self, master, cnf, **kw)
    tk.Button.__init__ = _new_button_init

    _orig_ttk_button_init = ttk.Button.__init__
    def _new_ttk_button_init(self, master=None, **kw):
        if 'text' in kw: kw['text'] = _t_str(kw['text'])
        return _orig_ttk_button_init(self, master, **kw)
    ttk.Button.__init__ = _new_ttk_button_init

    _orig_set = tk.StringVar.set
    def _new_set(self, value):
        return _orig_set(self, _t_str(value))
    tk.StringVar.set = _new_set

    _orig_title = tk.Toplevel.title
    def _new_title(self, title):
        return _orig_title(self, _t_str(title))
    tk.Toplevel.title = _new_title

    for msg_func in ['showinfo', 'showwarning', 'showerror', 'askyesno', 'askokcancel', 'askretrycancel', 'askyesnocancel']:
        if hasattr(messagebox, msg_func):
            _orig_func = getattr(messagebox, msg_func)
            def _make_wrapper(orig_f):
                def _new_msg(title, message, **options):
                    return orig_f(_t_str(title), _t_str(message), **options)
                return _new_msg
            setattr(messagebox, msg_func, _make_wrapper(_orig_func))

    _PATCH_INSTALLED = True

def tr(text, app_or_lang_map=None):
    global _GLOBAL_LANG_MAP
    if app_or_lang_map is not None:
        if hasattr(app_or_lang_map, 'lang_map'):
            _GLOBAL_LANG_MAP = app_or_lang_map.lang_map
        elif isinstance(app_or_lang_map, dict):
            _GLOBAL_LANG_MAP = app_or_lang_map

    _install_global_translator()

    if text in _GLOBAL_LANG_MAP:
        return _GLOBAL_LANG_MAP[text]
    return text


# ---------- AI 配置 ----------
API_KEY = ""
BASE_URL = "https://api.orcarouter.ai/v1"
MODEL = "orcarouter/free"

# ---------- 推广链接 ----------
REF_LINK = "https://www.orcarouter.ai/ref/ref_cbc36949200a20e9c814"

# ---------- AI 配置文件 ----------
AI_CONFIG_FILE = "orcarouterAI.json"

def load_ai_config():
    """加载 AI 配置，如果文件不存在则返回默认配置"""
    if os.path.exists(AI_CONFIG_FILE):
        try:
            with open(AI_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[AI配置] 加载失败: {e}")
    # 默认配置（默认只提供免费和自动路由，避免用户误以为可用付费模型）
    return {
        "api_key": API_KEY,
        "base_url": BASE_URL,
        "models": [
            {"name": "免费模型 Deepseek (OrcaRouter)", "id": "orcarouter/free"},
            {"name": "自动路由 (OrcaRouter)", "id": "orcarouter/auto"}
        ],
        "current_model": "orcarouter/free"
    }

def save_ai_config(config):
    """保存 AI 配置到文件"""
    try:
        with open(AI_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"[AI配置] 已保存到 {AI_CONFIG_FILE}")
        return True
    except Exception as e:
        print(f"[AI配置] 保存失败: {e}")
        return False

# 系统提示词
SYSTEM_PROMPT = """你是一个友好、可爱、通人情的 CZE 工程文件编辑助手。用户会用自然语言告诉你想要修改工程中的什么内容。你需要根据提供的工程 JSON 数据和项目语法说明（CZEmidiMarkdown_S.md），找出需要修改的地方，并给出精确的查找与替换方案。

你可以先简短地解释你的理解或思路，然后给出修改方案。但最终的修改方案必须按以下格式提供：

【Search】
精确的原始字符串（必须与工程文件中的内容完全一致，包括空格和换行）
【Replace】
替换后的新字符串

可以有多组这样的 Search/Replace 对。如果无法执行，请输出 【Error】: 原因。

示例：
【Search】
"window_type": "info"
【Replace】
"window_type": "warning"

【Search】
"title": "旧标题"
【Replace】
"title": "新标题"
"""
# -------------------------------------------------

def _re_module_match_sep(cell_text):
    """判断单个表格分隔单元格是否是 --- / :--- / ---: / :---: 形式"""
    import re as _re
    return bool(_re.match(r"^:?-{2,}:?$", cell_text))


def open_collaboration_dialog(app):
    """
    供主程序调用的入口函数
    app: MidiToCZE 实例
    """
    # 1. 检查是否有打开的工程
    if not app.current_project_path:
        messagebox.showwarning(tr("警告", app), tr("请先打开一个工程文件", app))
        return

    # 2. 确保工程文件存在（不强制要求保存到磁盘，改为纯内存操作）
    if not os.path.exists(app.current_project_path):
        messagebox.showerror(tr("错误", app), tr("工程文件不存在，请重新打开", app))
        return

    # 4. 单例：如果已经打开，就提到最前面，不重复创建
    existing = getattr(app, "_collaboration_dialog", None)
    if existing is not None:
        try:
            if existing.winfo_exists():
                existing.deiconify()
                existing.lift()
                existing.focus_force()
                return
        except Exception:
            pass

    # 5. 创建协作对话框（非阻塞，不调用 grab_set / mainloop）
    dialog = CollaborationDialog(app)
    # 挂到 app 上，方便下次复用 / 判断是否已经打开
    try:
        app._collaboration_dialog = dialog
    except Exception:
        pass
    # 不加 grab_set，不调用 mainloop，让它成为普通 Toplevel，
    # 用户可以随时切回主窗口。


def open_online_help_document(app):
    """打开在线帮助文档"""
    import webbrowser
    url = "https://xxdz-official.github.io/xxdz-Itoc/help/help.html"
    webbrowser.open(url)


def open_ai_model_config_dialog(app):
    """打开 AI 模型配置对话框（图形化模型列表管理，无闪烁）"""
    tr("", app)  # 触发全局翻译补丁
    dialog = tk.Toplevel(app.root)
    dialog.title("AI 模型配置")
    dialog.transient(app.root)
    dialog.grab_set()
    dialog.resizable(False, False)

    # 1. 先隐藏窗口，等所有控件和位置都算好后一次性显示，避免闪烁
    dialog.withdraw()

    # 2. 设置窗口图标
    try:
        icon_path = "img/icon.ico"
        if os.path.exists(icon_path):
            dialog.iconbitmap(icon_path)
    except Exception:
        pass

    # 3. 加载当前配置
    config = load_ai_config()
    models = config.get("models", []).copy()
    current_model_id = config.get("current_model", "")

    # 4. 计算居中位置（用主窗口的坐标，避免依赖 dialog 自己的尺寸）
    w, h = 580, 560
    screen_w = dialog.winfo_screenwidth()
    screen_h = dialog.winfo_screenheight()
    x = (screen_w - w) // 2
    y = (screen_h - h) // 2
    dialog.geometry(f"{w}x{h}+{x}+{y}")

    main_frame = ttk.Frame(dialog, padding="15")
    main_frame.pack(fill=tk.BOTH, expand=True)

    # ===== 顶部提示标签 =====
    info_label = ttk.Label(
        main_frame,
        text="Itoc默认使用免费AI模型，优点：无需登录、无限使用，\n缺点：辣鸡智商、单次token少，无法协作复杂工程。。。\n（付费模型由第三方 OrcaRouter 提供，与Itoc作者我无关，绝不强制消费）",
        font=("Microsoft YaHei", 9),
        foreground="#FF6600",
        wraplength=540,
        justify=tk.LEFT
    )
    info_label.pack(anchor=tk.W, pady=(0, 10))

    # ===== API 设置区域 =====
    api_frame = ttk.LabelFrame(main_frame, text="API 设置", padding="10")
    api_frame.pack(fill=tk.X, pady=(0, 10))

    ttk.Label(api_frame, text="API Key:").grid(row=0, column=0, sticky=tk.W, pady=2)
    key_var = tk.StringVar(value=config.get("api_key", ""))
    ttk.Entry(api_frame, textvariable=key_var, width=55).grid(row=0, column=1, padx=5, pady=2)

    ttk.Label(api_frame, text="Base URL:").grid(row=1, column=0, sticky=tk.W, pady=2)
    url_var = tk.StringVar(value=config.get("base_url", BASE_URL))
    ttk.Entry(api_frame, textvariable=url_var, width=55).grid(row=1, column=1, padx=5, pady=2)

    # ===== 模型列表区域 =====
    model_frame = ttk.LabelFrame(main_frame, text="模型列表", padding="10")
    model_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

    listbox_frame = ttk.Frame(model_frame)
    listbox_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    model_listbox = tk.Listbox(listbox_frame, font=("Microsoft YaHei", 10), height=10)
    scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=model_listbox.yview)
    model_listbox.configure(yscrollcommand=scrollbar.set)

    model_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # 模型操作按钮
    btn_frame = ttk.Frame(model_frame)
    btn_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))

    def refresh_listbox():
        model_listbox.delete(0, tk.END)
        for m in models:
            display_name = tr(m['name'], app)
            model_listbox.insert(tk.END, f"{display_name}  [{m['id']}]")

    def get_selected_model_index():
        sel = model_listbox.curselection()
        return sel[0] if sel else None

    def create_edit_sub_window(title_text, init_name="", init_id="", on_save=None):
        """通用的添加/编辑子窗口创建函数，无闪烁"""
        sub = tk.Toplevel(dialog)
        sub.title(title_text)
        sub.transient(dialog)
        sub.grab_set()
        sub.resizable(False, False)
        try:
            if os.path.exists("img/icon.ico"):
                sub.iconbitmap("img/icon.ico")
        except Exception:
            pass

        # 先隐藏，避免闪烁
        sub.withdraw()

        ttk.Label(sub, text="模型名称:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        name_var = tk.StringVar(value=init_name)
        ttk.Entry(sub, textvariable=name_var, width=30).grid(row=0, column=1, padx=10, pady=10)

        ttk.Label(sub, text="模型 ID:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        id_var = tk.StringVar(value=init_id)
        ttk.Entry(sub, textvariable=id_var, width=30).grid(row=1, column=1, padx=10, pady=10)

        def _on_ok():
            name = name_var.get().strip()
            mid = id_var.get().strip()
            if not name or not mid:
                messagebox.showwarning("提示", "名称和模型ID不能为空", parent=sub)
                return
            if on_save:
                on_save(name, mid)
            sub.destroy()

        ttk.Button(sub, text="确定", command=_on_ok).grid(row=2, column=0, columnspan=2, pady=10)

        # 计算居中位置（用 dialog 的当前位置和大小）
        sw, sh = 320, 170
        dx = dialog.winfo_x()
        dy = dialog.winfo_y()
        dw = dialog.winfo_width()
        dh = dialog.winfo_height()
        sx = dx + (dw - sw) // 2
        sy = dy + (dh - sh) // 2
        sub.geometry(f"{sw}x{sh}+{sx}+{sy}")

        # 一次性显示
        sub.deiconify()
        sub.focus_force()
        sub.wait_window(sub)

    def add_model():
        def _do_save(name, mid):
            models.append({"name": name, "id": mid})
            refresh_listbox()

        create_edit_sub_window("添加模型", "", "", _do_save)

    def edit_model():
        idx = get_selected_model_index()
        if idx is None:
            messagebox.showinfo("提示", "请先选择一个模型", parent=dialog)
            return
        m = models[idx]

        def _do_save(name, mid):
            models[idx] = {"name": name, "id": mid}
            refresh_listbox()

        create_edit_sub_window("编辑模型", m["name"], m["id"], _do_save)

    def delete_model():
        idx = get_selected_model_index()
        if idx is None:
            messagebox.showinfo("提示", "请先选择一个模型", parent=dialog)
            return
        if messagebox.askyesno("确认删除", f"确定要删除模型 {models[idx]['name']} 吗？", parent=dialog):
            models.pop(idx)
            refresh_listbox()

    ttk.Button(btn_frame, text="添加", command=add_model, width=8).pack(pady=(0, 5))
    ttk.Button(btn_frame, text="编辑", command=edit_model, width=8).pack(pady=5)
    ttk.Button(btn_frame, text="删除", command=delete_model, width=8).pack(pady=5)

    refresh_listbox()

    # ===== 当前模型选择区域 =====
    current_frame = ttk.Frame(main_frame)
    current_frame.pack(fill=tk.X, pady=(0, 10))

    ttk.Label(current_frame, text="当前模型:").pack(side=tk.LEFT, padx=(0, 5))
    current_var = tk.StringVar()
    current_combo = ttk.Combobox(current_frame, textvariable=current_var, state="readonly", width=45)
    current_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def refresh_current_combo():
        vals = [f"{tr(m['name'], app)} ({m['id']})" for m in models]
        current_combo["values"] = vals
        # 尝试匹配当前模型
        for m in models:
            if m["id"] == current_model_id:
                current_var.set(f"{tr(m['name'], app)} ({m['id']})")
                return
        if vals:
            current_var.set(vals[0])
        else:
            current_var.set("")

    refresh_current_combo()

    def save_config():
        sel = current_var.get()
        final_current_id = ""
        for m in models:
            if sel == f"{m['name']} ({m['id']})":
                final_current_id = m["id"]
                break
        if not final_current_id and models:
            final_current_id = models[0]["id"]

        new_config = {
            "api_key": key_var.get().strip(),
            "base_url": url_var.get().strip(),
            "models": models,
            "current_model": final_current_id
        }
        if save_ai_config(new_config):
            messagebox.showinfo("成功", "AI 配置已保存", parent=dialog)
            dialog.destroy()
        else:
            messagebox.showerror("错误", "保存配置失败", parent=dialog)

    # ===== 底部按钮 =====
    bottom_frame = ttk.Frame(main_frame)
    bottom_frame.pack(fill=tk.X, pady=(10, 0))

    # 左侧：购买付费模型额度按钮
    def open_buy_page():
        try:
            import webbrowser
            webbrowser.open(REF_LINK)
        except Exception as e:
            print(f"[AI配置] 打开购买页面失败: {e}")

    ttk.Button(bottom_frame, text="💎 购买付费模型额度", command=open_buy_page, width=22).pack(side=tk.LEFT)

    # 左侧：“？”帮助按钮
    def show_help():
        help_win = tk.Toplevel(dialog)
        help_win.title("如何获取第三方付费模型")
        help_win.transient(dialog)
        help_win.grab_set()
        help_win.resizable(False, False)
        try:
            if os.path.exists("img/icon.ico"):
                help_win.iconbitmap("img/icon.ico")
        except Exception:
            pass
        help_win.withdraw()

        ttk.Label(help_win, text="如何获取第三方付费模型？", font=("Microsoft YaHei", 12, "bold")).pack(pady=10)
        help_text = (
            "声明：本软件（Itoc）为完全免费、用爱发电的项目哦，此AI功能仅为额外附加选项喵\n"
            "💡 此合作由 OrcaRouter 官方主动邀请发起，详情可见下方B站动态按钮哦～\n\n"
            "1. 点击下方“💎 购买付费模型额度”按钮，跳转到第三方提供商 OrcaRouter 官网\n"
            "2. 注册/登录你的 OrcaRouter 账号。\n"
            "3. 在控制台充值或绑定你自己的 API Key（BYOK）。\n"
            "   （注：定价、充值及服务质量均由第三方 OrcaRouter 官方提供，非本软件作者收费）\n"
            "4. 回到本软件，点击“添加”，输入你购买的模型名称和 ID\n"
            "5. 保存配置后，就可以在对话窗口切换使用啦！\n\n"
            "注：免费模型不需要充值，但智商较低，仅适合简单任务。您完全可以选择跳过此配置，不影响核心功能的使用"
        )
        ttk.Label(help_win, text=help_text, justify=tk.LEFT, padding=10).pack()

        # 合作邀请说明
        invite_frame = ttk.Frame(help_win)
        invite_frame.pack(fill=tk.X, padx=15, pady=(0, 5))
        ttk.Label(
            invite_frame,
            text="💡 此合作由 OrcaRouter 官方主动邀请发起，详情可见我的B站动态：",
            font=("Microsoft YaHei", 9),
            foreground="#666666",
            justify=tk.LEFT,
            wraplength=440
        ).pack(anchor=tk.W)

        def open_invite_link():
            import webbrowser
            webbrowser.open("https://www.bilibili.com/opus/1242272823153524740")

        ttk.Button(
            invite_frame,
            text="📄 查看 OrcaRouter 官方邀请详情",
            command=open_invite_link,
            width=32
        ).pack(anchor=tk.W, pady=(3, 0))

        ttk.Button(help_win, text="欧了", command=help_win.destroy).pack(pady=10)

        help_win.update_idletasks()
        hw, hh = 480, 380
        dx, dy = dialog.winfo_x(), dialog.winfo_y()
        dw, dh = dialog.winfo_width(), dialog.winfo_height()
        help_win.geometry(f"{hw}x{hh}+{dx + (dw - hw) // 2}+{dy + (dh - hh) // 2}")
        help_win.deiconify()
        help_win.wait_window(help_win)

    ttk.Button(bottom_frame, text="?", command=show_help, width=3).pack(side=tk.LEFT, padx=(5, 0))

    # 右侧：保存/取消
    ttk.Button(bottom_frame, text="保存", command=save_config, width=10).pack(side=tk.RIGHT, padx=5)
    ttk.Button(bottom_frame, text="取消", command=dialog.destroy, width=10).pack(side=tk.RIGHT)

    # 5. 所有控件和位置准备就绪后，一次性显示窗口
    dialog.deiconify()
    dialog.focus_force()
    dialog.wait_window(dialog)


def open_dianzi_ai_assistant(app):
    """打开電籽AI助手对话框（非独占，主窗口可继续操作）"""
    tr("", app)  # 触发全局翻译补丁
    # 顺便通知主程序刷新一下主菜单的语言映射
    if hasattr(app, 'apply_language_mapping'):
        try:
            app.apply_language_mapping()
        except Exception:
            pass
    # 单例：如果已经打开，就提到最前面，不重复创建
    existing = getattr(app, "_dianzi_ai_dialog", None)
    if existing is not None:
        try:
            if existing.winfo_exists():
                existing.deiconify()
                existing.lift()
                existing.focus_force()
                return
        except Exception:
            pass
    dialog = DianZiAIAssistantDialog(app)
    # 挂到 app 上，方便下次复用 / 判断是否已经打开
    try:
        app._dianzi_ai_dialog = dialog
    except Exception:
        pass
    # 不加 grab_set，不调用 mainloop，让它成为普通 Toplevel，
    # 用户可以随时切回主窗口。


class DianZiAIAssistantDialog(tk.Toplevel):
    """電籽AI助手对话框（气泡聊天风格）"""

    # 颜色方案
    BG_COLOR = "#F5F7FA"           # 整体背景
    USER_BUBBLE_BG = "#E8F4FD"     # 用户气泡背景
    USER_BUBBLE_BORDER = "#C8D8E8"
    USER_TEXT_COLOR = "#1A2A3A"
    AI_BUBBLE_BG = "#FFFFFF"       # 電籽气泡背景
    AI_BUBBLE_BORDER = "#D0D7DE"
    AI_TEXT_COLOR = "#222222"
    INPUT_BG = "#FFFFFF"
    INPUT_BORDER = "#D0D7DE"
    SEND_BTN_BG = "#0C8CE9"        # 发送按钮
    SEND_BTN_HOVER = "#0A7CCE"
    SEND_BTN_ACTIVE = "#085FB0"
    TITLE_COLOR = "#1A5A8A"
    STATUS_COLOR = "#666666"

    def __init__(self, app):
        super().__init__(app.root)
        self.app = app
        self.title("電籽AI助手")
        self.resizable(True, True)
        self.minsize(480, 420)
        self.configure(bg=self.BG_COLOR)

        # ===== 关键：先 withdraw 隐藏，等所有控件和位置都算好后再 deiconify =====
        self.withdraw()

        # 设置图标
        try:
            self.iconbitmap("img/icon.ico")
        except:
            pass

        # 计算居中位置（不立刻 geometry，只保存）
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        w, h = 640, 580
        x = (screen_width - w) // 2
        y = (screen_height - h) // 2
        self._initial_geometry = f"{w}x{h}+{x}+{y}"

        # 系统提示词：优先从同目录下的 DianZiAI.md 读取
        _dianzi_md_path = os.path.join(os.path.dirname(__file__), "DianZiAI.md")
        if os.path.exists(_dianzi_md_path):
            try:
                with open(_dianzi_md_path, "r", encoding="utf-8") as _f:
                    self.system_prompt = _f.read().strip()
                print("[電籽AI] 已从 DianZiAI.md 加载系统提示词")
            except Exception as _e:
                print(f"[電籽AI] 读取 DianZiAI.md 失败，使用内置提示词: {_e}")
                self.system_prompt = "你是 xxdz Itoc 中的 AI 助手，名叫「電籽」。你是萌系小狼，性格活泼可爱，回答简洁清晰，可以加些颜文字。"
        else:
            print("[電籽AI] 未找到 DianZiAI.md，使用内置提示词")
            self.system_prompt = "你是 xxdz Itoc 中的 AI 助手，名叫「電籽」。你是萌系小狼，性格活泼可爱，回答简洁清晰，可以加些颜文字。"

        # 加载 AI 配置
        self.ai_config = load_ai_config()

        # 消息列表（用于构建对话上下文）
        self.messages = [{"role": "system", "content": self.system_prompt}]

        # 待发送的引用（key: 'project' | 'selected_notes' | 'time_selection'）
        self._references = {}

        # 头像图片引用
        self._ai_avatar_img = None
        self._user_avatar_img = None
        self._load_avatars()

        # 打字机相关
        self._typewriter_queue = []
        self._typewriter_bubble_widget = None
        self._typewriter_label = None
        self._typewriter_timer = None
        self._typewriter_full_text = ""   # 保存打字机原始 MD 文本，打完重新渲染用
        self._md_refresh_timer = None     # 打字过程中每秒 MD 渲染的定时器

        self._thinking_bubble_row = None
        self._thinking_dots = []
        self._thinking_dot_index = 0
        self._thinking_anim_timer = None

        self._create_widgets()


        self.protocol("WM_DELETE_WINDOW", self._on_dialog_close)


        self.geometry(self._initial_geometry)
        self.update_idletasks()
        self.deiconify()
        self.lift()
        self.focus_force()
        self.input_text.focus_set()

    def _on_dialog_close(self):
        """关闭对话框：清理 app 上挂的引用，然后销毁自己"""
        try:
            self._references = {}
        except Exception:
            pass
        try:
            if getattr(self.app, "_dianzi_ai_dialog", None) is self:
                self.app._dianzi_ai_dialog = None
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass

    def _toggle_topmost(self):
        """切换窗口置顶状态"""
        try:
            self._is_topmost = not self._is_topmost
            self.attributes("-topmost", self._is_topmost)
            self._update_topmost_btn_color()
            if self._is_topmost:
                self.lift()
        except Exception as _e:
            print(f"[電籽AI] 切换置顶失败: {_e}")

    def _update_topmost_btn_color(self):
        """根据当前置顶状态更新按钮颜色"""
        try:
            if getattr(self, "_is_topmost", False):
                self.topmost_btn.config(fg="#0C8CE9")
            else:
                self.topmost_btn.config(fg="#999999")
        except Exception:
            pass

    def _load_avatars(self):
        """尝试加载头像图片（電籽：img/DianZilogo.png；用户：noface.png）"""
        try:
            from PIL import Image, ImageTk
            base_dir = os.path.dirname(os.path.abspath(__file__))

            # 電籽头像：优先 img/DianZilogo.png，其次几个兼容路径
            ai_candidates = [
                os.path.join(base_dir, "img", "DianZilogo.png"),
                os.path.join(base_dir, "img", "DianZiLogo.png"),
                os.path.join(base_dir, "DianZilogo.png"),
            ]
            for p in ai_candidates:
                if os.path.exists(p):
                    try:
                        img = Image.open(p).convert("RGBA").resize((36, 36), Image.LANCZOS)
                        self._ai_avatar_img = ImageTk.PhotoImage(img)
                        print(f"[電籽AI] 已加载電籽头像: {p}")
                        break
                    except Exception as _e:
                        print(f"[電籽AI] 加载電籽头像失败 {p}: {_e}")
                        continue

            # 用户头像：noface.png
            user_candidates = [
                os.path.join(base_dir, "noface.png"),
                os.path.join(base_dir, "img", "noface.png"),
            ]
            for p in user_candidates:
                if os.path.exists(p):
                    try:
                        img = Image.open(p).convert("RGBA").resize((36, 36), Image.LANCZOS)
                        self._user_avatar_img = ImageTk.PhotoImage(img)
                        print(f"[電籽AI] 已加载用户头像: {p}")
                        break
                    except Exception as _e:
                        print(f"[電籽AI] 加载用户头像失败 {p}: {_e}")
                        continue
        except Exception as e:
            print(f"[電籽AI] 加载头像失败: {e}")

    def _create_widgets(self):
        # ============ 主容器 ============
        outer = tk.Frame(self, bg=self.BG_COLOR)
        outer.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ---- 标题行 ----
        title_bar = tk.Frame(outer, bg=self.BG_COLOR)
        title_bar.pack(fill=tk.X, pady=(0, 8))

        # 标题小图标（如果加载到了電籽头像，顺便复用）
        if self._ai_avatar_img is not None:
            try:
                icon_lbl = tk.Label(title_bar, image=self._ai_avatar_img, bg=self.BG_COLOR)
                icon_lbl.pack(side=tk.LEFT, padx=(0, 6))
            except Exception:
                pass

        title_label = tk.Label(
            title_bar, text="与電籽聊天",
            font=("Microsoft YaHei", 13, "bold"),
            bg=self.BG_COLOR, fg=self.TITLE_COLOR
        )
        title_label.pack(side=tk.LEFT)

        # ---- 标题栏右侧：置顶按钮 ----
        self._is_topmost = False

        self.topmost_btn = tk.Label(
            title_bar, text="📌",
            font=("Microsoft YaHei", 12),
            bg=self.BG_COLOR, fg="#999999",
            padx=6, pady=2,
            cursor="hand2",
        )
        self.topmost_btn.pack(side=tk.RIGHT, padx=(4, 0))
        self.topmost_btn.bind("<Button-1>", lambda e: self._toggle_topmost())
        self.topmost_btn.bind("<Enter>", lambda e: self.topmost_btn.config(fg="#0C8CE9"))
        self.topmost_btn.bind("<Leave>", lambda e: self._update_topmost_btn_color())

        # ---- 模型选择栏 ----
        model_bar = tk.Frame(outer, bg=self.BG_COLOR)
        model_bar.pack(fill=tk.X, pady=(2, 0))
        tk.Label(model_bar, text="模型：", font=("Microsoft YaHei", 9), bg=self.BG_COLOR, fg="#666666").pack(side=tk.LEFT)
        self.model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(model_bar, textvariable=self.model_var, state="readonly", width=30)
        self.model_combo.pack(side=tk.LEFT, padx=(0, 10))
        # 填充模型列表
        models = self.ai_config.get("models", [])
        model_display = [f"{m['name']} ({m['id']})" for m in models]
        self.model_combo["values"] = model_display
        # 设置当前模型
        current_id = self.ai_config.get("current_model", "")
        for m in models:
            if m['id'] == current_id:
                self.model_var.set(f"{m['name']} ({m['id']})")
                break
        if not self.model_var.get() and model_display:
            self.model_var.set(model_display[0])

        def on_model_change(event=None):
            """切换模型时更新配置"""
            sel = self.model_var.get()
            for m in models:
                if sel == f"{m['name']} ({m['id']})":
                    self.ai_config["current_model"] = m['id']
                    save_ai_config(self.ai_config)
                    print(f"[AI助手] 切换模型为: {m['id']}")
                    break
        self.model_combo.bind("<<ComboboxSelected>>", on_model_change)

        # ---- 分隔线 ----
        tk.Frame(outer, bg="#D0D7DE", height=1).pack(fill=tk.X)

        # ============ 对话滚动区 ============
        # 用 Canvas + 内嵌 Frame 模拟 QScrollArea 的气泡效果
        chat_outer = tk.Frame(outer, bg=self.BG_COLOR)
        chat_outer.pack(fill=tk.BOTH, expand=True, pady=(8, 8))

        self.chat_canvas = tk.Canvas(
            chat_outer, bg=self.BG_COLOR,
            highlightthickness=0, bd=0
        )
        self.chat_scrollbar = ttk.Scrollbar(chat_outer, orient="vertical", command=self.chat_canvas.yview)
        self.chat_canvas.configure(yscrollcommand=self.chat_scrollbar.set)

        # 让滚动条动态贴右边，Canvas 占满剩余空间
        self.chat_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 内嵌的内容 Frame
        self.chat_inner = tk.Frame(self.chat_canvas, bg=self.BG_COLOR)
        self._chat_window_id = self.chat_canvas.create_window(
            (0, 0), window=self.chat_inner, anchor="nw"
        )

        # 内容变化时更新滚动区域
        self.chat_inner.bind("<Configure>", self._on_chat_inner_configure)
        self.chat_canvas.bind("<Configure>", self._on_chat_canvas_configure)
        # 鼠标滚轮
        self.chat_canvas.bind("<MouseWheel>", self._on_chat_mousewheel)
        self.chat_inner.bind("<MouseWheel>", self._on_chat_mousewheel)

        # 欢迎语
        self._append_ai_bubble(
            "尼好丫~ 咱是電籽，有啥关于 Itoc 的问题都可以问咱哦 (´▽`ʃ♡)ƪ",
            typing=False
        )

        # ============ 待发送引用区（按钮行 + 卡片区） ============
        self._init_reference_area(outer)

        # ============ 状态栏（最底部） ============
        self.status_var = tk.StringVar(value="就绪")
        status_label = tk.Label(
            outer, textvariable=self.status_var,
            font=("Microsoft YaHei", 9),
            bg=self.BG_COLOR, fg=self.STATUS_COLOR,
            anchor=tk.W
        )
        status_label.pack(fill=tk.X, side=tk.BOTTOM, pady=(6, 0))

        # ============ 输入区（倒数第二） ============
        # 用 pack 布局：input_outer 水平铺满，内部 Text 用 fill/expand 动态跟随
        input_outer = tk.Frame(outer, bg=self.BG_COLOR)
        input_outer.pack(fill=tk.X, side=tk.BOTTOM)

        # 发送按钮固定宽度放在右边（先 pack 右边，确保不被挤压）
        self.send_btn = tk.Button(
            input_outer, text="发送",
            font=("Microsoft YaHei", 10, "bold"),
            bg=self.SEND_BTN_BG, fg="#FFFFFF",
            activebackground=self.SEND_BTN_ACTIVE, activeforeground="#FFFFFF",
            relief=tk.FLAT, bd=0, padx=18, pady=10,
            cursor="hand2",
            width=6,
            command=self._send_message
        )
        self.send_btn.pack(side=tk.RIGHT, fill=tk.Y, padx=(6, 0))
        self.send_btn.bind("<Enter>", lambda e: self.send_btn.config(bg=self.SEND_BTN_HOVER))
        self.send_btn.bind("<Leave>", lambda e: self.send_btn.config(bg=self.SEND_BTN_BG))

        # 输入框（带边框容器）填满剩下的空间
        input_border = tk.Frame(input_outer, bg=self.INPUT_BORDER)
        input_border.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.input_text = tk.Text(
            input_border, height=3, wrap=tk.WORD,
            font=("Microsoft YaHei", 10),
            bg=self.INPUT_BG, fg="#222222",
            relief=tk.FLAT, bd=0,
            highlightthickness=0,
            insertbackground="#0C8CE9",
            padx=8, pady=6
        )
        self.input_text.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        # 回车发送、Shift+回车换行
        self.input_text.bind("<Return>", self._on_enter)
        self.input_text.bind("<Shift-Return>", lambda e: None)
        # 输入时自动调整高度（3~8 行）
        self.input_text.bind("<KeyRelease>", self._auto_resize_input)

    # ---------- 滚动区相关 ----------
    def _on_chat_inner_configure(self, event=None):
        """内容 Frame 大小变化时，更新 Canvas 滚动区域"""
        try:
            self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all"))
        except Exception:
            pass

    def _on_chat_canvas_configure(self, event):
        """Canvas 大小变化时，让内嵌 Frame 宽度跟随"""
        try:
            self.chat_canvas.itemconfig(self._chat_window_id, width=event.width)
        except Exception:
            pass

    def _on_chat_mousewheel(self, event):
        """鼠标滚轮滚动对话区（每次滚 5 行）"""
        try:
            delta = -1 if event.delta > 0 else 1
            self.chat_canvas.yview_scroll(delta * 5, "units")
        except Exception:
            pass

    def _bind_wheel_recursive(self, widget):
        """递归给控件及其所有子控件绑定滚轮事件（已有绑定则不重复）"""
        try:
            if getattr(widget, "_wheel_bound", False):
                return
            widget._wheel_bound = True
            widget.bind("<MouseWheel>", self._on_chat_mousewheel, add="+")
        except Exception:
            pass
        try:
            for child in widget.winfo_children():
                self._bind_wheel_recursive(child)
        except Exception:
            pass

    def _scroll_chat_to_bottom(self):
        """滚动到底部"""
        try:
            self.chat_canvas.update_idletasks()
            self.chat_canvas.yview_moveto(1.0)
        except Exception:
            pass

    # ---------- 气泡相关 ----------
    def _append_user_bubble(self, text):
        """添加用户气泡（靠右）"""
        self._append_bubble(text, is_user=True)

    def _append_ai_bubble(self, text, typing=False):
        """添加電籽气泡（靠左）。typing=True 时启动打字机效果"""
        if typing:
            return self._append_ai_bubble_typing(text)
        return self._append_bubble(text, is_user=False)

    def _append_bubble(self, text, is_user):
        """通用的气泡渲染（头像优先使用真实图片，文本可选中复制）"""
        row = tk.Frame(self.chat_inner, bg=self.BG_COLOR)
        row.pack(fill=tk.X, pady=4, padx=4)

        # ---- 头像：优先真实图片，没有则退回到文字 ----
        avatar_kwargs = dict(bd=0, relief=tk.FLAT, bg=self.BG_COLOR)
        if is_user:
            if getattr(self, "_user_avatar_img", None) is not None:
                avatar = tk.Label(row, image=self._user_avatar_img, **avatar_kwargs)
            else:
                avatar = tk.Label(
                    row, text="你",
                    font=("Microsoft YaHei", 11, "bold"),
                    bg="#C8D8E8", fg="#1A2A3A",
                    width=2, height=1,
                    bd=0, relief=tk.FLAT
                )
        else:
            if getattr(self, "_ai_avatar_img", None) is not None:
                avatar = tk.Label(row, image=self._ai_avatar_img, **avatar_kwargs)
            else:
                avatar = tk.Label(
                    row, text="電",
                    font=("Microsoft YaHei", 11, "bold"),
                    bg="#0C8CE9", fg="#FFFFFF",
                    width=2, height=1,
                    bd=0, relief=tk.FLAT
                )

        # ---- 气泡 ----
        bubble_bg = self.USER_BUBBLE_BG if is_user else self.AI_BUBBLE_BG
        bubble_border = self.USER_BUBBLE_BORDER if is_user else self.AI_BUBBLE_BORDER
        text_color = self.USER_TEXT_COLOR if is_user else self.AI_TEXT_COLOR

        # 用 Text 代替 Label，支持选中复制
        bubble_wrap = tk.Frame(row, bg=bubble_border, bd=0)
        bubble = tk.Text(
            bubble_wrap,
            font=("Microsoft YaHei", 10),
            bg=bubble_bg, fg=text_color,
            relief=tk.FLAT, bd=0,
            highlightthickness=0,
            wrap=tk.WORD,
            padx=12, pady=8,
            cursor="arrow",
            height=1, width=30,
            takefocus=0,
        )
        # 先注册 Markdown tag，再用 Markdown 渲染塞内容
        self._setup_md_tags(bubble, bubble_bg)
        self._render_markdown_into(bubble, text)
        bubble.config(state=tk.DISABLED)
        bubble.pack(padx=1, pady=1)

        # 禁用气泡内部滚轮滚动，让外层 Canvas 接管
        self._disable_text_scroll(bubble)

        # 让气泡随窗口宽度动态换行 + 自适应高度
        bubble.bind("<Configure>", lambda e, b=bubble: self._adjust_bubble_wrap(b))
        # ===== 多时间点刷新高度，确保末尾文本完整显示 =====
        self._schedule_height_refresh(bubble)

        if is_user:
            # 用户：气泡在左，头像在最右
            # 注意：side=RIGHT 是从右往左叠，所以必须先 pack 头像（贴最右），
            # 再 pack 气泡（自然落在头像左边）
            avatar.pack(side=tk.RIGHT, anchor=tk.NE, padx=(6, 0))
            bubble_wrap.pack(side=tk.RIGHT, anchor=tk.NE, padx=(40, 6))
        else:

            avatar.pack(side=tk.LEFT, anchor=tk.NW, padx=(0, 2))
            bubble_wrap.pack(side=tk.LEFT, anchor=tk.NW, padx=(6, 40))


        self._bind_wheel_recursive(row)

        self._scroll_chat_to_bottom()
        return bubble

    def _setup_md_tags(self, text_widget, base_bg):
        """为 Text 控件注册 Markdown 渲染用到的 tag"""
        try:
            text_widget.tag_configure(
                "md_bold",
                font=("Microsoft YaHei", 10, "bold"),
            )
            text_widget.tag_configure(
                "md_italic",
                font=("Microsoft YaHei", 10, "italic"),
            )
            text_widget.tag_configure(
                "md_bold_italic",
                font=("Microsoft YaHei", 10, "bold", "italic"),
            )
            text_widget.tag_configure(
                "md_code",
                font=("Microsoft YaHei", 10),
                background="#F0F2F5",
                foreground="#C7254E",
            )
            text_widget.tag_configure(
                "md_code_block",
                font=("Microsoft YaHei", 10),
                background="#F6F8FA",
                foreground="#24292E",
                lmargin1=12, lmargin2=12,
                spacing1=2, spacing3=2,
            )
            text_widget.tag_configure(
                "md_h1",
                font=("Microsoft YaHei", 15, "bold"),
                foreground="#1A5A8A",
                spacing1=6, spacing3=4,
            )
            text_widget.tag_configure(
                "md_h2",
                font=("Microsoft YaHei", 13, "bold"),
                foreground="#1A5A8A",
                spacing1=5, spacing3=3,
            )
            text_widget.tag_configure(
                "md_h3",
                font=("Microsoft YaHei", 11, "bold"),
                foreground="#1A5A8A",
                spacing1=4, spacing3=2,
            )
            text_widget.tag_configure(
                "md_list",
                lmargin1=20, lmargin2=32,
                spacing1=1, spacing3=1,
            )
            text_widget.tag_configure(
                "md_hr",
                foreground="#D0D7DE",
                spacing1=4, spacing3=4,
            )
            text_widget.tag_configure(
                "md_link",
                foreground="#0C8CE9",
                underline=True,
            )
            # 链接悬停时颜色加深一点，视觉反馈
            text_widget.tag_configure(
                "md_link_hover",
                foreground="#085FB0",
                underline=True,
            )
            text_widget.tag_configure(
                "md_plain",
                font=("Microsoft YaHei", 10),
            )
            # ===== 表格相关 tag =====
            text_widget.tag_configure(
                "md_table_cell",
                font=("Microsoft YaHei", 10),
                lmargin1=4, lmargin2=4,
                spacing1=2, spacing3=2,
            )
            text_widget.tag_configure(
                "md_table_header",
                font=("Microsoft YaHei", 10, "bold"),
                foreground="#1A5A8A",
                lmargin1=4, lmargin2=4,
                spacing1=2, spacing3=2,
            )
            text_widget.tag_configure(
                "md_table_sep",
                font=("Microsoft YaHei", 10),
                foreground="#B0B8C0",
                lmargin1=4, lmargin2=4,
                spacing1=1, spacing3=1,
            )
        except Exception as _e:
            print(f"[電籽AI] 注册 Markdown tag 失败: {_e}")

    def _render_markdown_into(self, text_widget, md_text):
        """把 Markdown 文本渲染到 Text 控件里（支持粗体/斜体/代码/标题/列表/分割线/表格）"""
        import re as _re

        text_widget.config(state=tk.NORMAL)
        text_widget.delete("1.0", tk.END)

        # ---------- 1. 先切分代码块（``` ... ```） ----------
        code_block_pattern = _re.compile(r"```[a-zA-Z0-9_+-]*\n(.*?)```", _re.DOTALL)
        segments = []
        last_end = 0
        for m in code_block_pattern.finditer(md_text):
            if m.start() > last_end:
                segments.append((False, md_text[last_end:m.start()]))
            segments.append((True, m.group(1)))
            last_end = m.end()
        if last_end < len(md_text):
            segments.append((False, md_text[last_end:]))

        # ---------- 2. 逐段渲染 ----------
        for is_code, content in segments:
            if is_code:
                text_widget.insert(tk.END, content, "md_code_block")
                if not content.endswith("\n"):
                    text_widget.insert(tk.END, "\n", "md_code_block")
            else:
                self._render_plain_md_segment(text_widget, content)

        text_widget.config(state=tk.DISABLED)

        # ===== 渲染完用多时间点刷新高度，保证完整显示 =====
        try:
            self._schedule_height_refresh(text_widget)
        except Exception:
            pass

    def _render_plain_md_segment(self, text_widget, segment):
        """渲染非代码块部分：按行处理标题/列表/分割线/表格，再处理行内粗体/斜体/代码"""
        import re as _re

        lines = segment.split("\n")
        i = 0
        n = len(lines)
        while i < n:
            line = lines[i]

            # ===== 表格检测：当前行有 |，下一行是分隔行（|---|） =====
            if ("|" in line) and (i + 1 < n) and self._is_md_table_separator(lines[i + 1]):
                # 收集表格所有行
                table_lines = [line, lines[i + 1]]
                j = i + 2
                while j < n and "|" in lines[j] and lines[j].strip():
                    table_lines.append(lines[j])
                    j += 1
                self._render_md_table(text_widget, table_lines)
                i = j
                continue

            # 标题
            m = _re.match(r"^(#{1,6})\s+(.*)$", line)
            if m:
                level = len(m.group(1))
                content = m.group(2)
                tag = "md_h1" if level == 1 else ("md_h2" if level == 2 else "md_h3")
                self._insert_inline_md(text_widget, content, base_tags=(tag,))
                text_widget.insert(tk.END, "\n")
                i += 1
                continue

            # 分割线
            if _re.match(r"^\s*([-*_])\1{2,}\s*$", line):
                text_widget.insert(tk.END, "─" * 40 + "\n", "md_hr")
                i += 1
                continue

            # 无序列表
            m = _re.match(r"^(\s*)[-*+]\s+(.*)$", line)
            if m:
                indent = len(m.group(1))
                content = m.group(2)
                bullet = "  " * (indent // 2) + "• "
                text_widget.insert(tk.END, bullet, "md_list")
                self._insert_inline_md(text_widget, content, base_tags=("md_list",))
                text_widget.insert(tk.END, "\n")
                i += 1
                continue

            # 有序列表
            m = _re.match(r"^(\s*)(\d+)\.\s+(.*)$", line)
            if m:
                indent = len(m.group(1))
                num = m.group(2)
                content = m.group(3)
                bullet = "  " * (indent // 2) + f"{num}. "
                text_widget.insert(tk.END, bullet, "md_list")
                self._insert_inline_md(text_widget, content, base_tags=("md_list",))
                text_widget.insert(tk.END, "\n")
                i += 1
                continue

            # 普通段落
            self._insert_inline_md(text_widget, line, base_tags=("md_plain",))
            if i != n - 1:
                text_widget.insert(tk.END, "\n")
            i += 1

    def _is_md_table_separator(self, line):
        """判断是否是 Markdown 表格分隔行，如 |---|---| 或 |:---:|:--|"""
        s = line.strip()
        if not s or "|" not in s:
            return False
        # 去掉首尾 |，再按 | 切
        inner = s.strip("|").strip()
        if not inner:
            return False
        cells = inner.split("|")
        for c in cells:
            c2 = c.strip()
            if not c2:
                return False
            if not _re_module_match_sep(c2):
                return False
        return True

    def _render_md_table(self, text_widget, table_lines):
        """把 Markdown 表格渲染到 Text（用等宽对齐，视觉上像表格）"""
        import re as _re

        if len(table_lines) < 2:
            return

        def _split_cells(row):
            s = row.strip()
            if s.startswith("|"):
                s = s[1:]
            if s.endswith("|"):
                s = s[:-1]
            return [c.strip() for c in s.split("|")]

        header_cells = _split_cells(table_lines[0])
        body_rows = []
        for r in table_lines[2:]:
            body_rows.append(_split_cells(r))

        col_count = len(header_cells)
        if col_count == 0:
            return

        # 计算每列显示宽度（按字符宽度估算，中文按 2 个宽度算）
        def _visual_width(s):
            w = 0
            for ch in s:
                w += 2 if ord(ch) > 0x2E80 else 1
            return w

        all_rows = [header_cells] + body_rows
        col_widths = [0] * col_count
        for row in all_rows:
            for c_i in range(col_count):
                cell = row[c_i] if c_i < len(row) else ""
                w = _visual_width(cell)
                if w > col_widths[c_i]:
                    col_widths[c_i] = w

        def _pad(s, target_w):
            w = _visual_width(s)
            return s + (" " * max(0, target_w - w))

        # 顶部线
        top_line = "┌" + "┬".join("─" * (w + 2) for w in col_widths) + "┐"
        text_widget.insert(tk.END, top_line + "\n", "md_table_sep")

        # 表头
        header_line = "│"
        for c_i, cell in enumerate(header_cells):
            header_line += " " + _pad(cell, col_widths[c_i]) + " │"
        # 表头用 md_table_header
        text_widget.insert(tk.END, header_line + "\n", "md_table_header")

        # 表头分隔
        sep_line = "├" + "┼".join("─" * (w + 2) for w in col_widths) + "┤"
        text_widget.insert(tk.END, sep_line + "\n", "md_table_sep")

        # 数据行
        for row in body_rows:
            row_line = "│"
            for c_i in range(col_count):
                cell = row[c_i] if c_i < len(row) else ""
                row_line += " " + _pad(cell, col_widths[c_i]) + " │"
            # 数据行用 md_table_cell（走一遍 inline md 处理加粗/代码）
            # 先插入左侧边框
            text_widget.insert(tk.END, "│ ", "md_table_cell")
            for c_i in range(col_count):
                cell = row[c_i] if c_i < len(row) else ""
                self._insert_inline_md(text_widget, cell, base_tags=("md_table_cell",))
                if c_i != col_count - 1:
                    text_widget.insert(tk.END, " │ ", "md_table_cell")
            text_widget.insert(tk.END, " │\n", "md_table_cell")

        # 底部线
        bottom_line = "└" + "┴".join("─" * (w + 2) for w in col_widths) + "┘"
        text_widget.insert(tk.END, bottom_line + "\n", "md_table_sep")

        # 表格后补一个换行，避免和后面内容贴太近
        text_widget.insert(tk.END, "\n", "md_plain")

    def _insert_inline_md(self, text_widget, text, base_tags=()):
        """处理行内 Markdown：**粗体**、*斜体*、`代码`、[链接](url)"""
        import re as _re

        if not text:
            return

        # 用正则一次性匹配 行内代码 / 粗体 / 斜体 / 链接
        # 顺序很重要：行内代码优先（避免内部 ** 被解析）
        pattern = _re.compile(
            r"(`[^`]+`)"                 # 1: 行内代码
            r"|(\*\*\*[^*]+\*\*\*)"      # 2: 粗斜体
            r"|(\*\*[^*]+\*\*)"          # 3: 粗体
            r"|(\*[^*]+\*)"              # 4: 斜体
            r"|(\[[^\]]+\]\([^\)]+\))"    # 5: 链接
        )

        pos = 0
        for m in pattern.finditer(text):
            if m.start() > pos:
                text_widget.insert(tk.END, text[pos:m.start()], base_tags)

            token = m.group(0)
            if m.group(1):  # 行内代码
                inner = token[1:-1]
                text_widget.insert(tk.END, inner, tuple(base_tags) + ("md_code",))
            elif m.group(2):  # 粗斜体
                inner = token[3:-3]
                text_widget.insert(tk.END, inner, tuple(base_tags) + ("md_bold_italic",))
            elif m.group(3):  # 粗体
                inner = token[2:-2]
                text_widget.insert(tk.END, inner, tuple(base_tags) + ("md_bold",))
            elif m.group(4):  # 斜体
                inner = token[1:-1]
                text_widget.insert(tk.END, inner, tuple(base_tags) + ("md_italic",))
            elif m.group(5):  # 链接
                # [文本](url) -> 只显示文本，并打上 md_link + 记录 url
                lm = _re.match(r"\[([^\]]+)\]\(([^\)]+)\)", token)
                if lm:
                    label = lm.group(1)
                    url = lm.group(2).strip()
                    # 生成一个唯一 tag，用于记录 url 和绑定事件
                    link_tag = f"md_link_{id(url)}_{m.start()}"
                    try:
                        text_widget.tag_configure(
                            link_tag,
                            foreground="#0C8CE9",
                            underline=True,
                        )
                    except Exception:
                        pass
                    # 插入文本并同时打上通用 + 专属 tag
                    start_index = text_widget.index(tk.END)
                    text_widget.insert(tk.END, label,
                                       tuple(base_tags) + ("md_link", link_tag))
                    end_index = text_widget.index(tk.END)
                    # 记录 url，绑定点击 / 悬停 / 离开
                    self._bind_link_tag(text_widget, link_tag, url, start_index, end_index)
                else:
                    text_widget.insert(tk.END, token, base_tags)

            pos = m.end()

        if pos < len(text):
            text_widget.insert(tk.END, text[pos:], base_tags)

    def _bind_link_tag(self, text_widget, link_tag, url, start_index, end_index):
        """给一个链接 tag 绑定点击 / 悬停 / 离开事件，实现点击跳浏览器"""
        import webbrowser

        def _on_click(event, _url=url):
            try:
                webbrowser.open(_url)
            except Exception as _e:
                print(f"[電籽AI] 打开链接失败: {_url}, {_e}")
            return "break"  # 阻止 Text 默认的拖选行为

        def _on_enter(event, _tag=link_tag):
            try:
                text_widget.config(cursor="hand2")
            except Exception:
                pass
            return "break"

        def _on_leave(event, _tag=link_tag):
            try:
                text_widget.config(cursor="arrow")
            except Exception:
                pass
            return "break"

        try:
            text_widget.tag_bind(link_tag, "<Button-1>", _on_click)
            text_widget.tag_bind(link_tag, "<Enter>", _on_enter)
            text_widget.tag_bind(link_tag, "<Leave>", _on_leave)
        except Exception as _e:
            print(f"[電籽AI] 绑定链接事件失败: {_e}")

    def _auto_bubble_height(self, bubble):
        """根据内容自动调整 Text 气泡高度（保证所有文本完整显示）"""
        try:
            if bubble is None:
                return
            try:
                if not bubble.winfo_exists():
                    return
            except Exception:
                return

            bubble.update_idletasks()

            # ===== 优先用 displaylines 精确计算视觉行数（含自动换行） =====
            line_count = None
            try:
                res = bubble.count("1.0", "end-1c", "displaylines")
                # count() 返回可能是 tuple/list，也可能是单个 int
                if isinstance(res, (list, tuple)):
                    line_count = int(res[0]) if res else 0
                else:
                    line_count = int(res)
            except Exception:
                line_count = None

            # 兜底：按逻辑行数算
            if not line_count or line_count < 1:
                try:
                    line_count = int(bubble.index("end-1c").split(".")[0])
                except Exception:
                    line_count = 1

            if line_count < 1:
                line_count = 1

            # ===== 关键：displaylines 不计入"末尾换行符导致的空行"，
            #       再补 1 行余量，确保底部不被截断 =====
            line_count += 1

            # 避免无意义重复设置（防止死循环触发 Configure）
            try:
                cur_h = int(bubble.cget("height"))
            except Exception:
                cur_h = -1
            if cur_h != line_count:
                bubble.config(height=line_count)
        except Exception:
            pass

    def _schedule_height_refresh(self, bubble, delays=(0, 30, 80, 200, 500, 1000)):
        """在多个时间点刷新气泡高度，确保最终高度准确（覆盖各种延迟场景）

        说明：
          - Text 用 height 控制行数，内容换行后需要重新测量才能得到准确行数
          - Tk 的布局是异步的，一次刷新可能读到旧数据
          - 用多个时间点兜底，无论哪个时机布局已就绪，都会算出正确高度
        """
        if bubble is None:
            return
        for d in delays:
            try:
                if d <= 0:
                    self._auto_bubble_height(bubble)
                else:
                    self.after(d, lambda b=bubble: self._auto_bubble_height(b))
            except Exception:
                pass

    def _disable_text_scroll(self, text_widget):
        """禁用 Text 内部的滚轮滚动和键盘滚动（让外层 Canvas 接管滚动）"""
        try:
            def _on_mousewheel(event):
                # 把滚轮事件转发给外层 Canvas，Text 自己不滚
                try:
                    delta = -1 if event.delta > 0 else 1
                    self.chat_canvas.yview_scroll(delta * 5, "units")
                except Exception:
                    pass
                return "break"
            text_widget.bind("<MouseWheel>", _on_mousewheel)

            # ===== 拦截键盘滚动按键，防止 Text 内部产生滚动 =====
            def _block_key(event):
                return "break"
            for seq in ("<Up>", "<Down>", "<Prior>", "<Next>",
                        "<Home>", "<End>", "<Control-Home>", "<Control-End>"):
                try:
                    text_widget.bind(seq, _block_key)
                except Exception:
                    pass
        except Exception:
            pass

    def _adjust_bubble_wrap(self, bubble):
        """根据窗口宽度调整气泡宽度（Text 用 width 设置，Label 用 wraplength）"""
        try:
            total = self.chat_canvas.winfo_width()
            if total <= 1:
                # 窗口还没渲染完，稍后再试
                self.after(50, lambda b=bubble: self._adjust_bubble_wrap(b))
                return

            # 左右两侧预留：头像(36) + 间距(约 90) = 约 140
            bubble_px = max(220, total - 140)

            if isinstance(bubble, tk.Text):
                # 用字体测量精确换算：Text 的 width 单位是 "0" 字符的宽度
                try:
                    from tkinter.font import Font
                    f = Font(font=("Microsoft YaHei", 10))
                    zero_px = f.measure("0")
                    if zero_px <= 0:
                        zero_px = 7
                except Exception:
                    zero_px = 7
                char_width = max(15, int(bubble_px / zero_px))
                # 避免和已设置值相同导致死循环
                try:
                    cur_w = int(bubble.cget("width"))
                except Exception:
                    cur_w = -1
                if cur_w != char_width:
                    bubble.config(width=char_width)
                # 宽度变了，重新计算高度
                self._auto_bubble_height(bubble)
            else:
                bubble.config(wraplength=bubble_px)
        except Exception:
            pass

    def _append_ai_bubble_typing(self, full_text):
        """打字机效果：先创建空气泡，逐字填充；每秒做一次 Markdown 渲染"""
        row = tk.Frame(self.chat_inner, bg=self.BG_COLOR)
        row.pack(fill=tk.X, pady=4, padx=4)

        if getattr(self, "_ai_avatar_img", None) is not None:
            avatar = tk.Label(row, image=self._ai_avatar_img, bd=0, relief=tk.FLAT, bg=self.BG_COLOR)
        else:
            avatar = tk.Label(
                row, text="電",
                font=("Microsoft YaHei", 11, "bold"),
                bg="#0C8CE9", fg="#FFFFFF",
                width=2, height=1,
                bd=0, relief=tk.FLAT
            )
        avatar.pack(side=tk.LEFT, anchor=tk.NW, padx=(0, 2))

        bubble_wrap = tk.Frame(row, bg=self.AI_BUBBLE_BORDER, bd=0)
        bubble = tk.Text(
            bubble_wrap,
            font=("Microsoft YaHei", 10),
            bg=self.AI_BUBBLE_BG, fg=self.AI_TEXT_COLOR,
            relief=tk.FLAT, bd=0,
            highlightthickness=0,
            wrap=tk.WORD,
            padx=12, pady=8,
            cursor="arrow",
            height=1, width=30,
            takefocus=0,
        )
        # 注册 md_tag
        self._setup_md_tags(bubble, self.AI_BUBBLE_BG)
        bubble.pack(padx=1, pady=1)
        bubble_wrap.pack(side=tk.LEFT, anchor=tk.NW, padx=(6, 40))

        # 禁用气泡内部滚轮滚动
        self._disable_text_scroll(bubble)


        self._bind_wheel_recursive(row)

        # 绑定 Configure + 主动调整宽度
        bubble.bind("<Configure>", lambda e, b=bubble: self._adjust_bubble_wrap(b))
        bubble.after(20, lambda b=bubble: self._adjust_bubble_wrap(b))

        # ===== 记下"完整 MD 原文"，供打字结束后和每秒渲染时用 =====
        self._typewriter_full_text = full_text

        # 打字机队列
        self._typewriter_queue = list(full_text)
        self._typewriter_bubble_widget = bubble
        self._typewriter_label = bubble

        if self._typewriter_timer:
            try:
                self.after_cancel(self._typewriter_timer)
            except Exception:
                pass
        self._typewriter_timer = self.after(15, self._typewriter_step)

        # ===== 新增：每秒一次的"局部 MD 渲染"定时器 =====
        if getattr(self, "_md_refresh_timer", None):
            try:
                self.after_cancel(self._md_refresh_timer)
            except Exception:
                pass
        self._md_refresh_timer = self.after(1000, self._md_refresh_tick)

    def _typewriter_step(self):
        """打字机效果步进（往 Text 里逐字插入）；打完后做最终 Markdown 渲染"""
        if not self._typewriter_queue:
            self._typewriter_timer = None
            # 停掉每秒的 MD 刷新定时器（马上做最终渲染）
            if getattr(self, "_md_refresh_timer", None):
                try:
                    self.after_cancel(self._md_refresh_timer)
                except Exception:
                    pass
                self._md_refresh_timer = None

            # ===== 打完后，把纯文本整段替换成最终 Markdown 渲染结果 =====
            try:
                full_text = getattr(self, "_typewriter_full_text", "")
                bubble = self._typewriter_label
                if bubble is not None and full_text:
                    bubble.config(state=tk.NORMAL)
                    bubble.delete("1.0", tk.END)
                    bubble.config(state=tk.DISABLED)
                    self._render_markdown_into(bubble, full_text)
                self._typewriter_label.config(state=tk.DISABLED)
            except Exception as _e:
                print(f"[電籽AI] 打字结束后的 Markdown 渲染失败: {_e}")
                try:
                    self._typewriter_label.config(state=tk.DISABLED)
                except Exception:
                    pass

            # ===== 打字完成后用多时间点刷新高度，确保末尾文本完整显示 =====
            try:
                b = getattr(self, "_typewriter_label", None)
                if b is not None:
                    self._schedule_height_refresh(b)
            except Exception:
                pass

            self._scroll_chat_to_bottom()
            return

        # ===== 每次 tick 打 2 个字符，加快打字速度 =====
        chars_this_tick = min(2, len(self._typewriter_queue))
        try:
            # 打字过程中需要临时开启 NORMAL
            self._typewriter_label.config(state=tk.NORMAL)
            for _ in range(chars_this_tick):
                if not self._typewriter_queue:
                    break
                char = self._typewriter_queue.pop(0)
                self._typewriter_label.insert(tk.END, char)
            self._typewriter_label.config(state=tk.DISABLED)
        except Exception:
            pass

        # ===== 每打 3 个字更新一次气泡高度 =====
        try:
            total_chars = len(self._typewriter_queue)
            if total_chars % 3 == 0:
                self._auto_bubble_height(self._typewriter_label)
        except Exception:
            pass

        self._scroll_chat_to_bottom()
        self._typewriter_timer = self.after(8, self._typewriter_step)

    def _md_refresh_tick(self):
        """每 1 秒做一次 Markdown 局部渲染（只渲染已打出的那部分）"""
        try:
            # 如果打字已经结束，停掉自己
            if not self._typewriter_queue:
                self._md_refresh_timer = None
                return

            bubble = getattr(self, "_typewriter_label", None)
            full_text = getattr(self, "_typewriter_full_text", "")
            if bubble is None or not full_text:
                self._md_refresh_timer = self.after(1000, self._md_refresh_tick)
                return

            # 计算"已打出的字符数"
            total_len = len(full_text)
            remaining = len(self._typewriter_queue)
            typed_len = total_len - remaining
            if typed_len <= 0:
                self._md_refresh_timer = self.after(1000, self._md_refresh_tick)
                return

            typed_text = full_text[:typed_len]

            # 重新渲染到气泡（清空 → 用 MD 渲染 → DISABLED）
            bubble.config(state=tk.NORMAL)
            bubble.delete("1.0", tk.END)
            bubble.config(state=tk.DISABLED)
            self._render_markdown_into(bubble, typed_text)
            bubble.config(state=tk.DISABLED)

            # 高度和滚动都刷新一下
            self._auto_bubble_height(bubble)
            self._scroll_chat_to_bottom()
        except Exception as _e:
            print(f"[電籽AI] 每秒 MD 渲染失败: {_e}")
        finally:
            # 只要还在打字，就继续下一轮（1 秒后）
            try:
                if self._typewriter_queue:
                    self._md_refresh_timer = self.after(1000, self._md_refresh_tick)
                else:
                    self._md_refresh_timer = None
            except Exception:
                self._md_refresh_timer = None

    # ---------- 输入相关 ----------
    def _auto_resize_input(self, event=None):
        """根据内容自动调整输入框高度（3~8 行）"""
        try:
            content = self.input_text.get("1.0", tk.END)
            lines = content.count("\n")
            lines = max(3, min(8, lines + 1))
            self.input_text.config(height=lines)
        except Exception:
            pass

    # ---------- 引用功能 ----------
    def _init_reference_area(self, parent):
        """初始化待发送引用区（按钮行 + 卡片区）。"""
        # ===== 引用按钮行（紧贴输入区上方） =====
        self.ref_btn_row = tk.Frame(parent, bg=self.BG_COLOR)
        self.ref_btn_row.pack(fill=tk.X, side=tk.BOTTOM, pady=(6, 0))

        def _make_ref_btn(text, cmd):
            btn = tk.Button(
                self.ref_btn_row, text=text,
                font=("Microsoft YaHei", 9),
                bg="#F0F2F5", fg="#333333",
                activebackground="#E0E4EA",
                relief=tk.FLAT, bd=0, padx=10, pady=4,
                cursor="hand2",
                command=cmd,
            )
            return btn

        self.ref_project_btn = _make_ref_btn("📄 引用工程", self._on_reference_project)
        self.ref_project_btn.pack(side=tk.LEFT, padx=(0, 4))

        self.ref_notes_btn = _make_ref_btn("🎵 引用事件块", self._on_reference_selected_notes)
        self.ref_notes_btn.pack(side=tk.LEFT, padx=(0, 4))

        self.ref_timesel_btn = _make_ref_btn("⏱ 引用时间选区", self._on_reference_time_selection)
        self.ref_timesel_btn.pack(side=tk.LEFT)

        # 悬浮效果
        def _on_btn_enter(e, w):
            try:
                if w['state'] != tk.DISABLED:
                    w.config(bg="#E0E4EA")
            except Exception:
                pass

        def _on_btn_leave(e, w):
            try:
                if w['state'] != tk.DISABLED:
                    w.config(bg="#F0F2F5")
            except Exception:
                pass

        for b in (self.ref_project_btn, self.ref_notes_btn, self.ref_timesel_btn):
            b.bind("<Enter>", lambda e, w=b: _on_btn_enter(e, w))
            b.bind("<Leave>", lambda e, w=b: _on_btn_leave(e, w))

        # 初始化时如果没工程，全部禁用
        if not getattr(self.app, 'current_project_path', None):
            for b in (self.ref_project_btn, self.ref_notes_btn, self.ref_timesel_btn):
                b.config(state=tk.DISABLED, fg="#AAAAAA")

        # ===== 待发送引用区（卡片列表，在按钮行上方） =====
        self.reference_area = tk.Frame(parent, bg=self.BG_COLOR)
        self.reference_area.pack(fill=tk.X, side=tk.BOTTOM)
        self.reference_area.pack_forget()  # 初始隐藏

        self.reference_header_label = tk.Label(
            self.reference_area,
            text="待发送的引用",
            font=("Microsoft YaHei", 9, "bold"),
            bg=self.BG_COLOR, fg="#666666",
            anchor="w"
        )

        self.reference_inner = tk.Frame(self.reference_area, bg=self.BG_COLOR)

    def _compose_message_with_references(self, user_input):
        """将引用内容和用户输入拼装成最终消息。"""
        if not self._references:
            return user_input

        parts = ["【我的问题】", user_input, "", "【我引用的上下文】"]
        for ref_type in ('project', 'selected_notes', 'time_selection'):
            ref = self._references.get(ref_type)
            if ref:
                parts.append("")
                parts.append(f"=== {ref['title']} ===")
                parts.append(ref['content'])

        return "\n".join(parts)

    def _on_reference_project(self):
        """点击「引用工程」按钮。"""
        app = self.app
        if not getattr(app, 'current_project_path', None):
            messagebox.showwarning("提示", "请先打开一个工程", parent=self)
            return

        include_full_json_var = tk.BooleanVar(value=False)

        def _extra_options(win, main, refs, text_widget, size_label):
            cb_frame = ttk.Frame(main)
            cb_frame.pack(fill=tk.X, pady=(6, 0))
            ttk.Checkbutton(
                cb_frame,
                text="⚠️ 同时包含完整工程 JSON（可能占用大量 token）",
                variable=include_full_json_var,
                style="Preview.TCheckbutton"
            ).pack(anchor=tk.W)

            def _refresh(*args):
                content = self._build_project_reference_text(include_full_json_var.get())
                text_widget.config(state=tk.NORMAL)
                text_widget.delete("1.0", tk.END)
                text_widget.insert("1.0", content)
                text_widget.config(state=tk.DISABLED)
                size_label.config(text=f"预计内容大小：约 {len(content)} 字符")

            include_full_json_var.trace_add("write", _refresh)

        initial_content = self._build_project_reference_text(False)

        def _on_confirm(option_refs, final_content):
            title = "当前工程摘要"
            subtitle = os.path.basename(app.current_project_path) or "工程"
            if include_full_json_var.get():
                subtitle += "（含完整 JSON）"
            self._add_reference_card('project', title, subtitle, final_content)

        self._show_reference_preview("引用预览 - 当前工程", initial_content, _on_confirm, _extra_options)

    def _on_reference_selected_notes(self):
        """点击「引用事件块」按钮。"""
        app = self.app
        selected = list(getattr(app, 'selected_notes', []))
        if not selected:
            messagebox.showwarning("提示", "请先在主界面选中至少一个音符块或调整图层哦～", parent=self)
            return

        content = self._build_selected_notes_reference_text()
        if not content:
            messagebox.showinfo("提示", "选中的内容无法构造为引用", parent=self)
            return

        def _on_confirm(option_refs, final_content):
            n = len(selected)
            self._add_reference_card(
                'selected_notes',
                f"选中的 {n} 个事件块",
                "来自主界面当前选中",
                final_content
            )

        self._show_reference_preview(
            f"引用预览 - 选中的 {len(selected)} 个事件块",
            content, _on_confirm
        )

    def _on_reference_time_selection(self):
        """点击「引用时间选区」按钮。"""
        app = self.app
        ts = getattr(app, 'time_sel', None)
        if ts is None or not (ts.start_x > 0 and ts.end_x > 0 and ts.start_x < ts.end_x):
            messagebox.showwarning("提示", "请先在主界面按 F4 画一个时间选区哦～", parent=self)
            return

        mode_var = tk.StringVar(value='simple')

        def _extra_options(win, main, refs, text_widget, size_label):
            mode_frame = ttk.Frame(main)
            mode_frame.pack(fill=tk.X, pady=(6, 0))
            ttk.Radiobutton(mode_frame, text="简要列表（推荐）", variable=mode_var, value='simple', style="Preview.TRadiobutton").pack(side=tk.LEFT)
            ttk.Radiobutton(mode_frame, text="详细展开", variable=mode_var, value='detailed', style="Preview.TRadiobutton").pack(side=tk.LEFT, padx=10)

            def _refresh(*args):
                content = self._build_time_selection_reference_text(mode_var.get())
                if not content:
                    content = "（范围内没有事件块）"
                text_widget.config(state=tk.NORMAL)
                text_widget.delete("1.0", tk.END)
                text_widget.insert("1.0", content)
                text_widget.config(state=tk.DISABLED)
                size_label.config(text=f"预计内容大小：约 {len(content)} 字符")

            mode_var.trace_add("write", _refresh)

        initial_content = self._build_time_selection_reference_text('simple')
        if not initial_content:
            initial_content = "（范围内没有事件块）"

        def _on_confirm(option_refs, final_content):
            try:
                bpm_ratio = app.midi_original_bpm / app.target_bpm if app.target_bpm > 0 else 1.0
                scaled_beat_width = app.beat_width * app.scale_factor_x * bpm_ratio
                start_x_px = 50 * app.scale_factor_x
                sb = (ts.start_x - start_x_px) / scaled_beat_width if scaled_beat_width > 0 else 0
                eb = (ts.end_x - start_x_px) / scaled_beat_width if scaled_beat_width > 0 else 0
                beat_range = f"节拍 {sb:.2f} ~ {eb:.2f}"
            except Exception:
                beat_range = "时间选区"
            self._add_reference_card(
                'time_selection',
                f"时间选区 {beat_range}",
                "范围内事件块",
                final_content
            )

        self._show_reference_preview(
            "引用预览 - 时间选区",
            initial_content, _on_confirm, _extra_options
        )

    def _build_project_reference_text(self, include_full_json=False):
        """构造工程摘要引用文本。"""
        app = self.app
        lines = ["### 当前工程概览"]
        try:
            project_name = os.path.basename(app.current_project_path or '')
        except Exception:
            project_name = ''
        lines.append(f"- 工程名：{project_name}")
        lines.append(f"- 当前 BPM：{getattr(app, 'target_bpm', '?')}（原速 {getattr(app, 'midi_original_bpm', '?')}）")
        lines.append(f"- 总节拍：{getattr(app, 'midi_total_beat', '?')}")
        all_notes = getattr(app, 'all_notes', [])
        lines.append(f"- 音符块：{len(all_notes)} 个")

        tracks = set()
        for nd in all_notes:
            if len(nd) >= 5:
                tracks.add(nd[0])
        lines.append(f"- 轨道数：{len(tracks)}")

        adjust_layers = getattr(app, 'adjust_layers', []) or []
        lines.append(f"- 调整图层：{len(adjust_layers)} 个")

        try:
            if getattr(app, 'marker_manager', None):
                lines.append(f"- 标记：{app.marker_manager.get_marker_count()} 个")
            else:
                lines.append("- 标记：0 个")
        except Exception:
            lines.append("- 标记：?")

        try:
            if getattr(app, 'global_command_manager', None):
                lines.append(f"- 全局命令：{app.global_command_manager.get_command_count()} 条")
            else:
                lines.append("- 全局命令：0 条")
        except Exception:
            lines.append("- 全局命令：?")

        lines.append(f"- 阵列：{len(getattr(app, 'arrays', []) or [])} 个")

        # 时间选区
        ts = getattr(app, 'time_sel', None)
        if ts and (ts.start_x > 0 or ts.end_x > 0):
            try:
                bpm_ratio = app.midi_original_bpm / app.target_bpm if app.target_bpm > 0 else 1.0
                scaled_beat_width = app.beat_width * app.scale_factor_x * bpm_ratio
                start_x_px = 50 * app.scale_factor_x
                if scaled_beat_width > 0:
                    sb = (ts.start_x - start_x_px) / scaled_beat_width
                    eb = (ts.end_x - start_x_px) / scaled_beat_width
                    lines.append(f"- 时间选区：节拍 {sb:.2f} ~ {eb:.2f}")
                else:
                    lines.append("- 时间选区：（无）")
            except Exception:
                lines.append("- 时间选区：（无）")
        else:
            lines.append("- 时间选区：（无）")

        lines.append(f"- 当前选中：{len(getattr(app, 'selected_notes', []) or [])} 个")

        if include_full_json:
            try:
                with open(app.current_project_path, 'r', encoding='utf-8') as f:
                    full_json = f.read()
                lines.append("")
                lines.append("### 完整工程 JSON")
                lines.append("```json")
                lines.append(full_json)
                lines.append("```")
            except Exception as e:
                lines.append("")
                lines.append(f"（读取完整 JSON 失败：{e}）")

        return "\n".join(lines)

    def _build_selected_notes_reference_text(self):
        """构造选中事件块引用文本。"""
        app = self.app
        selected = list(getattr(app, 'selected_notes', []) or [])
        if not selected:
            return None

        adjust_layers = getattr(app, 'adjust_layers', []) or []
        layer_id_set = set()
        for ly in adjust_layers:
            if isinstance(ly, dict) and 'id' in ly:
                layer_id_set.add(ly['id'])

        lines = [f"### 引用：选中的 {len(selected)} 个事件块", ""]

        idx = 0
        for sid in selected:
            idx += 1
            if sid in layer_id_set:
                layer = next((ly for ly in adjust_layers if ly.get('id') == sid), None)
                if layer:
                    lines.append(f"#### 事件块 {idx}（调整图层）")
                    lines.append(f"- 轨道：{layer.get('track_idx', 0) + 1}")
                    sb = layer.get('start_beat', 0)
                    dur = layer.get('duration', 0)
                    lines.append(f"- 节拍：{sb:.2f} ~ {sb + dur:.2f}（{dur:.2f} 拍）")
                    color = layer.get('color', '')
                    if color:
                        lines.append(f"- 颜色：{color}")
                    ep = layer.get('effect_params', {})
                    if ep:
                        try:
                            lines.append(f"- 效果参数：{json.dumps(ep, ensure_ascii=False)}")
                        except Exception:
                            lines.append(f"- 效果参数：{ep}")
                    lines.append("")
            else:
                nd = next((d for d in app.all_notes if len(d) >= 5 and d[4] == sid), None)
                if nd:
                    lines.append(f"#### 事件块 {idx}（音符块）")
                    lines.append(f"- 轨道：{nd[0] + 1}")
                    sb, dur, nv = nd[1], nd[2], nd[3]
                    lines.append(f"- 节拍：{sb:.2f} ~ {sb + dur:.2f}（{dur:.2f} 拍）")
                    lines.append(f"- 音高：{nv}")
                    color = getattr(app, 'note_color_map', {}).get(sid, '')
                    if color:
                        lines.append(f"- 颜色：{color}")
                    custom_text = getattr(app, 'note_custom_text', {}).get(sid, '')
                    if custom_text:
                        lines.append(f"- 自定义文本：{custom_text}")
                    cze = nd[5] if len(nd) >= 6 else {}
                    if cze and isinstance(cze, dict) and len(cze) > 0:
                        lines.append(f"- 配参：")
                        for k, v in cze.items():
                            lines.append(f"  {k}: {v}")
                    transition = nd[6] if len(nd) >= 7 else None
                    if transition:
                        try:
                            lines.append(f"- 过渡：{json.dumps(transition, ensure_ascii=False)}")
                        except Exception:
                            lines.append(f"- 过渡：{transition}")
                    disabled = nd[7] if len(nd) >= 8 else False
                    lines.append(f"- 禁用：{'是' if disabled else '否'}")
                    lines.append("")

        return "\n".join(lines)

    def _build_time_selection_reference_text(self, mode='simple'):
        """构造时间选区引用文本。mode 可选 'simple' 或 'detailed'。"""
        app = self.app
        ts = getattr(app, 'time_sel', None)
        if ts is None or not (ts.start_x > 0 or ts.end_x > 0):
            return None

        bpm_ratio = app.midi_original_bpm / app.target_bpm if app.target_bpm > 0 else 1.0
        scaled_beat_width = app.beat_width * app.scale_factor_x * bpm_ratio
        start_x_px = 50 * app.scale_factor_x
        if scaled_beat_width <= 0:
            return None
        sb = (ts.start_x - start_x_px) / scaled_beat_width
        eb = (ts.end_x - start_x_px) / scaled_beat_width

        events = []
        for nd in getattr(app, 'all_notes', []):
            if len(nd) >= 5:
                s, d = nd[1], nd[2]
                e = s + d
                if e > sb and s < eb:
                    events.append(('note', nd))
        for ly in getattr(app, 'adjust_layers', []) or []:
            if not isinstance(ly, dict):
                continue
            s = ly.get('start_beat', 0)
            d = ly.get('duration', 0)
            e = s + d
            if e > sb and s < eb:
                events.append(('layer', ly))

        # ===== 获取全局命令和标记（仅在 detailed 模式下） =====
        if mode == 'detailed':
            if getattr(app, 'global_command_manager', None):
                try:
                    cmds = app.global_command_manager.get_commands_data()
                    for cmd in cmds:
                        c_beat = cmd.get('beat', 0)
                        # 兼容不同的节拍字段命名
                        if 'start_beat' in cmd: c_beat = cmd['start_beat']
                        elif 'position' in cmd: c_beat = cmd['position']
                        if sb <= c_beat <= eb:
                            events.append(('command', cmd))
                except Exception as e:
                    print(f"获取全局命令失败: {e}")

            if getattr(app, 'marker_manager', None):
                try:
                    markers = app.marker_manager.get_markers_data()
                    for m in markers:
                        m_beat = m.get('beat', 0)
                        if sb <= m_beat <= eb:
                            events.append(('marker', m))
                except Exception as e:
                    print(f"获取标记失败: {e}")

        def _sort_key(item):
            t, data = item
            if t == 'note':
                return data[1]
            elif t == 'layer':
                return data.get('start_beat', 0)
            elif t == 'command':
                # 全局命令可能存储为 beat 或 start_beat
                return data.get('start_beat', data.get('beat', data.get('position', 0)))
            elif t == 'marker':
                return data.get('beat', 0)
            return 0

        events.sort(key=_sort_key)

        note_count = sum(1 for t, _ in events if t == 'note')
        layer_count = sum(1 for t, _ in events if t == 'layer')
        cmd_count = sum(1 for t, _ in events if t == 'command')
        marker_count = sum(1 for t, _ in events if t == 'marker')

        type_desc_parts = []
        if note_count > 0: type_desc_parts.append(f"音符块 {note_count} 个")
        if layer_count > 0: type_desc_parts.append(f"调整图层 {layer_count} 个")
        if cmd_count > 0: type_desc_parts.append(f"全局命令 {cmd_count} 个")
        if marker_count > 0: type_desc_parts.append(f"标记 {marker_count} 个")

        type_desc = "，".join(type_desc_parts) if type_desc_parts else "无"

        lines = [
            f"### 引用：时间选区 节拍 {sb:.2f} ~ {eb:.2f}",
            f"范围内共 {len(events)} 个事件（{type_desc}）",
            ""
        ]

        if mode == 'simple':
            for i, (t, data) in enumerate(events, 1):
                if t == 'note':
                    s, d, nv = data[1], data[2], data[3]
                    lines.append(f"{i}. [音符] 轨道 {data[0] + 1}，节拍 {s:.2f} ~ {s + d:.2f}，音高 {nv}")
                    cze = data[5] if len(data) >= 6 else {}
                    if cze and isinstance(cze, dict):
                        wt = cze.get('window_type', '')
                        if wt:
                            lines.append(f"   配参类型：{wt}")
                else:
                    s = data.get('start_beat', 0)
                    d = data.get('duration', 0)
                    lines.append(f"{i}. [调整图层] 轨道 {data.get('track_idx', 0) + 1}，节拍 {s:.2f} ~ {s + d:.2f}")
        else:
            for i, (t, data) in enumerate(events, 1):
                if t == 'note':
                    lines.append(f"#### 事件块 {i}（音符块）")
                    lines.append(f"- 轨道：{data[0] + 1}")
                    s, d, nv = data[1], data[2], data[3]
                    lines.append(f"- 节拍：{s:.2f} ~ {s + d:.2f}（{d:.2f} 拍）")
                    lines.append(f"- 音高：{nv}")
                    cze = data[5] if len(data) >= 6 else {}
                    if cze and isinstance(cze, dict) and len(cze) > 0:
                        lines.append(f"- 配参：")
                        for k, v in cze.items():
                            lines.append(f"  {k}: {v}")
                    lines.append("")
                elif t == 'layer':
                    lines.append(f"#### 事件块 {i}（调整图层）")
                    lines.append(f"- 轨道：{data.get('track_idx', 0) + 1}")
                    s = data.get('start_beat', 0)
                    d = data.get('duration', 0)
                    lines.append(f"- 节拍：{s:.2f} ~ {s + d:.2f}（{d:.2f} 拍）")
                    lines.append("")
                elif t == 'command':
                    c_beat = data.get('start_beat', data.get('beat', data.get('position', 0)))
                    lines.append(f"#### 事件块 {i}（全局命令）")
                    lines.append(f"- 节拍：{c_beat:.2f}")
                    lines.append(f"- 描述：{data.get('description', '')}")
                    lines.append(f"- 命令：{data.get('command', '')}")
                    lines.append("")
                elif t == 'marker':
                    lines.append(f"#### 事件块 {i}（标记）")
                    lines.append(f"- 节拍：{data.get('beat', 0):.2f}")
                    lines.append(f"- 描述：{data.get('description', '')}")
                    lines.append("")

        return "\n".join(lines)

    def _show_reference_preview(self, title, content, on_confirm, extra_options=None):
        """显示引用预览窗口。
        extra_options(win, main, refs, text_widget, size_label) 可选回调，
        用于在预览窗口底部添加复选框/单选按钮等额外控件。
        """
        preview_win = tk.Toplevel(self)
        preview_win.title(title)
        preview_win.transient(self)
        preview_win.resizable(True, True)
        try:
            preview_win.iconbitmap("img/icon.ico")
        except Exception:
            pass
        preview_win.withdraw()

        w, h = 620, 460
        screen_w = preview_win.winfo_screenwidth()
        screen_h = preview_win.winfo_screenheight()
        x = (screen_w - w) // 2
        y = (screen_h - h) // 2
        preview_win.geometry(f"{w}x{h}+{x}+{y}")


        style = ttk.Style(preview_win)
        style.configure("Preview.TButton", font=("Microsoft YaHei", 10))
        style.configure("Preview.TCheckbutton", font=("Microsoft YaHei", 9))
        style.configure("Preview.TRadiobutton", font=("Microsoft YaHei", 9))

        main = ttk.Frame(preview_win, padding="10")
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text=title, font=("Microsoft YaHei", 11, "bold")).pack(anchor=tk.W, pady=(0, 8))

        text_frame = ttk.Frame(main)
        text_frame.pack(fill=tk.BOTH, expand=True)

        preview_text = tk.Text(
            text_frame, font=("Microsoft YaHei", 9), wrap=tk.WORD,
            bg="#F8F8F8", relief=tk.SUNKEN, bd=1, height=1
        )
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=preview_text.yview)
        preview_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        preview_text.insert("1.0", content)
        preview_text.config(state=tk.DISABLED)

        size_label = ttk.Label(main, text=f"预计内容大小：约 {len(content)} 字符", foreground="#666666")
        size_label.pack(anchor=tk.W, pady=(6, 0))

        option_refs = {}
        if extra_options:
            try:
                extra_options(preview_win, main, option_refs, preview_text, size_label)
            except Exception as e:
                print(f"[预览] extra_options 失败: {e}")
                import traceback
                traceback.print_exc()

        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        def _on_cancel():
            preview_win.destroy()

        def _on_ok():
            try:
                final_text = preview_text.get("1.0", tk.END).rstrip("\n")
                on_confirm(option_refs, final_text)
            except Exception as e:
                print(f"[预览] 确认回调失败: {e}")
                import traceback
                traceback.print_exc()
            preview_win.destroy()

        # 确认按钮先 pack（在最右侧），取消按钮后 pack（在左侧）
        ttk.Button(btn_frame, text="确认引用", command=_on_ok, width=10, style="Preview.TButton").pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="取消", command=_on_cancel, width=10, style="Preview.TButton").pack(side=tk.RIGHT)

        preview_win.deiconify()
        preview_win.focus_force()
        preview_win.grab_set()
        preview_win.wait_window(preview_win)

    def _add_reference_card(self, ref_type, title, subtitle, content):
        """向待发送区添加/更新引用卡片。"""
        self._remove_reference_card(ref_type, silent=True)

        icon_map = {
            'project': '📄',
            'selected_notes': '🎵',
            'time_selection': '⏱',
        }

        card_frame = tk.Frame(
            self.reference_inner, bg="#FFF8E1",
            bd=0, highlightthickness=1, highlightbackground="#F0C36D"
        )
        card_frame.pack(fill=tk.X, pady=2)

        icon = tk.Label(
            card_frame, text=icon_map.get(ref_type, '📎'),
            font=("Microsoft YaHei", 11), bg="#FFF8E1"
        )
        icon.pack(side=tk.LEFT, padx=(8, 4), pady=4)

        text_frame = tk.Frame(card_frame, bg="#FFF8E1")
        text_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=4)

        title_label = tk.Label(
            text_frame, text=title,
            font=("Microsoft YaHei", 9, "bold"),
            bg="#FFF8E1", fg="#333333",
            anchor="w", cursor="hand2"
        )
        title_label.pack(anchor="w")

        sub_label = tk.Label(
            text_frame, text=subtitle,
            font=("Microsoft YaHei", 8),
            bg="#FFF8E1", fg="#888888",
            anchor="w", cursor="hand2"
        )
        sub_label.pack(anchor="w")

        def _on_click(e):
            self._show_reference_preview(
                f"引用详情 - {title}", content,
                lambda opts, txt: None
            )

        title_label.bind("<Button-1>", _on_click)
        sub_label.bind("<Button-1>", _on_click)
        text_frame.bind("<Button-1>", _on_click)

        close_btn = tk.Label(
            card_frame, text="×",
            font=("Arial", 12, "bold"),
            bg="#FFF8E1", fg="#888888",
            cursor="hand2", padx=8
        )
        close_btn.pack(side=tk.RIGHT, pady=4)
        close_btn.bind("<Button-1>", lambda e: self._remove_reference_card(ref_type))
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg="#FF4444"))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg="#888888"))

        self._references[ref_type] = {
            'title': title,
            'subtitle': subtitle,
            'content': content,
            'card_frame': card_frame,
        }

        self._update_reference_area_visibility()

    def _remove_reference_card(self, ref_type, silent=False):
        """移除指定类型的引用卡片。"""
        ref = self._references.pop(ref_type, None)
        if ref and ref.get('card_frame'):
            try:
                ref['card_frame'].destroy()
            except Exception:
                pass
        if not silent:
            self._update_reference_area_visibility()

    def _clear_reference_cards(self):
        """清空所有引用卡片。"""
        for rt in list(self._references.keys()):
            self._remove_reference_card(rt, silent=True)
        self._update_reference_area_visibility()

    def _update_reference_area_visibility(self):
        """更新引用区可见性和状态栏文字。"""
        try:
            count = len(self._references)
            if count > 0:
                self.reference_header_label.config(text=f"待发送的引用（{count} 条）")
                if not self.reference_area.winfo_ismapped():
                    self.reference_area.pack(fill=tk.X, side=tk.BOTTOM)
                if not self.reference_header_label.winfo_ismapped():
                    self.reference_header_label.pack(fill=tk.X)
                if not self.reference_inner.winfo_ismapped():
                    self.reference_inner.pack(fill=tk.X)
                self.status_var.set(f"就绪（已引用 {count} 条上下文）")
                try:
                    self.update_idletasks()
                except Exception:
                    pass
            else:
                self.reference_area.pack_forget()
                self.status_var.set("就绪")
                try:
                    self.update_idletasks()
                except Exception:
                    pass
        except Exception as e:
            print(f"[引用] 更新可见性失败: {e}")

    def _on_enter(self, event):
        """回车发送，Shift+回车换行"""
        if event.state & 0x1:  # Shift 按下
            return None
        self._send_message()
        return "break"

    def _send_message(self):
        user_input = self.input_text.get("1.0", tk.END).strip()

        # 检查是否有引用
        has_refs = bool(self._references)

        if not user_input and not has_refs:
            return

        # 如果没打字但有引用，用默认提示词
        if not user_input and has_refs:
            if not messagebox.askyesno("确认发送", "你想让電籽分析这些引用的内容吗？\n\n（未输入具体问题，将发送默认提示）", parent=self):
                return
            user_input = "请分析以下我引用的内容。"

        # 构建最终消息（含引用内容）
        final_content = self._compose_message_with_references(user_input)

        self.input_text.delete("1.0", tk.END)
        self.input_text.config(height=3)

        # 显示气泡：用户输入 + 引用摘要（让用户在对话流里也能看到引用了什么）
        display_text = user_input
        if has_refs:
            ref_summary = "\n".join([f"📎 {r['title']}" for r in self._references.values()])
            display_text += f"\n\n—— 已引用上下文 ——\n{ref_summary}"
        self._append_user_bubble(display_text)

        self.messages.append({"role": "user", "content": final_content})

        # 清空引用卡片
        self._clear_reference_cards()

        self._set_busy(True)
        # ===== 先放一个"思考中"的气泡，带跳动点点 =====
        self._show_thinking_bubble()
        threading.Thread(target=self._request_ai, daemon=True).start()

    def _set_busy(self, busy):
        """切换忙碌/就绪状态"""
        if busy:
            self.status_var.set("電籽正在思考...")
            self.send_btn.config(state=tk.DISABLED, bg="#AAAAAA")
        else:
            self.status_var.set("就绪")
            self.send_btn.config(state=tk.NORMAL, bg=self.SEND_BTN_BG)

    def _request_ai(self):
        """后台线程请求 AI"""
        try:
            from openai import OpenAI
            # 从配置读取
            api_key = self.ai_config.get("api_key", API_KEY)
            base_url = self.ai_config.get("base_url", BASE_URL)
            model = self.ai_config.get("current_model", MODEL)
            client = OpenAI(api_key=api_key, base_url=base_url)
            response = client.chat.completions.create(
                model=model,
                messages=self.messages,
                stream=False,
                timeout=90
            )
            ai_reply = response.choices[0].message.content
            self.messages.append({"role": "assistant", "content": ai_reply})
            self.after(0, self._on_ai_reply, ai_reply)
        except Exception as e:
            self.after(0, self._on_ai_error, str(e))

    def _on_ai_reply(self, reply):
        self._set_busy(False)
        # 先移除思考气泡
        self._remove_thinking_bubble()
        self._append_ai_bubble(reply, typing=True)

    def _on_ai_error(self, error):
        self._set_busy(False)
        # 先移除思考气泡
        self._remove_thinking_bubble()
        self._append_ai_bubble(f"呜呜出错了啦 (｡>﹏<｡)：{error}", typing=False)

    # ---------- 思考气泡（三个跳动的小点） ----------
    def _show_thinking_bubble(self):
        """显示一个'電籽正在思考'的气泡，三个小点循环跳动"""
        # 先清理旧的可能残留的思考气泡
        self._remove_thinking_bubble()

        row = tk.Frame(self.chat_inner, bg=self.BG_COLOR)
        row.pack(fill=tk.X, pady=4, padx=4)

        # 头像
        if getattr(self, "_ai_avatar_img", None) is not None:
            avatar = tk.Label(row, image=self._ai_avatar_img, bd=0, relief=tk.FLAT, bg=self.BG_COLOR)
        else:
            avatar = tk.Label(
                row, text="電",
                font=("Microsoft YaHei", 11, "bold"),
                bg="#0C8CE9", fg="#FFFFFF",
                width=2, height=1,
                bd=0, relief=tk.FLAT
            )
        avatar.pack(side=tk.LEFT, anchor=tk.NW, padx=(0, 2))

        # 气泡容器
        bubble_wrap = tk.Frame(row, bg=self.AI_BUBBLE_BORDER, bd=0)
        bubble_inner = tk.Frame(bubble_wrap, bg=self.AI_BUBBLE_BG, padx=16, pady=12)
        bubble_inner.pack(padx=1, pady=1)
        bubble_wrap.pack(side=tk.LEFT, anchor=tk.NW, padx=(6, 40))

        # 三个点（用 Label 显示，通过改文字实现跳动）
        dots = []
        for i in range(3):
            lbl = tk.Label(
                bubble_inner, text="·",
                font=("Microsoft YaHei", 14, "bold"),
                bg=self.AI_BUBBLE_BG, fg="#888888",
                width=1
            )
            lbl.pack(side=tk.LEFT, padx=1)
            dots.append(lbl)

        # ===== 让整行思考气泡区域也响应鼠标滚轮 =====
        self._bind_wheel_recursive(row)

        # 保存引用，方便后续移除
        self._thinking_bubble_row = row
        self._thinking_dots = dots
        self._thinking_dot_index = 0

        # 启动动画
        self._animate_thinking_dots()
        self._scroll_chat_to_bottom()

    def _animate_thinking_dots(self):
        """三个点循环跳动：当前点变大变深，其它变浅"""
        try:
            # 若气泡已被移除，停止动画
            if not getattr(self, "_thinking_bubble_row", None):
                return
            if not self._thinking_bubble_row.winfo_exists():
                return

            dots = getattr(self, "_thinking_dots", [])
            if not dots:
                return

            idx = getattr(self, "_thinking_dot_index", 0) % 3
            for i, lbl in enumerate(dots):
                if i == idx:
                    lbl.config(text="•", fg="#0C8CE9",
                               font=("Microsoft YaHei", 16, "bold"))
                else:
                    lbl.config(text="·", fg="#BBBBBB",
                               font=("Microsoft YaHei", 12, "bold"))
            self._thinking_dot_index = idx + 1

            self._thinking_anim_timer = self.after(300, self._animate_thinking_dots)
        except Exception:
            pass

    def _remove_thinking_bubble(self):
        """移除思考气泡"""
        # 先停动画
        t = getattr(self, "_thinking_anim_timer", None)
        if t:
            try:
                self.after_cancel(t)
            except Exception:
                pass
            self._thinking_anim_timer = None

        row = getattr(self, "_thinking_bubble_row", None)
        if row is not None:
            try:
                if row.winfo_exists():
                    row.destroy()
            except Exception:
                pass
        self._thinking_bubble_row = None
        self._thinking_dots = []


class CollaborationDialog(tk.Toplevel):
    """AI 协作对话框"""

    def __init__(self, app):
        super().__init__(app.root)
        self.app = app
        self.title(tr("小電AI 工程协作", app))
        self.resizable(True, True)

        # 设置图标（可选）
        try:
            self.iconbitmap("img/icon.ico")
        except:
            pass

        # ---- 窗口居中：先 withdraw 隐藏窗口，设置 geometry 后再 deiconify ----
        self.withdraw()

        # 读取语法文档
        self.syntax_doc_simple = self._load_syntax_doc("CZEmidiMarkdown_S.md")
        self.syntax_doc_expert = self._load_syntax_doc("CZEmidiMarkdown.md")

        # 当前工程内容（字符串）
        self.project_content = None
        self._load_project_content()

        # 加载 AI 配置
        self.ai_config = load_ai_config()

        # 知识库模式：'none', 'simple', 'expert'
        self.knowledge_mode = tk.StringVar(value="simple")

        # 打字机相关变量
        self._typewriter_queue = []
        self._typewriter_timer = None
        self._typing_active = False

        # 待发送的引用
        self._references = {}

        # 创建 UI
        self._create_widgets()

        # 状态变量
        self._ai_thread = None
        self._is_processing = False

        # 设置默认字体
        default_font = ("Microsoft YaHei", 10)
        self.option_add("*Font", default_font)

        self.transient(app.root)

        # ---- 计算居中位置并设置 geometry ----
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        win_width = 700
        win_height = 750
        x = (screen_width - win_width) // 2
        y = (screen_height - win_height) // 2
        self.geometry(f"{win_width}x{win_height}+{x}+{y}")

        # ---- 绑定窗口关闭：清掉 app 上的引用，避免下次点菜单拿到已销毁的窗口 ----
        self.protocol("WM_DELETE_WINDOW", self._on_dialog_close)

        # ---- 显示窗口 ----
        self.deiconify()
        self.focus_force()

    def _on_dialog_close(self):
        """关闭对话框：清理 app 上挂的引用，然后销毁自己"""
        try:
            if getattr(self.app, "_collaboration_dialog", None) is self:
                self.app._collaboration_dialog = None
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass

    def _toggle_topmost(self):
        """切换窗口置顶状态"""
        try:
            self._is_topmost = not self._is_topmost
            self.attributes("-topmost", self._is_topmost)
            self._update_topmost_btn_color()
            if self._is_topmost:
                self.lift()
        except Exception as _e:
            print(f"[小電AI] 切换置顶失败: {_e}")

    def _update_topmost_btn_color(self):
        """根据当前置顶状态更新按钮颜色"""
        try:
            if getattr(self, "_is_topmost", False):
                self.topmost_btn.config(fg="#0C8CE9")
            else:
                self.topmost_btn.config(fg="#999999")
        except Exception:
            pass

    def _load_syntax_doc(self, filename="CZEmidiMarkdown_S.md"):
        """读取指定的语法文档文件"""
        # 优先使用 exe 同级的目录，兜底使用开发环境的当前文件目录
        base_dir = os.environ.get('ITOC_APP_DIR', '')
        if not base_dir or not os.path.isdir(base_dir):
            base_dir = os.path.dirname(os.path.abspath(__file__))

        doc_path = os.path.join(base_dir, filename)
        if os.path.exists(doc_path):
            try:
                with open(doc_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except:
                return "（无法读取语法文档）"
        else:
            return tr("（{filename} 文件未找到，请确保该文件存在于程序根目录）", self.app).format(filename=filename)

    def _load_project_content(self):
        """从主程序内存中加载当前工程 JSON 内容为字符串"""
        try:
            project_data = self.app._build_snapshot_data()
            if not project_data:
                raise ValueError("主程序返回的快照数据为空")
            self.project_content = json.dumps(project_data, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror(tr("错误", self.app), tr("无法获取内存工程数据：{error}", self.app).format(error=str(e)))
            self.destroy()

    def _create_widgets(self):
        """构建界面（全部控件使用微软雅黑，增加知识库单选框和进度条）"""
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 定义字体
        font_label = ("Microsoft YaHei", 10)
        font_text = ("Microsoft YaHei", 10)

        # ================= 1. 优先固定底部（防止窗口缩小时被裁切） =================
        # ---- 状态栏（最底部） ----
        self.status_var = tk.StringVar(value=tr("就绪", self.app))
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, font=font_label)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))

        # ---- 按钮行 + 进度条（状态栏上方） ----
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

        self.send_btn = ttk.Button(btn_frame, text=tr("发送", self.app), command=self._on_send)
        self.send_btn.pack(side=tk.LEFT, padx=5)

        self.progress_label = ttk.Label(btn_frame, text="", foreground="blue", font=font_label)
        self.progress_label.pack(side=tk.LEFT, padx=10)

        self.progress_bar = ttk.Progressbar(btn_frame, mode='indeterminate', length=150)
        self.progress_bar.pack(side=tk.LEFT, padx=5)
        self.progress_bar.pack_forget()  # 默认隐藏

        # ================= 2. 其次固定顶部 =================
        # ---- 顶部标题栏已移除（此窗口不需要置顶功能） ----
        self._is_topmost = False

        # ---- 知识库模式单选框 ----
        kb_frame = ttk.LabelFrame(main_frame, text=tr("📚 知识库模式", self.app), padding="5")
        kb_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 8))

        kb_inner = ttk.Frame(kb_frame)
        kb_inner.pack(anchor=tk.W)

        ttk.Radiobutton(kb_inner, text=tr("无知识库", self.app), variable=self.knowledge_mode,
                        value="none").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(kb_inner, text=tr("Itoc知识库（简单）", self.app), variable=self.knowledge_mode,
                        value="simple").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(kb_inner, text=tr("Itoc知识库（专家）", self.app), variable=self.knowledge_mode,
                        value="expert").pack(side=tk.LEFT)

        # ---- 模型选择 ----
        model_frame = ttk.LabelFrame(main_frame, text=tr("AI 模型", self.app), padding="5")
        model_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 8))
        model_inner = ttk.Frame(model_frame)
        model_inner.pack(anchor=tk.W, fill=tk.X)
        ttk.Label(model_inner, text=tr("选择模型：", self.app), font=font_label).pack(side=tk.LEFT)
        self.model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(model_inner, textvariable=self.model_var, state="readonly", width=40)
        self.model_combo.pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)
        # 填充模型列表
        models = self.ai_config.get("models", [])
        model_display = [f"{m['name']} ({m['id']})" for m in models]
        self.model_combo["values"] = model_display
        current_id = self.ai_config.get("current_model", "")
        for m in models:
            if m['id'] == current_id:
                self.model_var.set(f"{m['name']} ({m['id']})")
                break
        if not self.model_var.get() and model_display:
            self.model_var.set(model_display[0])

        def on_model_change(event=None):
            sel = self.model_var.get()
            for m in models:
                if sel == f"{m['name']} ({m['id']})":
                    self.ai_config["current_model"] = m['id']
                    save_ai_config(self.ai_config)
                    print(f"[AI协作] 切换模型为: {m['id']}")
                    break
        self.model_combo.bind("<<ComboboxSelected>>", on_model_change)

        # ================= 3. 中间核心响应式区域 (PanedWindow 上下可拖动分割) =================
        paned = tk.PanedWindow(main_frame, orient=tk.VERTICAL, sashwidth=6, sashrelief=tk.RAISED)
        paned.pack(fill=tk.BOTH, expand=True, pady=5)

        # ---- 上半部分：用户输入区 ----
        input_pane = ttk.Frame(paned)
        paned.add(input_pane, stretch="always")

        ttk.Label(input_pane, text=tr("请输入修改指令（例如：将窗口编组“魔理沙”绑定到svg阵列“bad apple”）：", self.app),
                  font=font_label).pack(anchor=tk.W)

        # 输入框，最小3行，跟随拉伸，不会被裁没
        self.input_text = scrolledtext.ScrolledText(input_pane, height=3, font=("Microsoft YaHei", 10))
        self.input_text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.input_text.focus_set()

        # ---- 引用按钮区 & 卡片区 ----
        self._init_reference_area(input_pane)

        # ---- 下半部分：AI 响应预览区 ----
        response_pane = ttk.Frame(paned)
        paned.add(response_pane, stretch="always")

        ttk.Label(response_pane, text=tr("AI 返回的修改方案：", self.app),
                  font=font_label).pack(anchor=tk.W)

        # 响应框，最小5行，跟随拉伸，自带内部滚动条
        self.response_text = tk.Text(response_pane, height=5, font=("Microsoft YaHei", 10),
                                     bg="#f8f8f8", state=tk.DISABLED,
                                     wrap=tk.WORD, relief=tk.SUNKEN, bd=1)
        self.response_text.pack(fill=tk.BOTH, expand=True, pady=5)

        # ---- 操作按钮 ----
        action_frame = ttk.Frame(response_pane)
        action_frame.pack(fill=tk.X, pady=5)

        self.apply_btn = ttk.Button(action_frame, text=tr("应用修改", self.app), command=self._apply_modifications,
                                    state=tk.DISABLED)
        self.apply_btn.pack(side=tk.LEFT, padx=5)

        self.clear_btn = ttk.Button(action_frame, text=tr("》", self.app), command=self._skip_typewriter)
        self.clear_btn.pack(side=tk.LEFT, padx=5)

    # ---------- 核心逻辑 ----------
    def _on_send(self):
        """发送用户指令（含调试输出，显示进度条）"""
        print("[AI协作] _on_send 被调用")
        if self._is_processing:
            print("[AI协作] 正在处理中，忽略重复点击")
            return

        user_input = self.input_text.get("1.0", tk.END).strip()
        has_refs = bool(self._references)
        print(f"[AI协作] 用户输入：{user_input}, 是否有引用：{has_refs}")
        if not user_input and not has_refs:
            print("[AI协作] 输入为空，警告用户")
            messagebox.showwarning(tr("输入为空", self.app), tr("请输入修改指令", self.app))
            return

        if not user_input and has_refs:
            user_input = "请分析以下我引用的内容。"

        # 构建包含引用的最终输入
        final_input = self._compose_message_with_references(user_input)

        # 禁用按钮，显示进度
        self._is_processing = True
        self.send_btn.config(state=tk.DISABLED)
        self.apply_btn.config(state=tk.DISABLED)
        self.progress_label.config(text=tr("AI 思考中...", self.app))
        self.status_var.set(tr("正在请求 AI...", self.app))
        print("[AI协作] 开始请求 AI...")

        # 显示进度条并启动动画
        self.progress_bar.pack(side=tk.LEFT, padx=5)
        self.progress_bar.start(10)

        # 清空旧响应
        self._clear_response()

        # 仅清空引用卡片，保留输入框内容
        self._clear_reference_cards()

        # 启动后台线程
        self._ai_thread = threading.Thread(target=self._ai_request, args=(final_input,), daemon=True)
        self._ai_thread.start()
        print("[AI协作] 后台线程已启动")

    def _ai_request(self, user_input):
        """在后台线程中调用 AI API（含详细调试输出）"""
        print("[AI协作] _ai_request 开始执行")
        try:
            # 构造消息
            print("[AI协作] 正在构造用户消息...")
            user_message = self._build_user_message(user_input)
            print(f"[AI协作] 用户消息长度：{len(user_message)} 字符")
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ]
            print(f"[AI协作] 系统提示词长度：{len(SYSTEM_PROMPT)} 字符")
            print("[AI协作] 准备调用 OpenAI API...")

            # 调用 OpenAI 兼容 API
            from openai import OpenAI
            # 从配置读取
            api_key = self.ai_config.get("api_key", API_KEY)
            base_url = self.ai_config.get("base_url", BASE_URL)
            model = self.ai_config.get("current_model", MODEL)
            client = OpenAI(api_key=api_key, base_url=base_url)
            print("[AI协作] OpenAI 客户端创建成功")
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                stream=False,
                timeout=90
            )
            print("[AI协作] API 调用成功，获得响应")

            ai_reply = response.choices[0].message.content
            print(f"[AI协作] AI 回复长度：{len(ai_reply)} 字符")
            print(f"[AI协作] AI 回复前100字符：{ai_reply[:100]}...")

            # 在主线程更新 UI
            self.app.root.after(0, self._on_ai_response, ai_reply)
            print("[AI协作] UI 更新已调度")

        except Exception as e:
            error_msg = f"AI 请求失败：{str(e)}"
            print(f"[AI协作] 错误：{error_msg}")
            import traceback
            traceback.print_exc()
            self.app.root.after(0, self._on_ai_error, error_msg)

    def _build_user_message(self, user_input):
        """构造发送给 AI 的用户消息（根据知识库模式选择文档）"""
        print("[AI协作] _build_user_message 开始构造")
        print(f"[AI协作] 当前知识库模式: {self.knowledge_mode.get()}")

        # 根据知识库模式选择语法文档
        mode = self.knowledge_mode.get()
        if mode == "none":
            syntax_content = "（未启用知识库）"
        elif mode == "simple":
            syntax_content = self.syntax_doc_simple
        else:  # expert
            syntax_content = self.syntax_doc_expert

        parts = [
            "下面是当前工程文件的完整 JSON 数据（请据此定位修改目标）：",
            "```json",
            self.project_content,
            "```",
            "",
            "下面是 CZE 工程语法说明文档：",
            "```markdown",
            syntax_content,
            "```",
            "",
            "用户指令：",
            user_input
        ]
        result = "\n".join(parts)
        print(f"[AI协作] 构造完成，总长度：{len(result)} 字符")
        print(f"[AI协作] 知识库长度：{len(syntax_content)} 字符")
        return result

    def _on_ai_response(self, reply):
        """AI 响应成功（含调试输出，打字机效果）"""
        print("[AI协作] _on_ai_response 被调用")


        self.progress_bar.stop()
        self.progress_bar.pack_forget()

        self._is_processing = False
        self.send_btn.config(state=tk.NORMAL)
        self.progress_label.config(text="")
        self.status_var.set(tr("AI 响应完成", self.app))
        print("[AI协作] UI 状态已恢复")

        # ---- 打字机效果 ----
        # 启用文本框
        self.response_text.config(state=tk.NORMAL)
        self.response_text.delete("1.0", tk.END)

        # 将回复内容放入队列
        self._typewriter_queue = list(reply)
        self._typing_active = True

        # 启动打字机定时器（每 15ms 打一个字）
        if self._typewriter_timer:
            try:
                self._typewriter_timer.stop()
            except:
                pass
        self._typewriter_timer = None
        self._type_step()

        # 检查是否包含 Search/Replace
        if "【Search】" in reply and "【Replace】" in reply:
            self.apply_btn.config(state=tk.NORMAL)
            print("[AI协作] 检测到 Search/Replace，应用按钮已启用")
        else:
            self.apply_btn.config(state=tk.DISABLED)
            print("[AI协作] 未检测到 Search/Replace")
            if "【Error】" in reply:
                error_msg = reply.split("【Error】")[-1].strip()
                self.status_var.set(tr("AI 返回错误：{error}", self.app).format(error=error_msg))
                print(f"[AI协作] AI 返回错误：{error_msg}")
            else:
                self.status_var.set(tr("未检测到有效的 Search/Replace 对", self.app))

    def _type_step(self):
        """打字机效果步进函数"""
        if not self._typewriter_queue:
            self._typing_active = False
            self.response_text.config(state=tk.DISABLED)
            return

        char = self._typewriter_queue.pop(0)
        self.response_text.insert(tk.END, char)
        self.response_text.see(tk.END)  # 自动滚动到底部

        # 每 15ms 打一个字，感觉流畅
        self._typewriter_timer = self.after(15, self._type_step)

    def _on_ai_error(self, error_msg):
        """AI 请求失败（含调试输出，隐藏进度条）"""
        print(f"[AI协作] _on_ai_error 被调用，错误信息：{error_msg}")


        self.progress_bar.stop()
        self.progress_bar.pack_forget()

        self._is_processing = False
        self.send_btn.config(state=tk.NORMAL)
        self.progress_label.config(text="")
        self.status_var.set(tr("错误", self.app))
        messagebox.showerror(tr("AI 错误", self.app), error_msg)
        print("[AI协作] 错误已显示给用户")

    # ---------- 引用功能 ----------
    def _init_reference_area(self, parent):
        """初始化待发送引用区（按钮行 + 卡片区）。"""

        self.ref_btn_row = tk.Frame(parent, bg="#FFFFFF")
        self.ref_btn_row.pack(fill=tk.X, pady=(0, 5))

        def _make_ref_btn(text, cmd):
            btn = tk.Button(
                self.ref_btn_row, text=text,
                font=("Microsoft YaHei", 9),
                bg="#F0F2F5", fg="#333333",
                activebackground="#E0E4EA",
                relief=tk.FLAT, bd=0, padx=10, pady=4,
                cursor="hand2",
                command=cmd,
            )
            return btn

        self.ref_project_btn = _make_ref_btn("📄 引用工程", self._on_reference_project)
        self.ref_project_btn.pack(side=tk.LEFT, padx=(0, 4))

        self.ref_notes_btn = _make_ref_btn("🎵 引用事件块", self._on_reference_selected_notes)
        self.ref_notes_btn.pack(side=tk.LEFT, padx=(0, 4))

        self.ref_timesel_btn = _make_ref_btn("⏱ 引用时间选区", self._on_reference_time_selection)
        self.ref_timesel_btn.pack(side=tk.LEFT)

        # 悬浮效果
        def _on_btn_enter(e, w):
            try:
                if w['state'] != tk.DISABLED:
                    w.config(bg="#E0E4EA")
            except Exception:
                pass

        def _on_btn_leave(e, w):
            try:
                if w['state'] != tk.DISABLED:
                    w.config(bg="#F0F2F5")
            except Exception:
                pass

        for b in (self.ref_project_btn, self.ref_notes_btn, self.ref_timesel_btn):
            b.bind("<Enter>", lambda e, w=b: _on_btn_enter(e, w))
            b.bind("<Leave>", lambda e, w=b: _on_btn_leave(e, w))

        # 初始化时如果没工程，全部禁用
        if not getattr(self.app, 'current_project_path', None):
            for b in (self.ref_project_btn, self.ref_notes_btn, self.ref_timesel_btn):
                b.config(state=tk.DISABLED, fg="#AAAAAA")

        # ===== 待发送引用区（卡片列表，在按钮行下方） =====
        self.reference_area = tk.Frame(parent, bg="#FFFFFF")
        self.reference_area.pack(fill=tk.X, pady=(0, 5))
        self.reference_area.pack_forget()  # 初始隐藏

        self.reference_header_label = tk.Label(
            self.reference_area,
            text="待发送的引用",
            font=("Microsoft YaHei", 9, "bold"),
            bg="#FFFFFF", fg="#666666",
            anchor="w"
        )

        self.reference_inner = tk.Frame(self.reference_area, bg="#FFFFFF")

    def _compose_message_with_references(self, user_input):
        """将引用内容和用户输入拼装成最终消息。"""
        if not self._references:
            return user_input

        parts = ["【用户指令】", user_input, "", "【用户引用的上下文】"]
        for ref_type in ('project', 'selected_notes', 'time_selection'):
            ref = self._references.get(ref_type)
            if ref:
                parts.append("")
                parts.append(f"=== {ref['title']} ===")
                parts.append(ref['content'])

        return "\n".join(parts)

    def _on_reference_project(self):
        """点击「引用工程」按钮。"""
        app = self.app
        if not getattr(app, 'current_project_path', None):
            messagebox.showwarning("提示", "请先打开一个工程", parent=self)
            return

        include_full_json_var = tk.BooleanVar(value=False)

        def _extra_options(win, main, refs, text_widget, size_label):
            cb_frame = ttk.Frame(main)
            cb_frame.pack(fill=tk.X, pady=(6, 0))
            ttk.Checkbutton(
                cb_frame,
                text="⚠️ 同时包含完整工程 JSON（可能占用大量 token）",
                variable=include_full_json_var,
                style="Preview.TCheckbutton"
            ).pack(anchor=tk.W)

            def _refresh(*args):
                content = self._build_project_reference_text(include_full_json_var.get())
                text_widget.config(state=tk.NORMAL)
                text_widget.delete("1.0", tk.END)
                text_widget.insert("1.0", content)
                text_widget.config(state=tk.DISABLED)
                size_label.config(text=f"预计内容大小：约 {len(content)} 字符")

            include_full_json_var.trace_add("write", _refresh)

        initial_content = self._build_project_reference_text(False)

        def _on_confirm(option_refs, final_content):
            title = "当前工程摘要"
            subtitle = os.path.basename(app.current_project_path) or "工程"
            if include_full_json_var.get():
                subtitle += "（含完整 JSON）"
            self._add_reference_card('project', title, subtitle, final_content)

        self._show_reference_preview("引用预览 - 当前工程", initial_content, _on_confirm, _extra_options)

    def _on_reference_selected_notes(self):
        """点击「引用事件块」按钮。"""
        app = self.app
        selected = list(getattr(app, 'selected_notes', []))
        if not selected:
            messagebox.showwarning("提示", "请先在主界面选中至少一个音符块或调整图层哦～", parent=self)
            return

        content = self._build_selected_notes_reference_text()
        if not content:
            messagebox.showinfo("提示", "选中的内容无法构造为引用", parent=self)
            return

        def _on_confirm(option_refs, final_content):
            n = len(selected)
            self._add_reference_card(
                'selected_notes',
                f"选中的 {n} 个事件块",
                "来自主界面当前选中",
                final_content
            )

        self._show_reference_preview(
            f"引用预览 - 选中的 {len(selected)} 个事件块",
            content, _on_confirm
        )

    def _on_reference_time_selection(self):
        """点击「引用时间选区」按钮。"""
        app = self.app
        ts = getattr(app, 'time_sel', None)
        if ts is None or not (ts.start_x > 0 and ts.end_x > 0 and ts.start_x < ts.end_x):
            messagebox.showwarning("提示", "请先在主界面按 F4 画一个时间选区哦～", parent=self)
            return

        mode_var = tk.StringVar(value='simple')

        def _extra_options(win, main, refs, text_widget, size_label):
            mode_frame = ttk.Frame(main)
            mode_frame.pack(fill=tk.X, pady=(6, 0))
            ttk.Radiobutton(mode_frame, text="简要列表（推荐）", variable=mode_var, value='simple', style="Preview.TRadiobutton").pack(side=tk.LEFT)
            ttk.Radiobutton(mode_frame, text="详细展开", variable=mode_var, value='detailed', style="Preview.TRadiobutton").pack(side=tk.LEFT, padx=10)

            def _refresh(*args):
                content = self._build_time_selection_reference_text(mode_var.get())
                if not content:
                    content = "（范围内没有事件块）"
                text_widget.config(state=tk.NORMAL)
                text_widget.delete("1.0", tk.END)
                text_widget.insert("1.0", content)
                text_widget.config(state=tk.DISABLED)
                size_label.config(text=f"预计内容大小：约 {len(content)} 字符")

            mode_var.trace_add("write", _refresh)

        initial_content = self._build_time_selection_reference_text('simple')
        if not initial_content:
            initial_content = "（范围内没有事件块）"

        def _on_confirm(option_refs, final_content):
            try:
                bpm_ratio = app.midi_original_bpm / app.target_bpm if app.target_bpm > 0 else 1.0
                scaled_beat_width = app.beat_width * app.scale_factor_x * bpm_ratio
                start_x_px = 50 * app.scale_factor_x
                sb = (ts.start_x - start_x_px) / scaled_beat_width if scaled_beat_width > 0 else 0
                eb = (ts.end_x - start_x_px) / scaled_beat_width if scaled_beat_width > 0 else 0
                beat_range = f"节拍 {sb:.2f} ~ {eb:.2f}"
            except Exception:
                beat_range = "时间选区"
            self._add_reference_card(
                'time_selection',
                f"时间选区 {beat_range}",
                "范围内事件块",
                final_content
            )

        self._show_reference_preview(
            "引用预览 - 时间选区",
            initial_content, _on_confirm, _extra_options
        )

    def _build_project_reference_text(self, include_full_json=False):
        """构造工程摘要引用文本。"""
        app = self.app
        lines = ["### 当前工程概览"]
        try:
            project_name = os.path.basename(app.current_project_path or '')
        except Exception:
            project_name = ''
        lines.append(f"- 工程名：{project_name}")
        lines.append(f"- 当前 BPM：{getattr(app, 'target_bpm', '?')}（原速 {getattr(app, 'midi_original_bpm', '?')}）")
        lines.append(f"- 总节拍：{getattr(app, 'midi_total_beat', '?')}")
        all_notes = getattr(app, 'all_notes', [])
        lines.append(f"- 音符块：{len(all_notes)} 个")

        tracks = set()
        for nd in all_notes:
            if len(nd) >= 5:
                tracks.add(nd[0])
        lines.append(f"- 轨道数：{len(tracks)}")

        adjust_layers = getattr(app, 'adjust_layers', []) or []
        lines.append(f"- 调整图层：{len(adjust_layers)} 个")

        try:
            if getattr(app, 'marker_manager', None):
                lines.append(f"- 标记：{app.marker_manager.get_marker_count()} 个")
            else:
                lines.append("- 标记：0 个")
        except Exception:
            lines.append("- 标记：?")

        try:
            if getattr(app, 'global_command_manager', None):
                lines.append(f"- 全局命令：{app.global_command_manager.get_command_count()} 条")
            else:
                lines.append("- 全局命令：0 条")
        except Exception:
            lines.append("- 全局命令：?")

        lines.append(f"- 阵列：{len(getattr(app, 'arrays', []) or [])} 个")

        # 时间选区
        ts = getattr(app, 'time_sel', None)
        if ts and (ts.start_x > 0 or ts.end_x > 0):
            try:
                bpm_ratio = app.midi_original_bpm / app.target_bpm if app.target_bpm > 0 else 1.0
                scaled_beat_width = app.beat_width * app.scale_factor_x * bpm_ratio
                start_x_px = 50 * app.scale_factor_x
                if scaled_beat_width > 0:
                    sb = (ts.start_x - start_x_px) / scaled_beat_width
                    eb = (ts.end_x - start_x_px) / scaled_beat_width
                    lines.append(f"- 时间选区：节拍 {sb:.2f} ~ {eb:.2f}")
                else:
                    lines.append("- 时间选区：（无）")
            except Exception:
                lines.append("- 时间选区：（无）")
        else:
            lines.append("- 时间选区：（无）")

        lines.append(f"- 当前选中：{len(getattr(app, 'selected_notes', []) or [])} 个")

        if include_full_json:
            try:
                with open(app.current_project_path, 'r', encoding='utf-8') as f:
                    full_json = f.read()
                lines.append("")
                lines.append("### 完整工程 JSON")
                lines.append("```json")
                lines.append(full_json)
                lines.append("```")
            except Exception as e:
                lines.append("")
                lines.append(f"（读取完整 JSON 失败：{e}）")

        return "\n".join(lines)

    def _build_selected_notes_reference_text(self):
        """构造选中事件块引用文本。"""
        app = self.app
        selected = list(getattr(app, 'selected_notes', []) or [])
        if not selected:
            return None

        adjust_layers = getattr(app, 'adjust_layers', []) or []
        layer_id_set = set()
        for ly in adjust_layers:
            if isinstance(ly, dict) and 'id' in ly:
                layer_id_set.add(ly['id'])

        lines = [f"### 引用：选中的 {len(selected)} 个事件块", ""]

        idx = 0
        for sid in selected:
            idx += 1
            if sid in layer_id_set:
                layer = next((ly for ly in adjust_layers if ly.get('id') == sid), None)
                if layer:
                    lines.append(f"#### 事件块 {idx}（调整图层）")
                    lines.append(f"- 轨道：{layer.get('track_idx', 0) + 1}")
                    sb = layer.get('start_beat', 0)
                    dur = layer.get('duration', 0)
                    lines.append(f"- 节拍：{sb:.2f} ~ {sb + dur:.2f}（{dur:.2f} 拍）")
                    color = layer.get('color', '')
                    if color:
                        lines.append(f"- 颜色：{color}")
                    ep = layer.get('effect_params', {})
                    if ep:
                        try:
                            lines.append(f"- 效果参数：{json.dumps(ep, ensure_ascii=False)}")
                        except Exception:
                            lines.append(f"- 效果参数：{ep}")
                    lines.append("")
            else:
                nd = next((d for d in app.all_notes if len(d) >= 5 and d[4] == sid), None)
                if nd:
                    lines.append(f"#### 事件块 {idx}（音符块）")
                    lines.append(f"- 轨道：{nd[0] + 1}")
                    sb, dur, nv = nd[1], nd[2], nd[3]
                    lines.append(f"- 节拍：{sb:.2f} ~ {sb + dur:.2f}（{dur:.2f} 拍）")
                    lines.append(f"- 音高：{nv}")
                    color = getattr(app, 'note_color_map', {}).get(sid, '')
                    if color:
                        lines.append(f"- 颜色：{color}")
                    custom_text = getattr(app, 'note_custom_text', {}).get(sid, '')
                    if custom_text:
                        lines.append(f"- 自定义文本：{custom_text}")
                    cze = nd[5] if len(nd) >= 6 else {}
                    if cze and isinstance(cze, dict) and len(cze) > 0:
                        lines.append(f"- 配参：")
                        for k, v in cze.items():
                            lines.append(f"  {k}: {v}")
                    transition = nd[6] if len(nd) >= 7 else None
                    if transition:
                        try:
                            lines.append(f"- 过渡：{json.dumps(transition, ensure_ascii=False)}")
                        except Exception:
                            lines.append(f"- 过渡：{transition}")
                    disabled = nd[7] if len(nd) >= 8 else False
                    lines.append(f"- 禁用：{'是' if disabled else '否'}")
                    lines.append("")

        return "\n".join(lines)

    def _build_time_selection_reference_text(self, mode='simple'):
        """构造时间选区引用文本。mode 可选 'simple' 或 'detailed'。"""
        app = self.app
        ts = getattr(app, 'time_sel', None)
        if ts is None or not (ts.start_x > 0 or ts.end_x > 0):
            return None

        bpm_ratio = app.midi_original_bpm / app.target_bpm if app.target_bpm > 0 else 1.0
        scaled_beat_width = app.beat_width * app.scale_factor_x * bpm_ratio
        start_x_px = 50 * app.scale_factor_x
        if scaled_beat_width <= 0:
            return None
        sb = (ts.start_x - start_x_px) / scaled_beat_width
        eb = (ts.end_x - start_x_px) / scaled_beat_width

        events = []
        for nd in getattr(app, 'all_notes', []):
            if len(nd) >= 5:
                s, d = nd[1], nd[2]
                e = s + d
                if e > sb and s < eb:
                    events.append(('note', nd))
        for ly in getattr(app, 'adjust_layers', []) or []:
            if not isinstance(ly, dict):
                continue
            s = ly.get('start_beat', 0)
            d = ly.get('duration', 0)
            e = s + d
            if e > sb and s < eb:
                events.append(('layer', ly))

        if mode == 'detailed':
            if getattr(app, 'global_command_manager', None):
                try:
                    cmds = app.global_command_manager.get_commands_data()
                    for cmd in cmds:
                        c_beat = cmd.get('beat', 0)
                        if 'start_beat' in cmd: c_beat = cmd['start_beat']
                        elif 'position' in cmd: c_beat = cmd['position']
                        if sb <= c_beat <= eb:
                            events.append(('command', cmd))
                except Exception as e:
                    print(f"获取全局命令失败: {e}")

            if getattr(app, 'marker_manager', None):
                try:
                    markers = app.marker_manager.get_markers_data()
                    for m in markers:
                        m_beat = m.get('beat', 0)
                        if sb <= m_beat <= eb:
                            events.append(('marker', m))
                except Exception as e:
                    print(f"获取标记失败: {e}")

        def _sort_key(item):
            t, data = item
            if t == 'note':
                return data[1]
            elif t == 'layer':
                return data.get('start_beat', 0)
            elif t == 'command':
                return data.get('start_beat', data.get('beat', data.get('position', 0)))
            elif t == 'marker':
                return data.get('beat', 0)
            return 0

        events.sort(key=_sort_key)

        note_count = sum(1 for t, _ in events if t == 'note')
        layer_count = sum(1 for t, _ in events if t == 'layer')
        cmd_count = sum(1 for t, _ in events if t == 'command')
        marker_count = sum(1 for t, _ in events if t == 'marker')

        type_desc_parts = []
        if note_count > 0: type_desc_parts.append(f"音符块 {note_count} 个")
        if layer_count > 0: type_desc_parts.append(f"调整图层 {layer_count} 个")
        if cmd_count > 0: type_desc_parts.append(f"全局命令 {cmd_count} 个")
        if marker_count > 0: type_desc_parts.append(f"标记 {marker_count} 个")

        type_desc = "，".join(type_desc_parts) if type_desc_parts else "无"

        lines = [
            f"### 引用：时间选区 节拍 {sb:.2f} ~ {eb:.2f}",
            f"范围内共 {len(events)} 个事件（{type_desc}）",
            ""
        ]

        if mode == 'simple':
            for i, (t, data) in enumerate(events, 1):
                if t == 'note':
                    s, d, nv = data[1], data[2], data[3]
                    lines.append(f"{i}. [音符] 轨道 {data[0] + 1}，节拍 {s:.2f} ~ {s + d:.2f}，音高 {nv}")
                    cze = data[5] if len(data) >= 6 else {}
                    if cze and isinstance(cze, dict):
                        wt = cze.get('window_type', '')
                        if wt:
                            lines.append(f"   配参类型：{wt}")
                else:
                    s = data.get('start_beat', 0)
                    d = data.get('duration', 0)
                    lines.append(f"{i}. [调整图层] 轨道 {data.get('track_idx', 0) + 1}，节拍 {s:.2f} ~ {s + d:.2f}")
        else:
            for i, (t, data) in enumerate(events, 1):
                if t == 'note':
                    lines.append(f"#### 事件块 {i}（音符块）")
                    lines.append(f"- 轨道：{data[0] + 1}")
                    s, d, nv = data[1], data[2], data[3]
                    lines.append(f"- 节拍：{s:.2f} ~ {s + d:.2f}（{d:.2f} 拍）")
                    lines.append(f"- 音高：{nv}")
                    cze = data[5] if len(data) >= 6 else {}
                    if cze and isinstance(cze, dict) and len(cze) > 0:
                        lines.append(f"- 配参：")
                        for k, v in cze.items():
                            lines.append(f"  {k}: {v}")
                    lines.append("")
                elif t == 'layer':
                    lines.append(f"#### 事件块 {i}（调整图层）")
                    lines.append(f"- 轨道：{data.get('track_idx', 0) + 1}")
                    s = data.get('start_beat', 0)
                    d = data.get('duration', 0)
                    lines.append(f"- 节拍：{s:.2f} ~ {s + d:.2f}（{d:.2f} 拍）")
                    lines.append("")
                elif t == 'command':
                    c_beat = data.get('start_beat', data.get('beat', data.get('position', 0)))
                    lines.append(f"#### 事件块 {i}（全局命令）")
                    lines.append(f"- 节拍：{c_beat:.2f}")
                    lines.append(f"- 描述：{data.get('description', '')}")
                    lines.append(f"- 命令：{data.get('command', '')}")
                    lines.append("")
                elif t == 'marker':
                    lines.append(f"#### 事件块 {i}（标记）")
                    lines.append(f"- 节拍：{data.get('beat', 0):.2f}")
                    lines.append(f"- 描述：{data.get('description', '')}")
                    lines.append("")

        return "\n".join(lines)

    def _show_reference_preview(self, title, content, on_confirm, extra_options=None):
        """显示引用预览窗口。"""
        preview_win = tk.Toplevel(self)
        preview_win.title(title)
        preview_win.transient(self)
        preview_win.resizable(True, True)
        try:
            preview_win.iconbitmap("img/icon.ico")
        except Exception:
            pass
        preview_win.withdraw()

        w, h = 620, 460
        screen_w = preview_win.winfo_screenwidth()
        screen_h = preview_win.winfo_screenheight()
        x = (screen_w - w) // 2
        y = (screen_h - h) // 2
        preview_win.geometry(f"{w}x{h}+{x}+{y}")


        style = ttk.Style(preview_win)
        style.configure("Preview.TButton", font=("Microsoft YaHei", 10))
        style.configure("Preview.TCheckbutton", font=("Microsoft YaHei", 9))
        style.configure("Preview.TRadiobutton", font=("Microsoft YaHei", 9))

        main = ttk.Frame(preview_win, padding="10")
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text=title, font=("Microsoft YaHei", 11, "bold")).pack(anchor=tk.W, pady=(0, 8))

        text_frame = ttk.Frame(main)
        text_frame.pack(fill=tk.BOTH, expand=True)

        preview_text = tk.Text(
            text_frame, font=("Microsoft YaHei", 9), wrap=tk.WORD,
            bg="#F8F8F8", relief=tk.SUNKEN, bd=1, height=1
        )
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=preview_text.yview)
        preview_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        preview_text.insert("1.0", content)
        preview_text.config(state=tk.DISABLED)

        size_label = ttk.Label(main, text=f"预计内容大小：约 {len(content)} 字符", foreground="#666666")
        size_label.pack(anchor=tk.W, pady=(6, 0))

        option_refs = {}
        if extra_options:
            try:
                extra_options(preview_win, main, option_refs, preview_text, size_label)
            except Exception as e:
                print(f"[预览] extra_options 失败: {e}")
                import traceback
                traceback.print_exc()

        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        def _on_cancel():
            preview_win.destroy()

        def _on_ok():
            try:
                final_text = preview_text.get("1.0", tk.END).rstrip("\n")
                on_confirm(option_refs, final_text)
            except Exception as e:
                print(f"[预览] 确认回调失败: {e}")
                import traceback
                traceback.print_exc()
            preview_win.destroy()

        ttk.Button(btn_frame, text="确认引用", command=_on_ok, width=10, style="Preview.TButton").pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="取消", command=_on_cancel, width=10, style="Preview.TButton").pack(side=tk.RIGHT)

        preview_win.deiconify()
        preview_win.focus_force()
        preview_win.grab_set()
        preview_win.wait_window(preview_win)

    def _add_reference_card(self, ref_type, title, subtitle, content):
        """向待发送区添加/更新引用卡片。"""
        self._remove_reference_card(ref_type, silent=True)

        icon_map = {
            'project': '📄',
            'selected_notes': '🎵',
            'time_selection': '⏱',
        }

        card_frame = tk.Frame(
            self.reference_inner, bg="#FFF8E1",
            bd=0, highlightthickness=1, highlightbackground="#F0C36D"
        )
        card_frame.pack(fill=tk.X, pady=2)

        icon = tk.Label(
            card_frame, text=icon_map.get(ref_type, '📎'),
            font=("Microsoft YaHei", 11), bg="#FFF8E1"
        )
        icon.pack(side=tk.LEFT, padx=(8, 4), pady=4)

        text_frame = tk.Frame(card_frame, bg="#FFF8E1")
        text_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=4)

        title_label = tk.Label(
            text_frame, text=title,
            font=("Microsoft YaHei", 9, "bold"),
            bg="#FFF8E1", fg="#333333",
            anchor="w", cursor="hand2"
        )
        title_label.pack(anchor="w")

        sub_label = tk.Label(
            text_frame, text=subtitle,
            font=("Microsoft YaHei", 8),
            bg="#FFF8E1", fg="#888888",
            anchor="w", cursor="hand2"
        )
        sub_label.pack(anchor="w")

        def _on_click(e):
            self._show_reference_preview(
                f"引用详情 - {title}", content,
                lambda opts, txt: None
            )

        title_label.bind("<Button-1>", _on_click)
        sub_label.bind("<Button-1>", _on_click)
        text_frame.bind("<Button-1>", _on_click)

        close_btn = tk.Label(
            card_frame, text="×",
            font=("Arial", 12, "bold"),
            bg="#FFF8E1", fg="#888888",
            cursor="hand2", padx=8
        )
        close_btn.pack(side=tk.RIGHT, pady=4)
        close_btn.bind("<Button-1>", lambda e: self._remove_reference_card(ref_type))
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg="#FF4444"))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg="#888888"))

        self._references[ref_type] = {
            'title': title,
            'subtitle': subtitle,
            'content': content,
            'card_frame': card_frame,
        }

        self._update_reference_area_visibility()

    def _remove_reference_card(self, ref_type, silent=False):
        """移除指定类型的引用卡片。"""
        ref = self._references.pop(ref_type, None)
        if ref and ref.get('card_frame'):
            try:
                ref['card_frame'].destroy()
            except Exception:
                pass
        if not silent:
            self._update_reference_area_visibility()

    def _clear_reference_cards(self):
        """清空所有引用卡片。"""
        for rt in list(self._references.keys()):
            self._remove_reference_card(rt, silent=True)
        self._update_reference_area_visibility()

    def _update_reference_area_visibility(self):
        """更新引用区可见性和状态栏文字。"""
        try:
            count = len(self._references)
            if count > 0:
                self.reference_header_label.config(text=f"待发送的引用（{count} 条）")
                if not self.reference_area.winfo_ismapped():
                    self.reference_area.pack(fill=tk.X, pady=(0, 5))
                if not self.reference_header_label.winfo_ismapped():
                    self.reference_header_label.pack(fill=tk.X)
                if not self.reference_inner.winfo_ismapped():
                    self.reference_inner.pack(fill=tk.X)
                try:
                    self.update_idletasks()
                except Exception:
                    pass
            else:
                self.reference_area.pack_forget()
                try:
                    self.update_idletasks()
                except Exception:
                    pass
        except Exception as e:
            print(f"[引用] 更新可见性失败: {e}")

    def _parse_modifications(self, text):
        """
        从 AI 回复中解析 Search/Replace 对
        返回列表，每个元素是 (search, replace)
        支持多种格式：
        - 【Search】...【Replace】...
        - Search: ... Replace: ...
        - 纯文本块
        """
        print("[AI协作] _parse_modifications 开始解析")
        modifications = []

        # ---- 方法1：按【Search】/【Replace】分割 ----
        # 使用正则匹配所有 Search/Replace 对
        # 支持换行和任意字符
        pattern = r'【Search】\s*(.*?)\s*【Replace】\s*(.*?)(?=【Search】|$)'
        matches = re.findall(pattern, text, re.DOTALL)

        if matches:
            print(f"[AI协作] 使用【Search】/【Replace】格式解析，找到 {len(matches)} 对")
            for search, replace in matches:
                search_clean = search.strip()
                replace_clean = replace.strip()
                # 去除可能的 json 标记
                search_clean = self._clean_search_content(search_clean)
                replace_clean = self._clean_search_content(replace_clean)
                if search_clean:
                    modifications.append((search_clean, replace_clean))
                    print(f"[AI协作] 提取到修改: search长度={len(search_clean)}, replace长度={len(replace_clean)}")
            if modifications:
                return modifications

        # ---- 方法2：按行解析（兼容旧格式） ----
        print("[AI协作] 使用按行解析方式")
        lines = text.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith("【Search】"):
                search_line = line[len("【Search】"):].strip()
                if not search_line:
                    search_parts = []
                    i += 1
                    while i < len(lines) and not lines[i].strip().startswith("【Replace】"):
                        search_parts.append(lines[i])
                        i += 1
                    search_line = "\n".join(search_parts).strip()
                    if i >= len(lines):
                        break
                replace_line = lines[i].strip() if i < len(lines) else ""
                if replace_line.startswith("【Replace】"):
                    replace_content = replace_line[len("【Replace】"):].strip()
                    if not replace_content:
                        replace_parts = []
                        i += 1
                        while i < len(lines) and not lines[i].strip().startswith("【Search】"):
                            replace_parts.append(lines[i])
                            i += 1
                        replace_content = "\n".join(replace_parts).strip()
                        i -= 1
                    search_clean = self._clean_search_content(search_line)
                    replace_clean = self._clean_search_content(replace_content)
                    if search_clean:
                        modifications.append((search_clean, replace_clean))
                        print(f"[AI协作] 提取到修改 (按行): search长度={len(search_clean)}")
                i += 1
            else:
                i += 1

        print(f"[AI协作] _parse_modifications 完成，共 {len(modifications)} 处修改")
        return modifications

    def _clean_search_content(self, content):
        """
        清理 Search/Replace 内容：
        - 去除首尾空白
        - 去除开头的 json、``` 等标记
        - 去除结尾的 ``` 等标记
        - 确保内容是有效的 JSON 片段
        """
        if not content:
            return ""

        cleaned = content.strip()

        # 去除开头的 json 标记
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].lstrip()
        # 去除开头的 ```json 或 ``` 等标记
        if cleaned.startswith("```"):
            cleaned = cleaned[3:].lstrip()
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].lstrip()
        # 去除结尾的 ```
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].rstrip()

        # 再次去除首尾空白
        cleaned = cleaned.strip()

        # 如果内容是多行 JSON 片段，确保它是完整的键值对
        # 这里不做额外处理，让替换时自然匹配

        return cleaned

    def _apply_modifications(self):
        """应用所有 Search/Replace 修改（高容错、逐条验证、纯内存操作）"""
        print("[AI协作] _apply_modifications 被调用")

        # 从响应中解析
        response_content = self.response_text.get("1.0", tk.END).strip()
        mods = self._parse_modifications(response_content)
        if not mods:
            messagebox.showwarning(tr("无修改", self.app), tr("未找到有效的 Search/Replace 对", self.app))
            return

        try:
            # 直接从内存快照获取原始内容，不再读磁盘
            original_content = self.project_content
            content = original_content
            success_count = 0
            fail_list = []

            # 逐条应用与验证
            for i, (search, replace) in enumerate(mods):
                print(f"[AI协作] 执行替换 {i + 1}/{len(mods)}")
                temp_content = content
                matched = False

                # 第 1 层：精确匹配
                if search in temp_content:
                    temp_content = temp_content.replace(search, replace, 1)
                    matched = True
                else:
                    # 第 2 层：宽松匹配
                    import re
                    pattern_parts = re.split(r'\s+', search.strip())
                    if pattern_parts:
                        loose_pattern = r'\s*'.join(re.escape(p) for p in pattern_parts)
                        try:
                            match = re.search(loose_pattern, temp_content)
                            if match:
                                temp_content = temp_content[:match.start()] + replace + temp_content[match.end():]
                                matched = True
                        except Exception as ex:
                            print(f"[AI协作] 宽松匹配正则出错: {ex}")

                if not matched:
                    fail_list.append(f"第 {i+1} 条：未找到匹配的文本。")
                    continue

                # 单条验证 JSON
                try:
                    json.loads(temp_content)
                    content = temp_content  # 验证通过，正式接受
                    success_count += 1
                except json.JSONDecodeError as e:
                    fail_list.append(f"第 {i+1} 条：替换后导致 JSON 错误（{e.msg}），已自动撤销。")

            # 全部处理完毕，验证最终整体结果
            final_json_valid = False
            final_error_msg = ""
            try:
                json.loads(content)
                final_json_valid = True
            except json.JSONDecodeError as e:
                final_error_msg = str(e)

            # 如果全部成功且合法，直接应用到内存
            if success_count == len(mods) and final_json_valid:
                self._apply_to_memory(content)
                return

            # 如果有失败项或最终 JSON 损坏，弹出裁决面板
            self._show_result_dialog(content, success_count, fail_list, final_json_valid, final_error_msg, original_content, mods)

        except Exception as e:
            print(f"[AI协作] 应用失败：{str(e)}")
            import traceback
            traceback.print_exc()
            messagebox.showerror(tr("应用失败", self.app), tr("修改应用失败：{error}", self.app).format(error=str(e)))

    def _try_force_merge(self, original_content, mods, fail_list):
        """尝试强行合并（当找不到文本时，尝试将 Replace 解析为 JSON 并合并）"""
        try:
            content_dict = json.loads(original_content)
        except Exception as e:
            print(f"[强行合并] 原始 JSON 解析失败: {e}")
            return None

        merged_count = 0
        new_fail_list = list(fail_list)

        for i, (search, replace) in enumerate(mods):
            # 如果这条不在失败列表里，说明原本就成功了，跳过
            fail_flag = f"第 {i+1} 条：未找到匹配的文本。"
            if fail_flag not in new_fail_list:
                continue

            try:
                # 尝试把 Replace 解析为 JSON 对象
                # 如果 AI 给的是一整块带键的字典，比如 {"window_type": "info"}，可以直接合并
                # 如果 AI 给的只是一个值或者不完整的片段，这里会报错
                replace_dict = json.loads(replace)
                if isinstance(replace_dict, dict):
                    # 如果是字典，尝试直接合并到工程根节点（这能应对大部分新增字段的情况）
                    for k, v in replace_dict.items():
                        content_dict[k] = v
                    merged_count += 1
                    new_fail_list.remove(fail_flag)
                    print(f"[强行合并] 第 {i+1} 条：成功合并字典字段")
            except Exception as e:
                print(f"[强行合并] 第 {i+1} 条无法作为字典合并: {e}")

        if merged_count > 0:
            # 如果合并了东西，重新 dump 出来
            try:
                new_content = json.dumps(content_dict, ensure_ascii=False, indent=2)
                json.loads(new_content)  # 验证一次
                return new_content, new_fail_list
            except Exception as e:
                print(f"[强行合并] dump 后验证失败: {e}")
                return None
        return None
    def _apply_to_memory(self, content_str):
        """将修改后的 JSON 字符串应用回主程序的内存中，不写盘、不重新加载"""
        try:
            project_data = json.loads(content_str)
            # 调用主程序的 apply_snapshot_data 将数据恢复并重绘 UI
            self.app.apply_snapshot_data(project_data)
            # 标记工程已被修改（出现 * 号）
            self.app.mark_project_modified()
            self.destroy()
        except Exception as e:
            messagebox.showerror(tr("应用失败", self.app), tr("应用到内存失败：{error}", self.app).format(error=str(e)))
            import traceback
            traceback.print_exc()

    def _show_result_dialog(self, content, success_count, fail_list, final_json_valid, final_error_msg,
                            original_content, mods):
        """显示带有人工抉择的操作面板"""
        dialog = tk.Toplevel(self)
        dialog.title(tr("AI 修改结果与抉择", self.app))
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)

        # 居中
        dialog.update_idletasks()
        w, h = 600, 460
        x = self.winfo_x() + (self.winfo_width() - w) // 2
        y = self.winfo_y() + (self.winfo_height() - h) // 2
        dialog.geometry(f"{w}x{h}+{x}+{y}")

        main_frame = ttk.Frame(dialog, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 提示语
        ttk.Label(main_frame, text="⚠️ 修改执行完毕，但存在异常：", font=("Microsoft YaHei", 12, "bold"),
                  foreground="#D32F2F").pack(anchor=tk.W, pady=(0, 10))

        # 日志区
        log_text = tk.Text(main_frame, height=8, font=("Microsoft YaHei", 10), bg="#F8F8F8", wrap=tk.WORD, state=tk.NORMAL)
        log_text.pack(fill=tk.X, pady=(0, 10))

        log_text.insert(tk.END, f"✅ 成功应用了 {success_count} 处无错修改。\n\n")

        if fail_list:
            log_text.insert(tk.END, "❌ 以下修改未能成功应用或导致格式损坏已自动撤销：\n")
            for f in fail_list:
                log_text.insert(tk.END, f" - {f}\n")

        if not final_json_valid:
            log_text.insert(tk.END, f"\n🔥 最终 JSON 整体校验失败：\n{final_error_msg}\n")

        log_text.config(state=tk.DISABLED)

        # 复选框区
        chk_frame = tk.Frame(main_frame)
        chk_frame.pack(anchor=tk.W, pady=(0, 10))

        merge_var = tk.BooleanVar(value=True)
        cb_merge = ttk.Checkbutton(chk_frame, text="🪄 找不到匹配文本时，尝试强行合并以应用（仅限新增/修改字段）",
                                   variable=merge_var)
        cb_merge.pack(anchor=tk.W)

        # 按钮区
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

        def do_keep_success():
            self._apply_to_memory(content)
            dialog.destroy()

        def do_force_apply():
            final_content = content
            current_fail = list(fail_list)

            # 如果勾选了强行合并，尝试合并
            if merge_var.get():
                merge_result = self._try_force_merge(original_content, mods, current_fail)
                if merge_result:
                    final_content, current_fail = merge_result
                    pass

            # 检查合并后是否合法
            is_valid = False
            try:
                json.loads(final_content)
                is_valid = True
            except Exception:
                pass

            self._apply_to_memory(final_content)
            dialog.destroy()



        if final_json_valid:
            ttk.Button(btn_frame, text="仅保留无错修改", command=do_keep_success).pack(side=tk.RIGHT, padx=5)
        else:
            ttk.Button(btn_frame, text="仅保留无错修改 (当前不可用)", state=tk.DISABLED).pack(side=tk.RIGHT, padx=5)

        ttk.Button(btn_frame, text="💀 强行合并并应用", command=do_force_apply).pack(side=tk.RIGHT, padx=5)

    def _create_timestamp_backup(self):
        pass

    def _clear_response(self):
        print("[AI协作] _clear_response 被调用")


        self._typewriter_queue = []
        self._typing_active = False
        if self._typewriter_timer:
            try:
                self.after_cancel(self._typewriter_timer)
            except:
                pass
            self._typewriter_timer = None

        self.response_text.config(state=tk.NORMAL)
        self.response_text.delete("1.0", tk.END)
        self.response_text.config(state=tk.DISABLED)
        self.apply_btn.config(state=tk.DISABLED)
        self.status_var.set(tr("已清空", self.app))
        print("[AI协作] 响应已清空")

    def _skip_typewriter(self):
        print("[AI协作] _skip_typewriter 被调用")
        if not self._typing_active:
            self._clear_response()
            return
        if self._typewriter_timer:
            try:
                self.after_cancel(self._typewriter_timer)
            except:
                pass
            self._typewriter_timer = None

        # 将剩余队列内容一次性输出
        remaining = "".join(self._typewriter_queue)
        self._typewriter_queue = []
        self._typing_active = False

        self.response_text.config(state=tk.NORMAL)
        self.response_text.insert(tk.END, remaining)
        self.response_text.see(tk.END)
        self.response_text.config(state=tk.DISABLED)
        self.status_var.set(tr("已跳过打字机动画", self.app))
        print("[AI协作] 打字机动画已跳过，剩余内容已直接输出")
