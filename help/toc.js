// ===== 帮助文档目录数据 =====
// 请确保此文件与 help.html 放在同一目录下。
// 对应的 .html 文件需要根据此目录结构创建。
// 分组说明：group 字段用于在侧边栏中显示分组标题。

const TOC_DATA = [
    // ==================== 入门篇 ====================
    { group: '入门篇' },
    { title: '初识 Itoc', file: 'start.html' },
    { title: '安装与启动', file: 'install.html' },
    { title: '界面概览', file: 'interface.html' },
    { title: '快速上手：您的第一个项目', file: 'quickstart.html' },
    { title: '时间轴与音符编辑', file: 'timeline.html' },
    { title: '作品元数据', file: 'metadata.html' },
    // ==================== 弹窗编排 ====================
    { group: '弹窗编排' },
    { title: 'CZEmaker 弹窗编排 · 基础篇', file: 'czemaker.html' },
    { title: 'CZEmaker 弹窗编排 · 进阶篇', file: 'czemaker_advanced.html' },
    { title: '窗口样式钮', file: 'window_style.html' },
    { title: '镂空窗口', file: 'hollow_window.html' },
    { title: '亚克力与云母', file: 'acrylic_mica.html' },
    { title: '普通弹窗（信息/警告/错误/询问）', file: 'window_type_regular.html' },
    { title: '图片框', file: 'window_type_image.html' },
    { title: '视频框', file: 'window_type_video.html' },
    { title: '气泡 / 通知', file: 'window_type_notice.html' },
    { title: '执行代码', file: 'window_type_code.html' },
    { title: '模类框', file: 'window_type_uiclass.html' },

    // ==================== 事件块与音符 ====================
    { group: '事件块与音符' },
    { title: '音符块自身属性', file: 'midi_color.html' },
    { title: '绘制音符块', file: 'paint.html' },
    { title: '调整图层', file: 'adjust_layer.html' },
    { title: '启用/禁用事件块或全局命令', file: 'disabled_blocks.html' },
    { title: '新建节奏事件点', file: 'beat_event_point.html' },
    { title: '新建并发事件点', file: 'concurrent_event_point.html' },

    // ==================== 动画与音效 ====================
    { group: '动画与音效' },
    { title: '过渡动画', file: 'transition.html' },
    { title: '根据窗口类型赋予自定义音效', file: 'assign_window_sound.html' },
    { title: '音频音谱', file: 'yinpin_yinpu.html' },

    // ==================== 全局命令 ====================
    { group: '全局命令' },
    { title: '全局命令 · 基础篇', file: 'global_1.html' },
    { title: '全局命令 · 进阶篇', file: 'global_2.html' },
    { title: '全局命令 · 窗口位移动画', file: 'cmd_window_animation.html' },
    { title: '全局命令 · 鼠标移动', file: 'cmd_mouse_move.html' },
    { title: '全局命令 · 镜像克隆编组', file: 'cmd_mirror_clone.html' },
    { title: '全局命令 · 设置桌面背景', file: 'cmd_wallpaper.html' },

    // ==================== 阵列系统 ====================
    { group: '阵列系统' },
    { title: '阵列设计器 · 总览', file: 'array.html' },
    { title: '直线阵列', file: 'array_linear.html' },
    { title: '贝塞尔曲线阵列', file: 'array_bezier.html' },
    { title: '多边形阵列', file: 'array_polygon.html' },
    { title: '环形阵列', file: 'array_circle.html' },
    { title: '极坐标阵列', file: 'array_polar.html' },
    { title: 'SVG阵列', file: 'array_svg.html' },

    // ==================== 窗口类名与编组 ====================
    { group: '窗口类名与编组' },
    { title: '窗口类名', file: 'cze_window_class.html' },
    { title: '窗口编组', file: 'cze_window_group.html' },

    // ==================== 模类系统 ====================
    { group: '模类系统 (UI Class)' },
    { title: '初识模类', file: 'uiclass_1.html' },
    { title: '模类设计器详解', file: 'uiclass_2.html' },
    { title: '模类进阶与生态', file: 'uiclass_3.html' },

    // ==================== 侧边栏与辅助工具 ====================
    { group: '侧边栏与辅助工具' },
    { title: '侧边栏', file: 'sidebar.html' },
    { title: '显示器', file: 'sidebar_display.html' },
    { title: '参考媒体', file: 'sidebar_reference_media.html' },
    { title: '字幕', file: 'str.html' },
    { title: '标记与轨道便利贴', file: 'marker_and_sticky_note.html' },
    { title: '媒体浏览器', file: 'media_browser.html' },
    { title: '高能进度表', file: 'high_energy_table.html' },
    { title: '终端', file: 'terminal.html' },
    { title: '代码视图', file: 'code_view.html' },
    { title: '窗口拾取器', file: 'GetWindowClassName.html' },

    // ==================== 歌词、协作与历史 ====================
    { group: '歌词、协作与历史' },
    { title: '插入歌词', file: 'insert_lyrics.html' },
    { title: '协作', file: 'cooperation.html' },
    { title: '撤销与重做', file: 'ctrl_z_undo_redo.html' },

    // ==================== 渲染与输出 ====================
    { group: '渲染与输出' },
    { title: '渲染为 CZE 数据文件', file: 'render_cze_data.html' },
    { title: '渲染为 Python 代码', file: 'render_python_code.html' },
    { title: '渲染为音频文件', file: 'export_audio.html' },
    { title: '渲染视频文件', file: 'render_video.html' },

    // ==================== 编译与运行 ====================
    { group: '编译与运行' },
    { title: '编译为 exe', file: 'compile_exe.html' },
    { title: '组装打包模式', file: 'assembly_package.html' },
    { title: '解释器自定义配置', file: 'interpreter_config.html' },
    { title: '测试运行', file: 'test_run.html' },
    { title: '运行日志', file: 'run_log.html' },
    { title: 'Python 运行库', file: 'python_libs.html' },

    // ==================== 设置与个性化 ====================
    { group: '设置与个性化' },
    { title: '首选项（设置）', file: 'settings.html' },
    { title: '皮肤设置', file: 'settings_skin.html' },
    { title: '文件关联（打开方式）', file: 'file_association.html' },

    // ==================== 多语言与插件 ====================
    { group: '多语言与插件' },
    { title: '语言包', file: 'language_pack.html' },
    { title: '插件使用指南', file: 'plugin_user.html' },
    { title: '插件开发指南', file: 'plugin_dev.html' },

    // ==================== 其他 ====================
    { group: '其他' },
    { title: '轮播图', file: 'carousel.html' },
];