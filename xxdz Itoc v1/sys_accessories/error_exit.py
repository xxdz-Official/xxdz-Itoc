# sys_accessories/error_exit.py
import os
import json
import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import webbrowser
from PIL import Image, ImageTk  # 需要安装Pillow库


class ErrorExitDetector:
    def __init__(self, data_file="sys_accessories/Every_day_trick.data"):
        self.data_file = data_file
        self.app_running = True
        self.last_status = None
        # 新增：自动保存路径
        self.autosave_path = None  # 将在初始化时设置
        self.main_app = None  # 主程序引用
        self.data_file = data_file
        self.app_running = True
        self.last_status = None
        # 新增：自动保存路径
        self.autosave_path = None  # 将在初始化时设置
        self.main_app = None  # 主程序引用

    def load_last_status(self):
        """加载上次的运行状态"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.last_status = data
                print(f"加载上次状态: {data.get('status', 'unknown')}")
                return data
            else:
                print("未找到状态文件，可能是首次运行")
                return None
        except Exception as e:
            print(f"加载状态文件失败: {e}")
            return None

    def record_startup(self):
        """记录程序启动"""
        try:
            startup_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            status_data = {
                "status": "program_started",
                "startup_time": startup_time,
                "timestamp": datetime.datetime.now().timestamp()
            }

            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(status_data, f, ensure_ascii=False, indent=2)

            print(f"记录程序启动时间: {startup_time}")
            return True
        except Exception as e:
            print(f"记录程序启动失败: {e}")
            return False

    def record_normal_exit(self):
        """记录程序正常退出"""
        try:
            if not self.app_running:
                return False

            exit_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            status_data = {
                "status": "normal_exit",
                "exit_time": exit_time,
                "timestamp": datetime.datetime.now().timestamp()
            }

            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(status_data, f, ensure_ascii=False, indent=2)

            print(f"记录程序正常退出: {exit_time}")
            return True
        except Exception as e:
            print(f"记录程序退出失败: {e}")
            return False

    def check_abnormal_exit(self):
        """检查是否有异常退出"""
        last_status = self.load_last_status()

        if not last_status:
            # 首次运行，没有异常退出
            return False, None

        last_status_type = last_status.get("status", "")
        last_time = last_status.get("startup_time", last_status.get("exit_time", ""))

        # 如果上次状态是程序启动，但这次启动时还不是正常退出，说明异常退出
        if last_status_type == "program_started":
            return True, last_time

        return False, last_time

    def show_abnormal_exit_warning(self, last_time):
        """显示异常退出警告窗口"""

        def open_bilibili():
            """打开B站空间"""
            try:
                webbrowser.open("https://space.bilibili.com/3461569935575626")
                print("已打开B站空间")
            except Exception as e:
                print(f"打开浏览器失败: {e}")
                messagebox.showerror("错误", f"无法打开浏览器:\n{str(e)}")

        # 创建警告窗口
        warning_dialog = tk.Toplevel()
        warning_dialog.title(" 检测到上回异常退出辣")
        warning_dialog.geometry("600x380")  # 稍微增加宽度容纳新按钮

        # 直接计算并设置窗口到屏幕中央
        screen_width = warning_dialog.winfo_screenwidth()
        screen_height = warning_dialog.winfo_screenheight()
        x = (screen_width - 600) // 2
        y = (screen_height - 380) // 2
        warning_dialog.geometry(f"600x380+{x}+{y}")

        warning_dialog.resizable(False, False)

        # 设置整个窗口背景为淡黄色
        warning_dialog.configure(bg="#FFF3CD")

        # 强制窗口置顶
        warning_dialog.attributes('-topmost', True)

        # 尝试加载自定义图标作为窗口图标
        icon_path = "sys_accessories/msdt_110.ico"
        if os.path.exists(icon_path):
            try:
                warning_dialog.iconbitmap(icon_path)
                print("已加载自定义警告图标")
            except Exception as e:
                print(f"加载自定义窗口图标失败: {e}")

        # 主框架 - 设置背景色为淡黄色
        main_frame = tk.Frame(warning_dialog, bg="#FFF3CD", padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)

        # 警告图标和标题
        title_frame = tk.Frame(main_frame, bg="#FFF3CD")
        title_frame.pack(fill="x", pady=(0, 15))

        # 尝试加载自定义图标作为标签图标
        icon_label = None
        if os.path.exists(icon_path):
            try:
                # 方法1: 直接使用tkinter的PhotoImage（仅支持PNG、GIF等格式）
                if icon_path.lower().endswith('.ico'):
                    # 对于ICO文件，使用Pillow转换
                    try:
                        from PIL import Image, ImageTk
                        # 加载ICO文件
                        img = Image.open(icon_path)
                        # 调整大小为32x32
                        img = img.resize((32, 32), Image.Resampling.LANCZOS)
                        icon_img = ImageTk.PhotoImage(img)

                        icon_label = tk.Label(title_frame, image=icon_img, bg="#FFF3CD")
                        icon_label.image = icon_img  # 保持引用
                        icon_label.pack(side="left", padx=(0, 15))

                    except ImportError:
                        print("Pillow库未安装，无法加载ICO文件")
                        # 如果Pillow不可用，使用默认方法尝试
                        icon_img = tk.PhotoImage(file=icon_path)
                        icon_label = tk.Label(title_frame, image=icon_img, bg="#FFF3CD")
                        icon_label.image = icon_img
                        icon_label.pack(side="left", padx=(0, 15))
                else:
                    # 对于其他格式，直接使用PhotoImage
                    icon_img = tk.PhotoImage(file=icon_path)
                    icon_label = tk.Label(title_frame, image=icon_img, bg="#FFF3CD")
                    icon_label.image = icon_img
                    icon_label.pack(side="left", padx=(0, 15))

            except Exception as e:

                # 如果加载失败，使用文本图标
                icon_label = tk.Label(title_frame, text="⚠️",
                                      font=("Arial", 28),
                                      bg="#FFF3CD")
                icon_label.pack(side="left", padx=(0, 15))
        else:

            # 使用文本图标
            icon_label = tk.Label(title_frame, text="⚠️",
                                  font=("Arial", 28),
                                  bg="#FFF3CD")
            icon_label.pack(side="left", padx=(0, 15))

        title_label = tk.Label(title_frame, text="检测到异常退出 XwX",
                               font=("Microsoft YaHei", 16, "bold"),
                               foreground="#856404",
                               background="#FFF3CD")
        title_label.pack(side="left", anchor="w")

        # 上次打开时间信息
        time_frame = tk.Frame(main_frame, bg="#FFF3CD")
        time_frame.pack(fill="x", pady=(0, 10))

        time_label = tk.Label(time_frame,
                              text=f"上次软件打开时间: {last_time}",
                              font=("Microsoft YaHei", 11),
                              foreground="#856404",
                              background="#FFF3CD")
        time_label.pack(side="left", anchor="w")

        # 信息文本框架（带滚动条）
        info_frame = tk.Frame(main_frame, bg="#FFF3CD")
        info_frame.pack(fill="both", expand=True, pady=(0, 20))

        # 内容容器（白色背景，与黄色窗口形成对比）
        content_container = tk.Frame(info_frame, bg="#FFFFFF", relief="solid", bd=1)
        content_container.pack(fill="both", expand=True)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(content_container)
        scrollbar.pack(side="right", fill="y")

        # 信息文本（使用Text控件以便滚动）
        info_text = tk.Text(content_container, wrap="word", height=6,
                            font=("Microsoft YaHei", 11),
                            bg="#FFFFFF",
                            fg="#856404",
                            relief="flat",
                            borderwidth=0,
                            yscrollcommand=scrollbar.set,
                            padx=15,
                            pady=15)
        info_text.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=info_text.yview)

        # 插入信息内容
        info_content = """软件被异常退出！ QwQ

