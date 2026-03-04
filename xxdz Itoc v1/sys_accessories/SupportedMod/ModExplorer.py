# sys_accessories/SupportedMod/ModExplorer.py
"""
插件管理器（ModExplorer） - 简化修复版
用于管理所有插件的启用/禁用、卸载等基本操作
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import os
import sys
import shutil
import json
from datetime import datetime

# 导入配置管理器
try:
    from ModConfig import ModConfigManager, ModStatus
except ImportError:
    # 如果在主程序中，路径可能不同
    sys.path.append("sys_accessories/SupportedMod")
    from ModConfig import ModConfigManager, ModStatus


class ModExplorer:
    """插件管理器类 - 简化修复版"""

    def __init__(self, app_reference, supported_mod):
        """
        初始化插件管理器

        Args:
            app_reference: 主程序引用
            supported_mod: SupportedMOD实例
        """
        self.app = app_reference
        self.supported_mod = supported_mod
        self.config_manager = ModConfigManager()

        # 插件目录路径
        self.mods_dir = "mod"
        self.backup_dir = "mod_backup"  # 保留但不使用

        # 确保备份目录存在（可选）
        os.makedirs(self.backup_dir, exist_ok=True)

        print("插件管理器初始化完成")

    def create_manager_window(self):
        """创建插件管理器窗口"""
        if hasattr(self, 'manager_window') and self.manager_window.winfo_exists():
            self.manager_window.lift()
            return

        # 创建管理器窗口（横向窗口）
        self.manager_window = tk.Toplevel(self.app.root)
        self.manager_window.title("插件管理器")
        self.manager_window.geometry("1000x700")  # 更宽的窗口
        self.manager_window.transient(self.app.root)
        self.manager_window.protocol("WM_DELETE_WINDOW", self.on_manager_close)

        # 设置图标
        try:
            self.manager_window.iconbitmap("sys_accessories/msdt_110.ico")
        except:
            pass

        # 使窗口可调整大小
        self.manager_window.resizable(True, True)

        # 创建主框架
        main_frame = ttk.Frame(self.manager_window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 创建标题
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill="x", pady=(0, 10))

        title_label = ttk.Label(title_frame, text="📦 Itoc 插件管理器",
                                font=("微软雅黑", 16, "bold"))
        title_label.pack(side="left")

        # 自动扫描插件
        self.status_label = ttk.Label(title_frame, text="正在扫描插件...",
                                      font=("微软雅黑", 10))
        self.status_label.pack(side="left", padx=10)

        # 创建工具栏
        toolbar_frame = ttk.Frame(main_frame)
        toolbar_frame.pack(fill="x", pady=(0, 10))

        # 工具栏按钮
        ttk.Button(toolbar_frame, text="🔄 重新扫描",
                   command=self.scan_for_new_mods).pack(side="left", padx=2)

        ttk.Button(toolbar_frame, text="📊 系统信息",
                   command=self.show_system_info).pack(side="left", padx=2)

        ttk.Button(toolbar_frame, text="❓ 帮助",
                   command=self.show_help).pack(side="left", padx=2)

        # 创建搜索框
        search_frame = ttk.Frame(toolbar_frame)
        search_frame.pack(side="right")

        ttk.Label(search_frame, text="搜索:").pack(side="left", padx=(10, 5))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=25)
        self.search_entry.pack(side="left")
        self.search_entry.bind("<KeyRelease>", self.on_search_changed)

        # 使用PanedWindow创建可调整的分割区域
        self.main_paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill="both", expand=True)

        # 左侧：插件列表（40%宽度）
        left_container = ttk.Frame(self.main_paned)
        self.main_paned.add(left_container, weight=40)

        # 插件列表标题
        list_title_frame = ttk.Frame(left_container)
        list_title_frame.pack(fill="x", pady=(0, 5))

        ttk.Label(list_title_frame, text="插件列表",
                  font=("微软雅黑", 12, "bold")).pack(side="left")

        # 创建插件列表树形视图容器
        list_container = ttk.Frame(left_container)
        list_container.pack(fill="both", expand=True)

        # 创建插件列表树形视图
        columns = ("name", "status", "version", "author")
        self.mod_tree = ttk.Treeview(list_container, columns=columns, show="headings", height=20)

        # 设置列标题
        self.mod_tree.heading("name", text="插件名称")
        self.mod_tree.heading("status", text="状态")
        self.mod_tree.heading("version", text="版本")
        self.mod_tree.heading("author", text="作者")

        # 设置列宽度（更宽的列）
        self.mod_tree.column("name", width=180, minwidth=100)
        self.mod_tree.column("status", width=90, minwidth=80)
        self.mod_tree.column("version", width=90, minwidth=80)
        self.mod_tree.column("author", width=120, minwidth=100)

        # 添加水平和垂直滚动条
        tree_vscroll = ttk.Scrollbar(list_container, orient="vertical", command=self.mod_tree.yview)
        tree_hscroll = ttk.Scrollbar(list_container, orient="horizontal", command=self.mod_tree.xview)
        self.mod_tree.configure(yscrollcommand=tree_vscroll.set, xscrollcommand=tree_hscroll.set)

        # 使用grid布局，让滚动条正确显示
        self.mod_tree.grid(row=0, column=0, sticky="nsew")
        tree_vscroll.grid(row=0, column=1, sticky="ns")
        tree_hscroll.grid(row=1, column=0, sticky="ew")

        # 配置grid权重
        list_container.grid_rowconfigure(0, weight=1)
        list_container.grid_columnconfigure(0, weight=1)

        # 绑定选择事件
        self.mod_tree.bind("<<TreeviewSelect>>", self.on_mod_selected)

        # 右侧：详细信息面板（60%宽度）
        right_container = ttk.Frame(self.main_paned)
        self.main_paned.add(right_container, weight=60)

        # 详细信息标题
        detail_title_frame = ttk.Frame(right_container)
        detail_title_frame.pack(fill="x", pady=(0, 5))

        ttk.Label(detail_title_frame, text="插件详情",
                  font=("微软雅黑", 12, "bold")).pack(side="left")

        # 创建详细信息容器（使用Frame而不是Canvas，避免横向滚动条）
        detail_content = ttk.Frame(right_container)
        detail_content.pack(fill="both", expand=True, padx=5)

        # 创建主内容框架，用于放置垂直滚动条
        detail_main_frame = ttk.Frame(detail_content)
        detail_main_frame.pack(fill="both", expand=True)

        # 创建Canvas和Scrollbar（仅垂直方向）
        detail_canvas = tk.Canvas(detail_main_frame)
        detail_scrollbar = ttk.Scrollbar(detail_main_frame, orient="vertical", command=detail_canvas.yview)

        # 创建内部框架用于容纳所有详情内容
        self.detail_inner_frame = ttk.Frame(detail_canvas)

        # 配置Canvas滚动区域
        self.detail_inner_frame.bind(
            "<Configure>",
            lambda e: detail_canvas.configure(scrollregion=detail_canvas.bbox("all"))
        )

        # 将内部框架添加到Canvas
        detail_canvas.create_window((0, 0), window=self.detail_inner_frame, anchor="nw",
                                    width=detail_canvas.winfo_reqwidth())
        detail_canvas.configure(yscrollcommand=detail_scrollbar.set)

        # 配置Canvas调整大小时更新内部框架宽度
        def configure_canvas(event):
            detail_canvas.itemconfig("all", width=event.width)

        detail_canvas.bind("<Configure>", configure_canvas)

        # 布局Canvas和滚动条
        detail_canvas.pack(side="left", fill="both", expand=True)
        detail_scrollbar.pack(side="right", fill="y")

        # 插件名称
        name_frame = ttk.Frame(self.detail_inner_frame)
        name_frame.pack(fill="x", pady=(5, 10))

        ttk.Label(name_frame, text="插件名称:",
                  font=("微软雅黑", 11, "bold")).pack(side="left")
        self.detail_name_label = ttk.Label(name_frame, text="", font=("微软雅黑", 11))
        self.detail_name_label.pack(side="left", padx=5)

        # 版本和作者在同一行显示
        info_frame = ttk.Frame(self.detail_inner_frame)
        info_frame.pack(fill="x", pady=(0, 15))

        version_frame = ttk.Frame(info_frame)
        version_frame.pack(side="left", padx=(0, 20), fill="x", expand=True)
        ttk.Label(version_frame, text="版本:", font=("微软雅黑", 10, "bold")).pack(anchor="w")
        self.detail_version_label = ttk.Label(version_frame, text="", wraplength=200)
        self.detail_version_label.pack(anchor="w", fill="x")

        author_frame = ttk.Frame(info_frame)
        author_frame.pack(side="left", fill="x", expand=True)
        ttk.Label(author_frame, text="作者:", font=("微软雅黑", 10, "bold")).pack(anchor="w")
        self.detail_author_label = ttk.Label(author_frame, text="", wraplength=200)
        self.detail_author_label.pack(anchor="w", fill="x")

        # 作者网站
        website_frame = ttk.Frame(self.detail_inner_frame)
        website_frame.pack(fill="x", pady=(0, 15))

        ttk.Label(website_frame, text="作者网站:",
                  font=("微软雅黑", 10, "bold")).pack(side="left")
        self.detail_website_label = ttk.Label(website_frame, text="", font=("微软雅黑", 9),
                                              foreground="blue", cursor="hand2", wraplength=400)
        self.detail_website_label.pack(side="left", padx=5, fill="x", expand=True)
        self.detail_website_label.bind("<Button-1>", self.open_website)

        # 描述
        ttk.Label(self.detail_inner_frame, text="插件描述:",
                  font=("微软雅黑", 10, "bold")).pack(anchor="w", pady=(0, 5))

        self.detail_desc_text = scrolledtext.ScrolledText(self.detail_inner_frame, height=6,  # 从4改为6
                                                          font=("微软雅黑", 9), wrap=tk.WORD)
        self.detail_desc_text.pack(fill="x", pady=(0, 15))
        self.detail_desc_text.config(state=tk.DISABLED)


        # 插件路径
        path_frame = ttk.Frame(self.detail_inner_frame)
        path_frame.pack(fill="x", pady=(0, 15))

        ttk.Label(path_frame, text="插件路径:",
                  font=("微软雅黑", 10, "bold")).pack(side="left")
        self.detail_path_label = ttk.Label(path_frame, text="", font=("微软雅黑", 9),
                                           foreground="blue", cursor="hand2", wraplength=400)
        self.detail_path_label.pack(side="left", padx=5, fill="x", expand=True)
        self.detail_path_label.bind("<Button-1>", self.open_mod_directory)

        # 启用/禁用设置
        enabled_frame = ttk.Frame(self.detail_inner_frame)
        enabled_frame.pack(fill="x", pady=(0, 15))

        self.enabled_var = tk.BooleanVar()
        self.enabled_check = ttk.Checkbutton(enabled_frame, text="启用此插件",
                                             variable=self.enabled_var,
                                             command=self.save_enabled_setting)
        self.enabled_check.pack(anchor="w")

        # 分隔线
        ttk.Separator(self.detail_inner_frame, orient='horizontal').pack(fill='x', pady=5)

        # 文件列表标题
        files_title_frame = ttk.Frame(self.detail_inner_frame)
        files_title_frame.pack(fill="x", pady=(0, 5))

        ttk.Label(files_title_frame, text="插件文件:",
                  font=("微软雅黑", 10, "bold")).pack(side="left")

        # 刷新文件列表按钮
        ttk.Button(files_title_frame, text="刷新文件列表",
                   command=self.refresh_files_list).pack(side="right")

        # 文件列表容器
        files_container = ttk.Frame(self.detail_inner_frame)
        files_container.pack(fill="both", expand=True)

        # 创建文件列表树形视图 - 修复版
        self.files_tree = ttk.Treeview(files_container, columns=("filename", "size", "modified"),
                                       show="headings", height=8)

        # 设置列标题
        self.files_tree.heading("filename", text="文件名")
        self.files_tree.heading("size", text="大小")
        self.files_tree.heading("modified", text="修改时间")

        # 设置列宽度（更宽的列）
        self.files_tree.column("filename", width=250, minwidth=150)
        self.files_tree.column("size", width=80, minwidth=60)
        self.files_tree.column("modified", width=120, minwidth=100)

        # 添加垂直滚动条
        files_vscroll = ttk.Scrollbar(files_container, orient="vertical", command=self.files_tree.yview)
        self.files_tree.configure(yscrollcommand=files_vscroll.set)

        # 使用grid布局
        self.files_tree.grid(row=0, column=0, sticky="nsew")
        files_vscroll.grid(row=0, column=1, sticky="ns")

        # 配置grid权重
        files_container.grid_rowconfigure(0, weight=1)
        files_container.grid_columnconfigure(0, weight=1)

        # 文件操作按钮
        file_buttons_frame = ttk.Frame(self.detail_inner_frame)
        file_buttons_frame.pack(fill="x", pady=(5, 0))

        ttk.Button(file_buttons_frame, text="📄 查看文件",
                   command=self.view_selected_file).pack(side="left", padx=2)

        ttk.Button(file_buttons_frame, text="📋 复制路径",
                   command=self.copy_file_path).pack(side="left", padx=2)

        # 查看Attribute.txt按钮
        ttk.Button(file_buttons_frame, text="📝 查看属性文件",
                   command=self.view_attribute_file).pack(side="left", padx=2)

        # 底部操作按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))

        # 操作按钮
        ttk.Button(button_frame, text="✅ 启用插件",
                   command=self.enable_selected_mod).pack(side="left", padx=2)

        ttk.Button(button_frame, text="⛔ 禁用插件",
                   command=self.disable_selected_mod).pack(side="left", padx=2)

        ttk.Button(button_frame, text="📁 打开插件目录",
                   command=self.open_mods_directory).pack(side="left", padx=2)
        ttk.Button(button_frame, text="🗑️ 卸载插件",
                   command=self.uninstall_selected_mod).pack(side="left", padx=2)

        ttk.Button(button_frame, text="❌ 关闭",
                   command=self.on_manager_close).pack(side="right", padx=2)

        # 焦点设置
        self.manager_window.focus_set()

        # 延迟加载插件列表（确保窗口完全创建后）
        self.manager_window.after(100, self.load_mods_list)

    def load_mods_list(self):
        """加载插件列表"""
        # 确保supported_mod有插件数据
        if self.supported_mod and not self.supported_mod.mods:
            # 重新扫描插件
            self.supported_mod.mods = self.supported_mod.scan_mods()

        self.refresh_mods_list()

    def refresh_mods_list(self):
        """刷新插件列表"""
        # 清空列表
        for item in self.mod_tree.get_children():
            self.mod_tree.delete(item)

        if not self.supported_mod or not self.supported_mod.mods:
            self.status_label.config(text="没有找到插件")
            return

        # 获取搜索关键词
        search_text = self.search_var.get().lower()

        # 按名称排序
        sorted_mods = sorted(self.supported_mod.mods,
                             key=lambda x: x.mod_display_name.lower())

        added_count = 0
        for mod_info in sorted_mods:
            # 检查是否匹配搜索条件
            display_name = mod_info.mod_display_name.lower()
            description = mod_info.mod_description.lower()
            author = mod_info.mod_author.lower()

            if search_text and (search_text not in display_name and
                                search_text not in description and
                                search_text not in author):
                continue

            # 确定状态文本
            status_text = "已启用" if self.config_manager.is_mod_enabled(mod_info.mod_name) else "已禁用"

            # 添加状态标记
            if mod_info.mod_state.name == "ERROR":
                status_text += " (错误)"

            # 添加插件到列表
            self.mod_tree.insert("", "end",
                                 values=(mod_info.mod_display_name,
                                         status_text,
                                         mod_info.mod_version,
                                         mod_info.mod_author),
                                 tags=(mod_info.mod_name,))

            # 设置行颜色
            if mod_info.mod_state.name == "ERROR":
                self.mod_tree.tag_configure(mod_info.mod_name, foreground="red")
            elif not self.config_manager.is_mod_enabled(mod_info.mod_name):
                self.mod_tree.tag_configure(mod_info.mod_name, foreground="gray")

            added_count += 1

        self.status_label.config(text=f"共 {added_count} 个插件")

        # 如果有插件，自动选择第一个
        if added_count > 0:
            first_item = self.mod_tree.get_children()[0]
            self.mod_tree.selection_set(first_item)
            self.mod_tree.focus(first_item)
            self.on_mod_selected(None)

    def on_mod_selected(self, event):
        """插件选择事件"""
        selection = self.mod_tree.selection()
        if not selection:
            return

        item = selection[0]
        mod_name = self.mod_tree.item(item, "tags")[0]

        # 找到对应的插件信息
        mod_info = None
        for m in self.supported_mod.mods:
            if m.mod_name == mod_name:
                mod_info = m
                break

        if mod_info:
            self.update_mod_details(mod_info)

    def update_mod_details(self, mod_info):
        """更新插件详细信息"""
        # 更新基本信息
        self.detail_name_label.config(text=mod_info.mod_display_name)
        self.detail_version_label.config(text=mod_info.mod_version)
        self.detail_author_label.config(text=mod_info.mod_author)

        # 更新作者网站
        website_text = mod_info.mod_website if hasattr(mod_info, 'mod_website') else "未提供"
        self.detail_website_label.config(text=website_text)

        # 如果网站URL有效，设置为可点击的链接样式
        if website_text and website_text != "未提供" and (
                website_text.startswith("http://") or
                website_text.startswith("https://") or
                website_text.startswith("www.")
        ):
            self.detail_website_label.config(foreground="blue", cursor="hand2")
            self.current_website = website_text
        else:
            self.detail_website_label.config(foreground="black", cursor="")
            self.current_website = None

        # 更新描述
        self.detail_desc_text.config(state=tk.NORMAL)
        self.detail_desc_text.delete(1.0, tk.END)
        self.detail_desc_text.insert(1.0, mod_info.mod_description)
        self.detail_desc_text.config(state=tk.DISABLED)



        # 更新路径
        self.detail_path_label.config(text=mod_info.mod_path)

        # 更新启用状态
        self.enabled_var.set(self.config_manager.is_mod_enabled(mod_info.mod_name))

        # 更新文件列表
        self.update_files_list(mod_info.mod_path)

    def update_files_list(self, mod_path):
        """更新文件列表"""
        # 清空列表
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)

        if not os.path.exists(mod_path):
            return

        # 遍历插件目录
        for root, dirs, files in os.walk(mod_path):
            # 计算相对路径
            rel_root = os.path.relpath(root, mod_path)
            if rel_root == ".":
                rel_root = ""

            # 添加文件
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.join(rel_root, file) if rel_root else file

                # 获取文件信息
                try:
                    file_size = os.path.getsize(file_path)
                    mtime = datetime.fromtimestamp(os.path.getmtime(file_path))

                    # 格式化文件大小
                    if file_size < 1024:
                        size_text = f"{file_size}B"
                    elif file_size < 1024 * 1024:
                        size_text = f"{file_size / 1024:.1f}KB"
                    else:
                        size_text = f"{file_size / (1024 * 1024):.1f}MB"

                    # 添加到列表 - 修复版
                    self.files_tree.insert("", "end",
                                           values=(rel_path, size_text, mtime.strftime("%Y-%m-%d %H:%M")),
                                           tags=(file_path,))
                except:
                    pass

        # 如果有文件，自动调整列宽
        if self.files_tree.get_children():
            self.files_tree.update_idletasks()

    def view_attribute_file(self):
        """查看Attribute.txt属性文件"""
        selection = self.mod_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择一个插件")
            return

        item = selection[0]
        mod_name = self.mod_tree.item(item, "tags")[0]

        # 找到插件路径
        for mod_info in self.supported_mod.mods:
            if mod_info.mod_name == mod_name:
                attribute_file = os.path.join(mod_info.mod_path, "Attribute.txt")
                if os.path.exists(attribute_file):
                    try:
                        with open(attribute_file, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # 创建查看窗口
                        attr_window = tk.Toplevel(self.manager_window)
                        attr_window.title(f"属性文件: {mod_info.mod_display_name}")
                        attr_window.geometry("600x500")

                        # 创建文本区域
                        text_widget = scrolledtext.ScrolledText(attr_window, wrap=tk.WORD)
                        text_widget.pack(fill="both", expand=True, padx=10, pady=10)

                        text_widget.insert(1.0, content)
                        text_widget.config(state=tk.DISABLED)

                        # 添加关闭按钮
                        ttk.Button(attr_window, text="关闭",
                                   command=attr_window.destroy).pack(pady=10)

                    except Exception as e:
                        messagebox.showerror("错误", f"无法读取属性文件: {str(e)}")
                else:
                    messagebox.showinfo("提示", f"未找到Attribute.txt文件\n\n插件路径: {mod_info.mod_path}")
                break

    def open_website(self, event=None):
        """打开作者网站"""
        if hasattr(self, 'current_website') and self.current_website:
            try:
                import webbrowser
                # 确保URL格式正确
                url = self.current_website
                if not url.startswith(("http://", "https://")):
                    url = "https://" + url
                webbrowser.open(url)
            except Exception as e:
                messagebox.showerror("错误", f"无法打开网站: {str(e)}")

    def refresh_files_list(self):
        """刷新文件列表"""
        selection = self.mod_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择一个插件")
            return

        item = selection[0]
        mod_name = self.mod_tree.item(item, "tags")[0]

        # 找到插件路径
        for mod_info in self.supported_mod.mods:
            if mod_info.mod_name == mod_name:
                self.update_files_list(mod_info.mod_path)
                break

    def on_search_changed(self, event):
        """搜索文本改变事件"""
        self.refresh_mods_list()

    def save_enabled_setting(self):
        """保存启用设置"""
        selection = self.mod_tree.selection()
        if not selection:
            return

        item = selection[0]
        mod_name = self.mod_tree.item(item, "tags")[0]

        if self.enabled_var.get():
            self.config_manager.enable_mod(mod_name)
        else:
            self.config_manager.disable_mod(mod_name)

        # 更新列表显示
        self.refresh_mods_list()

    def enable_selected_mod(self):
        """启用选中的插件"""
        selection = self.mod_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择一个插件")
            return

        item = selection[0]
        mod_name = self.mod_tree.item(item, "tags")[0]

        self.config_manager.enable_mod(mod_name)
        self.refresh_mods_list()
        messagebox.showinfo("成功", f"已启用插件: {mod_name}")

    def disable_selected_mod(self):
        """禁用选中的插件"""
        selection = self.mod_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择一个插件")
            return

        item = selection[0]
        mod_name = self.mod_tree.item(item, "tags")[0]

        self.config_manager.disable_mod(mod_name)
        self.refresh_mods_list()
        messagebox.showinfo("成功", f"已禁用插件: {mod_name}")

    def uninstall_selected_mod(self):
        """卸载选中的插件（直接删除）"""
        selection = self.mod_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择一个插件")
            return

        item = selection[0]
        mod_name = self.mod_tree.item(item, "tags")[0]

        # 找到插件信息
        mod_info = None
        for m in self.supported_mod.mods:
            if m.mod_name == mod_name:
                mod_info = m
                break

        if not mod_info:
            return

        # 确认对话框 - 警告用户将直接删除
        if not messagebox.askyesno("确认卸载",
                                   f"⚠️ 警告：这将永久删除插件文件！\n\n"
                                   f"插件: {mod_info.mod_display_name}\n"
                                   f"版本: {mod_info.mod_version}\n"
                                   f"作者: {mod_info.mod_author}\n\n"
                                   f"确定要永久删除此插件吗？\n"
                                   f"此操作无法撤销！",
                                   icon=messagebox.WARNING):
            return

        # 可选：再次确认
        if not messagebox.askyesno("最后确认",
                                   f"你确定要永久删除插件吗？\n\n"
                                   f"插件路径: {mod_info.mod_path}\n\n"
                                   f"删除后无法恢复！",
                                   icon=messagebox.ERROR):
            return

        try:
            # 删除插件目录
            if os.path.exists(mod_info.mod_path):
                # 删除整个插件目录
                shutil.rmtree(mod_info.mod_path)
                print(f"已删除插件目录: {mod_info.mod_path}")
            else:
                print(f"插件目录不存在: {mod_info.mod_path}")

            # 删除插件配置
            self.config_manager.delete_mod_config(mod_name)

            # 从列表中移除
            self.supported_mod.mods = [m for m in self.supported_mod.mods if m.mod_name != mod_name]

            # 刷新列表
            self.refresh_mods_list()

            # 清空详情显示
            self.detail_name_label.config(text="")
            self.detail_version_label.config(text="")
            self.detail_author_label.config(text="")
            self.detail_website_label.config(text="")
            self.detail_desc_text.config(state=tk.NORMAL)
            self.detail_desc_text.delete(1.0, tk.END)
            self.detail_desc_text.config(state=tk.DISABLED)

            self.detail_path_label.config(text="")

            # 清空文件列表
            for item in self.files_tree.get_children():
                self.files_tree.delete(item)

            messagebox.showinfo("成功", f"插件已永久删除:\n{mod_info.mod_display_name}")

        except PermissionError as e:
            messagebox.showerror("删除失败", f"无法删除插件，文件可能正在被使用:\n{str(e)}\n\n请关闭相关程序后重试。")
        except Exception as e:
            messagebox.showerror("错误", f"删除插件失败: {str(e)}")

    def scan_for_new_mods(self):
        """扫描新插件"""
        self.status_label.config(text="正在扫描插件...")

        if not self.supported_mod:
            self.status_label.config(text="插件系统未初始化")
            return

        old_count = len(self.supported_mod.mods)
        self.supported_mod.mods = self.supported_mod.scan_mods()
        new_count = len(self.supported_mod.mods)

        self.refresh_mods_list()

        if new_count > old_count:
            messagebox.showinfo("扫描完成", f"发现 {new_count - old_count} 个新插件")

    def view_selected_file(self):
        """查看选中的文件"""
        selection = self.files_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择一个文件")
            return

        item = selection[0]
        file_path = self.files_tree.item(item, "tags")[0]

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 创建查看窗口
            view_window = tk.Toplevel(self.manager_window)
            view_window.title(f"查看文件: {os.path.basename(file_path)}")
            view_window.geometry("800x600")

            text_widget = scrolledtext.ScrolledText(view_window, wrap=tk.WORD)
            text_widget.pack(fill="both", expand=True, padx=10, pady=10)

            text_widget.insert(1.0, content)
            text_widget.config(state=tk.DISABLED)

            # 添加关闭按钮
            ttk.Button(view_window, text="关闭",
                       command=view_window.destroy).pack(pady=10)

        except Exception as e:
            messagebox.showerror("错误", f"无法读取文件: {str(e)}")

    def copy_file_path(self):
        """复制文件路径"""
        selection = self.files_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择一个文件")
            return

        item = selection[0]
        # 从标签中获取文件路径
        tags = self.files_tree.item(item, "tags")
        if tags:
            file_path = tags[0]
        else:
            # 如果标签不存在，尝试从值中获取
            values = self.files_tree.item(item, "values")
            if values:
                filename = values[0]
                # 需要结合插件路径找到完整路径
                mod_selection = self.mod_tree.selection()
                if mod_selection:
                    mod_item = mod_selection[0]
                    mod_name = self.mod_tree.item(mod_item, "tags")[0]
                    for mod_info in self.supported_mod.mods:
                        if mod_info.mod_name == mod_name:
                            file_path = os.path.join(mod_info.mod_path, filename)
                            break

        try:
            self.manager_window.clipboard_clear()
            self.manager_window.clipboard_append(file_path)
            messagebox.showinfo("复制成功", f"已复制文件路径:\n{file_path}")
        except:
            messagebox.showinfo("复制", f"文件路径:\n{file_path}")

    def open_mod_directory(self, event=None):
        """打开插件目录"""
        selection = self.mod_tree.selection()
        if not selection:
            return

        item = selection[0]
        mod_name = self.mod_tree.item(item, "tags")[0]

        # 找到插件路径
        for mod_info in self.supported_mod.mods:
            if mod_info.mod_name == mod_name:
                if os.path.exists(mod_info.mod_path):
                    os.startfile(mod_info.mod_path)
                else:
                    messagebox.showwarning("警告", f"目录不存在: {mod_info.mod_path}")
                break

    def open_mods_directory(self):
        """打开插件目录"""
        if os.path.exists(self.mods_dir):
            os.startfile(self.mods_dir)
        else:
            messagebox.showwarning("警告", f"插件目录不存在: {self.mods_dir}")

    def show_system_info(self):
        """显示系统信息"""
        import platform

        enabled_count = 0
        disabled_count = 0
        error_count = 0

        if self.supported_mod and self.supported_mod.mods:
            for mod_info in self.supported_mod.mods:
                if mod_info.mod_state.name == "ERROR":
                    error_count += 1
                elif self.config_manager.is_mod_enabled(mod_info.mod_name):
                    enabled_count += 1
                else:
                    disabled_count += 1

        info_text = f"""插件系统信息:

