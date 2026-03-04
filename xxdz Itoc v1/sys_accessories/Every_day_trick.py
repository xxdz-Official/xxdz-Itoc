# sys_accessories/Every_day_trick.py
import json
import os
import random
import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import webbrowser


class EveryDayTrick:
    def __init__(self, parent_app):
        self.parent_app = parent_app
        self.tricks_data = []
        self.current_trick_index = 0
        self.show_on_startup = True  # 默认启动时显示
        self.load_tricks_data()

    def load_tricks_data(self):
        """加载小技巧数据"""
        try:
            tricks_file = "sys_accessories/Every_day_trick.json"
            if os.path.exists(tricks_file):
                with open(tricks_file, 'r', encoding='utf-8') as f:
                    self.tricks_data = json.load(f)
                print(f"加载了 {len(self.tricks_data)} 个小技巧")
            else:
                print("未找到小技巧数据文件")
                # 创建默认数据
                self.tricks_data = [
                    {
                        "title": "欢迎使用每日小技巧",
                        "content": "这是默认的小技巧内容。请创建 sys_accessories/Every_day_trick.json 文件来添加更多小技巧。"
                    }
                ]
        except Exception as e:
            print(f"加载小技巧数据失败: {e}")
            self.tricks_data = []

    def get_random_trick_index(self):
        """随机获取一个小技巧的索引"""
        if not self.tricks_data:
            return 0

        # 使用当前时间作为随机种子，确保每次都是随机的
        random.seed(datetime.datetime.now().timestamp())

        # 随机选择一个索引
        return random.randint(0, len(self.tricks_data) - 1)

    def get_next_trick_index(self):
        """获取下一个小技巧的索引（随机）"""
        if not self.tricks_data or len(self.tricks_data) <= 1:
            return 0

        # 随机获取下一个技巧索引（确保不是当前这个）
        current = self.current_trick_index
        while True:
            random.seed(datetime.datetime.now().timestamp() + random.random())
            new_index = random.randint(0, len(self.tricks_data) - 1)
            if new_index != current:
                return new_index

    def open_bilibili(self):
        """打开B站空间"""
        try:
            webbrowser.open("https://space.bilibili.com/3461569935575626")
            print("已打开B站空间")
        except Exception as e:
            print(f"打开浏览器失败: {e}")
            messagebox.showerror("错误", f"无法打开浏览器:\n{str(e)}")

    def show_daily_trick(self, auto_startup=False):
        """
        显示每日小技巧对话框

        参数:
        auto_startup: 是否是启动时自动显示
                     True: 启动时自动显示（需要检查show_on_startup设置）
                     False: 用户手动打开（总是显示）
        """
        # 如果是启动时自动显示，但用户设置了不显示，则直接返回
        if auto_startup and not self.show_on_startup:
            print("用户设置启动时不显示小技巧，跳过显示")
            return

        # 获取随机的小技巧索引
        self.current_trick_index = self.get_random_trick_index()
        trick = self.tricks_data[self.current_trick_index] if self.tricks_data else None
        if not trick:
            return

        # 创建对话框
        dialog = tk.Toplevel(self.parent_app.root)
        dialog.title("每天一个小技巧 ✨")
        dialog.geometry("550x420")

        # 直接计算并设置窗口到屏幕中央
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        x = (screen_width - 550) // 2
        y = (screen_height - 420) // 2
        dialog.geometry(f"550x420+{x}+{y}")

        dialog.transient(self.parent_app.root)
        dialog.resizable(False, False)

        # 设置窗口样式
        dialog.configure(bg="#F5F7FA")

        # 主框架
        main_frame = ttk.Frame(dialog, padding="25")
        main_frame.pack(fill="both", expand=True)

        # 顶部区域：标题和制作者信息
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill="x", pady=(0, 15))

        # 左侧：标题文本（左对齐）- 现在放到左上角
        title_label = ttk.Label(top_frame, text="💡 每天一个小技巧",
                                font=("Microsoft YaHei", 16, "bold"),
                                foreground="#0098ff")  # 使用指定的蓝色
        title_label.pack(side="left", anchor="w")

        # 右侧：制作者信息（可点击）- 现在放到右上角
        maker_label = tk.Label(top_frame,
                               text="小小电子xxdz 制作",
                               font=("Microsoft YaHei", 9, "italic"),
                               fg="#666666",
                               cursor="hand2")
        maker_label.pack(side="right", anchor="e")
        maker_label.bind("<Button-1>", lambda e: self.open_bilibili())
        maker_label.bind("<Enter>", lambda e: maker_label.config(fg="#0098ff"))
        maker_label.bind("<Leave>", lambda e: maker_label.config(fg="#666666"))

        # 技巧标题区域（左对齐）
        trick_title_frame = ttk.Frame(main_frame)
        trick_title_frame.pack(fill="x", pady=(0, 10))

        # 技巧标题（左对齐）
        trick_title = ttk.Label(trick_title_frame, text=trick["title"],
                                font=("Microsoft YaHei", 13, "bold"),
                                foreground="#2C3E50",  # 使用深灰色，与标题蓝色区分
                                wraplength=480,
                                justify="left")
        trick_title.pack(side="left", anchor="w")

        # 内容框架（带滚动条）- 左对齐，高度减小
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill="both", expand=True, pady=(0, 15))

        # 内容容器（用于左对齐）
        content_container = tk.Frame(content_frame, bg="#FFFFFF", relief="solid", bd=1)
        content_container.pack(fill="both", expand=True, side="left", anchor="w")

        # 添加滚动条
        scrollbar = ttk.Scrollbar(content_container)
        scrollbar.pack(side="right", fill="y")

        # 内容文本（左对齐）- 减小高度，确保显示完整
        content_text = tk.Text(content_container, wrap="word", height=8,  # 从10改为8，减少高度
                               font=("Microsoft YaHei", 11),
                               yscrollcommand=scrollbar.set,
                               bg="#FFFFFF",
                               fg="#34495E",
                               relief="flat",
                               padx=15,
                               pady=15,
                               spacing2=5)  # 段落间距
        content_text.pack(side="left", fill="both", expand=True, anchor="w")
        scrollbar.config(command=content_text.yview)

        # 插入内容（左对齐）
        content_text.insert("1.0", trick["content"])
        content_text.tag_configure("left", justify="left")
        content_text.tag_add("left", "1.0", "end")
        content_text.config(state="disabled")

        # 底部控制框架
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill="x", pady=(5, 0))

        # 左侧：启动时显示复选框（左对齐）
        left_frame = ttk.Frame(bottom_frame)
        left_frame.pack(side="left", anchor="w", fill="x", expand=True)

        self.show_var = tk.BooleanVar(value=self.show_on_startup)
        show_check = ttk.Checkbutton(left_frame, text="下次启动时显示小技巧",
                                     variable=self.show_var,
                                     command=self.toggle_show_on_startup,
                                     style="TrickCheckbutton.TCheckbutton")
        show_check.pack(side="left", anchor="w")

        # 右侧：按钮框架（右对齐）
        button_frame = ttk.Frame(bottom_frame)
        button_frame.pack(side="right", anchor="e")

        # 样式配置
        style = ttk.Style()
        style.configure("Trick.TButton", font=("Microsoft YaHei", 10))
        style.configure("TrickCheckbutton.TCheckbutton", font=("Microsoft YaHei", 10))

        # 下一个技巧按钮
        next_btn = ttk.Button(button_frame, text="下一个技巧 ↻",
                              command=lambda: self.show_next_trick(dialog, content_text, trick_title,
                                                                   content_container),
                              style="Trick.TButton",
                              width=12)
        next_btn.pack(side="left", padx=(0, 10))

        # 关闭按钮
        close_btn = ttk.Button(button_frame, text="关闭 ✕",
                               command=dialog.destroy,
                               style="Trick.TButton",
                               width=8)
        close_btn.pack(side="left")

        # 绑定快捷键
        dialog.bind("<Return>", lambda e: dialog.destroy())
        dialog.bind("<Escape>", lambda e: dialog.destroy())
        dialog.bind("<Right>", lambda e: self.show_next_trick(dialog, content_text, trick_title, content_container))

        # 设置焦点
        dialog.focus_set()

        # 让窗口显示在最前面
        dialog.lift()
        dialog.attributes('-topmost', True)
        dialog.after(100, lambda: dialog.attributes('-topmost', False))

    def show_next_trick(self, dialog, content_text, title_label, content_container):
        """显示下一个小技巧（随机）"""
        if not self.tricks_data or len(self.tricks_data) <= 1:
            return

        # 获取下一个随机技巧索引
        self.current_trick_index = self.get_next_trick_index()
        trick = self.tricks_data[self.current_trick_index]

        # 更新显示
        title_label.config(text=trick["title"])

        # 更新文本内容
        content_text.config(state="normal")
        content_text.delete("1.0", "end")
        content_text.insert("1.0", trick["content"])
        content_text.tag_configure("left", justify="left")
        content_text.tag_add("left", "1.0", "end")
        content_text.config(state="disabled")

        # 闪烁一下内容框，提示已更新
        original_bg = content_container.cget("bg")
        for color in ["#E3F2FD", "#FFF9C4", original_bg]:
            content_container.configure(bg=color)
            dialog.update()
            dialog.after(50)

    def toggle_show_on_startup(self):
        """切换启动时显示设置"""
        self.show_on_startup = self.show_var.get()
        print(f"下次启动时显示小技巧: {'是' if self.show_on_startup else '否'}")

    def save_settings(self):
        """保存设置（由父应用调用）"""
        return {
            "show_on_startup": self.show_on_startup
        }

    def load_settings(self, settings):
        """加载设置（由父应用调用）"""
        if "show_on_startup" in settings:
            self.show_on_startup = settings["show_on_startup"]