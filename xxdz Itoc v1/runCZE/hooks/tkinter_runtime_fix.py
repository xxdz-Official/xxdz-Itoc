# -*- coding: utf-8 -*-
# 自定义Tkinter运行时钩子，修复Tk数据目录问题
import os
import sys
import tkinter
import tempfile
import ctypes
import ctypes.wintypes

def _pyi_rthook():
    # 修复Tkinter在PyInstaller中的路径问题
    if getattr(sys, 'frozen', False):
        # 如果是打包后的EXE
        base_dir = sys._MEIPASS

        # 尝试从多个可能的位置查找Tcl/Tk
        possible_tcl_dirs = [
            os.path.join(base_dir, 'tcl'),
            os.path.join(base_dir, '_internal', 'tcl'),
            os.path.join(os.path.dirname(sys.executable), 'tcl'),
        ]

        possible_tk_dirs = [
            os.path.join(base_dir, 'tk'),
            os.path.join(base_dir, '_internal', 'tk'),
            os.path.join(os.path.dirname(sys.executable), 'tk'),
        ]

        tcl_found = False
        tk_found = False

        # 查找Tcl目录
        for tcl_dir in possible_tcl_dirs:
            if os.path.exists(tcl_dir):
                os.environ['TCL_LIBRARY'] = tcl_dir
                tcl_found = True
                if hasattr(sys, '_debug') and sys._debug:
                    print(f"找到TCL_LIBRARY: {tcl_dir}")
                break

        # 查找Tk目录
        for tk_dir in possible_tk_dirs:
            if os.path.exists(tk_dir):
                os.environ['TK_LIBRARY'] = tk_dir
                tk_found = True
                if hasattr(sys, '_debug') and sys._debug:
                    print(f"找到TK_LIBRARY: {tk_dir}")
                break

        # 如果还没找到，尝试在tcl目录下查找tk子目录
        if not tk_found and tcl_found:
            tcl_dir = os.environ.get('TCL_LIBRARY', '')
            if tcl_dir:
                for item in os.listdir(tcl_dir):
                    if item.lower().startswith('tk'):
                        tk_path = os.path.join(tcl_dir, item)
                        if os.path.isdir(tk_path):
                            os.environ['TK_LIBRARY'] = tk_path
                            tk_found = True
                            if hasattr(sys, '_debug') and sys._debug:
                                print(f"在Tcl目录下找到TK_LIBRARY: {tk_path}")
                            break

# 立即执行钩子
_pyi_rthook()