系统信息:
  操作系统: {platform.system()} {platform.release()}
  Python版本: {platform.python_version()}
  系统架构: {platform.architecture()[0]}

目录信息:
  插件目录: {os.path.abspath(self.mods_dir)}
  配置文件: {os.path.abspath(self.config_manager.config_file)}

插件统计:
  插件总数: {len(self.supported_mod.mods) if self.supported_mod else 0}
  已启用: {enabled_count}
  已禁用: {disabled_count}
  错误状态: {error_count}

属性文件:
  插件信息从Attribute.txt读取
  格式: 键=值 或 键: 值
  必需字段: DisplayName, Description, Author, Version

卸载说明:
  插件卸载后将永久删除，请谨慎操作
"""

        messagebox.showinfo("系统信息", info_text)

    def show_help(self):
        """显示帮助"""
        help_text = """插件管理器使用帮助:

基本操作:
  1. 点击插件列表中的插件查看详细信息
  2. 使用搜索框快速查找插件
  3. 启用/禁用插件控制插件的加载状态

插件状态:
  ✅ 已启用: 插件已加载并可用
  ⛔ 已禁用: 插件已加载但被禁用
  ⚠ 错误: 插件加载时出现错误

插件属性文件 (Attribute.txt):
  每个插件应包含Attribute.txt文件
  格式: 键=值 或 键: 值
  必需字段:
    DisplayName: 插件显示名称
    Description: 插件描述
    Author: 插件作者
    Version: 插件版本
  可选字段:
    Website: 作者网站
    Features: 支持的功能(用逗号分隔)