如果有异常请检查控制台日志。
或者联系作者 B站_小小电子xxdz，
会很快回复你噢 (点击下方按钮跳转)

开了自动保存？可以去恢复一下噢
"""

        info_text.insert("1.0", info_content)
        info_text.tag_configure("left", justify="left")
        info_text.tag_add("left", "1.0", "end")
        info_text.config(state="disabled")

        # 加载表情包图片（位于详细信息文本框的"上边缘"右侧）
        warning_img_path = "img/Warning.png"
        if os.path.exists(warning_img_path):
            try:
                # 打开图片
                original_img = Image.open(warning_img_path)

                # 原始分辨率：484x399
                # 目标高度：155px，等比缩放
                original_width, original_height = original_img.size
                target_height = 155
                # 计算缩放比例
                scale_factor = target_height / original_height
                target_width = int(original_width * scale_factor)

                # 等比缩放图片
                resized_img = original_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
                warning_img = ImageTk.PhotoImage(resized_img)

                # 创建图片标签
                # 锚点为图片底部居中位置，放置在文本框的右上角
                img_label = tk.Label(content_container,
                                     image=warning_img,
                                     bg="#FFFFFF",
                                     borderwidth=0)
                img_label.image = warning_img  # 保持引用

                # 使用place布局精确定位
                # 距离文本框上边缘0px，向右移动15px，向下移动9px
                img_label.place(relx=1.0, rely=0.0, anchor="ne", x=-15, y=9)

                print(f"已加载表情包图片: {warning_img_path} (缩放至{target_width}x{target_height})")

            except Exception as e:
                print(f"加载表情包图片失败: {e}")
                # 如果加载失败，可以添加一个占位符标签
                placeholder_label = tk.Label(content_container,
                                             text="(๑•̀ㅂ•́)و✧",
                                             font=("Microsoft YaHei", 14),
                                             bg="#FFFFFF",
                                             fg="#856404")
                placeholder_label.place(relx=1.0, rely=0.0, anchor="ne", x=-10, y=5)
        else:
            print(f"表情包图片未找到: {warning_img_path}")
            # 如果图片不存在，添加文本替代
            placeholder_label = tk.Label(content_container,
                                         text="(๑•̀ㅂ•́)و✧",
                                         font=("Microsoft YaHei", 14),
                                         bg="#FFFFFF",
                                         fg="#856404")
            placeholder_label.place(relx=1.0, rely=0.0, anchor="ne", x=-10, y=5)

        # 底部按钮框架
        bottom_frame = tk.Frame(main_frame, bg="#FFF3CD")
        bottom_frame.pack(fill="x", pady=(10, 0))

        # 左侧按钮组
        left_btn_frame = tk.Frame(bottom_frame, bg="#FFF3CD")
        left_btn_frame.pack(side="left")

        # 作者链接按钮
        author_btn = ttk.Button(left_btn_frame, text="联系作者 (B站_小小电子xxdz)",
                                command=open_bilibili)
        author_btn.pack(side="left", padx=(0, 10))

        # ========== 新增：自动保存相关按钮 ==========
        # 加载最近的自动保存按钮
        load_autosave_btn = ttk.Button(
            left_btn_frame,
            text="加载最近的自动保存",
            command=lambda: self.load_recent_autosave(warning_dialog)
        )
        load_autosave_btn.pack(side="left", padx=(0, 10))

        # 打开自动保存文件夹按钮
        open_folder_btn = ttk.Button(
            left_btn_frame,
            text="打开自动保存文件夹",
            command=lambda: self.open_autosave_folder()
        )
        open_folder_btn.pack(side="left", padx=(0, 10))
        # ============================================

        # 右侧：关闭按钮
        close_btn = ttk.Button(bottom_frame, text="关闭",
                               command=warning_dialog.destroy)
        close_btn.pack(side="right")

        # 绑定快捷键
        warning_dialog.bind("<Return>", lambda e: warning_dialog.destroy())
        warning_dialog.bind("<Escape>", lambda e: warning_dialog.destroy())

        # 设置焦点到关闭按钮
        close_btn.focus_set()

        # 确保窗口保持置顶
        def keep_on_top():
            warning_dialog.lift()
            warning_dialog.attributes('-topmost', True)
            warning_dialog.focus_force()

        # 窗口显示后立即置顶
        warning_dialog.after(10, keep_on_top)

        # 等待窗口显示
        warning_dialog.wait_visibility()
        keep_on_top()

        return warning_dialog

    def set_autosave_path(self, path):
        """设置自动保存路径（由主程序调用）"""
        self.autosave_path = path
        print(f"[异常检测] 自动保存路径已设置: {path}")

    def set_main_app(self, app):
        """设置主程序引用（由主程序调用）"""
        self.main_app = app
        print("[异常检测] 主程序引用已设置")

    def load_recent_autosave(self, dialog):
        """加载最近的自动保存文件"""
        try:
            if not self.autosave_path or not os.path.exists(self.autosave_path):
                messagebox.showwarning(
                    "无法加载",
                    "自动保存文件夹不存在或未设置。\n\n请先保存工程并启用自动保存功能。",
                    parent=dialog
                )
                return

            # 获取工程名称
            project_name = None
            if hasattr(self, 'main_app') and self.main_app and hasattr(self.main_app, 'current_project_path'):
                if self.main_app.current_project_path:
                    project_name = os.path.splitext(
                        os.path.basename(self.main_app.current_project_path)
                    )[0]

            # 查找所有自动保存文件
            autosave_files = []
            for filename in os.listdir(self.autosave_path):
                if filename.endswith('.czemidi') and '_autosave_' in filename:
                    if not project_name or filename.startswith(project_name):
                        filepath = os.path.join(self.autosave_path, filename)
                        autosave_files.append((filepath, os.path.getmtime(filepath)))

            if not autosave_files:
                messagebox.showinfo(
                    "没有自动保存文件",
                    f"在 {self.autosave_path} 中没有找到自动保存文件。",
                    parent=dialog
                )
                return

            # 按修改时间排序（最新的在前）
            autosave_files.sort(key=lambda x: x[1], reverse=True)
            latest_file = autosave_files[0][0]
            latest_time = datetime.datetime.fromtimestamp(autosave_files[0][1]).strftime("%Y-%m-%d %H:%M:%S")

            # 询问用户是否加载
            response = messagebox.askyesno(
                "加载自动保存",
                f"找到最近的自动保存文件：\n\n"
                f"文件: {os.path.basename(latest_file)}\n"
                f"时间: {latest_time}\n\n"
                f"是否加载？\n\n"
                f"(当前工程未保存的修改可能会丢失)",
                parent=dialog
            )

            if response:
                # 关闭警告对话框
                dialog.destroy()

                # 在主程序中加载文件
                if hasattr(self, 'main_app') and self.main_app:
                    self.main_app.open_cze_project_from_path(latest_file)
                    messagebox.showinfo(
                        "加载成功",
                        f"已加载自动保存文件：\n{os.path.basename(latest_file)}"
                    )
                else:
                    messagebox.showerror(
                        "加载失败",
                        "无法访问主程序，请手动打开工程文件。\n\n"
                        f"文件路径：{latest_file}"
                    )

        except Exception as e:
            messagebox.showerror("加载失败", f"加载自动保存文件时出错：\n\n{str(e)}", parent=dialog)

    def open_autosave_folder(self):
        """打开自动保存文件夹"""
        try:
            if not self.autosave_path or not os.path.exists(self.autosave_path):
                # 尝试使用默认路径
                default_path = os.path.join(os.getcwd(), "TempSave")
                if os.path.exists(default_path):
                    self.autosave_path = default_path
                else:
                    messagebox.showwarning(
                        "文件夹不存在",
                        f"自动保存文件夹不存在：\n{self.autosave_path or '未设置'}\n\n"
                        f"请先保存工程并启用自动保存功能。"
                    )
                    return

            # 在资源管理器中打开文件夹
            if os.name == 'nt':  # Windows
                import subprocess
                subprocess.run(['explorer', os.path.normpath(self.autosave_path)])
            elif os.name == 'posix':  # Linux/Mac
                import subprocess
                if sys.platform == 'darwin':  # Mac
                    subprocess.run(['open', '-R', self.autosave_path])
                else:  # Linux
                    subprocess.run(['xdg-open', self.autosave_path])

            print(f"已打开自动保存文件夹：{self.autosave_path}")

        except Exception as e:
            messagebox.showerror("打开失败", f"无法打开自动保存文件夹：\n\n{str(e)}")

    def set_app_stopped(self):
        """设置程序已停止（用于异常情况）"""
        self.app_running = False