文件操作:
  📄 查看文件: 查看插件文件内容
  📋 复制路径: 复制文件完整路径
  📝 查看属性文件: 查看Attribute.txt

操作说明:
  启用插件: 插件将被加载，可在选项卡中使用
  禁用插件: 插件将不会被加载，节省资源
  卸载插件: 永久删除插件文件，无法恢复

⚠️ 重要警告:
  1. 卸载插件将永久删除文件，无法恢复！
  2. 请确保不再需要该插件后再卸载
  3. 建议手动备份重要插件

注意事项:
  1. 修改插件状态后需要重启Itoc才能生效
  2. 插件配置文件保存在ModShezhi.txt中
  3. 点击作者网站链接可直接打开浏览器访问
"""

        # 创建帮助窗口
        help_window = tk.Toplevel(self.manager_window)
        help_window.title("插件管理器帮助")
        help_window.geometry("500x400")

        text_widget = scrolledtext.ScrolledText(help_window, wrap=tk.WORD)
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)

        text_widget.insert(1.0, help_text)
        text_widget.config(state=tk.DISABLED)

        ttk.Button(help_window, text="关闭",
                   command=help_window.destroy).pack(pady=10)

    def on_manager_close(self):
        """关闭管理器窗口"""
        if hasattr(self, 'manager_window'):
            self.manager_window.destroy()
            del self.manager_window

    def cleanup(self):
        """清理资源"""
        if hasattr(self, 'manager_window') and self.manager_window.winfo_exists():
            self.manager_window.destroy()
        print("插件管理器已清理")