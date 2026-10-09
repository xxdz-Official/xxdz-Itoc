/* ============================================================
   layout.js - Itoc 帮助文档动态布局渲染
   依赖：toc.js（提供 TOC_DATA）
   用法：
     renderLayout({
         currentFile: 'start.html',
         pageTitle: '初识 Itoc'
     });
   ============================================================ */

(function (global) {

    // ==================== 顶栏 HTML ====================
    function buildHeader(pageTitle) {
        return `
        <div class="header-row">
            <a class="logo-area" href="help.html" title="返回帮助文档首页">
                <img src="../icon.png" alt="Itoc logo" class="logo-img">
                <h1>Itoc 帮助文档${pageTitle ? ' - ' + pageTitle : ''}</h1>
            </a>
            <div class="top-bar">
                <a href="https://message.bilibili.com/#/whisper/mid3461569935575626" target="_blank"><span>联系作者</span></a>
                <a href="https://miku66ccff.freeflarum.com/t/itoc" target="_blank"><span>交流论坛</span></a>
                <a href="https://github.com/xxdz-Official/xxdz-Itoc" target="_blank"><span>GitHub主页</span></a>
                <a href="../Mode.html"><span>插件市场</span></a>
                <a href="../FriendURL.html"><span>友情链接</span></a>
                <a href="help.html"><span>帮助文档</span></a>
            </div>
        </div>`;
    }

    // ==================== 侧边栏 HTML ====================
    function buildSidebar(data, currentFile) {
        let lis = '';
        data.forEach((item) => {
            if (item.group) {
                lis += `<li class="toc-group"><span>${item.group}</span></li>`;
            } else if (item.title) {
                const active = item.file === currentFile ? ' active' : '';
                lis += `<li class="toc-item${active}" data-file="${item.file}"><span>${item.title}</span></li>`;
            }
        });
        return `
        <nav class="sidebar" id="sidebar">
            <h3 class="sidebar-title">📖 目录</h3>
            <div class="toc-search-box">
                <div class="toc-search-field">
                    <span class="toc-search-icon" aria-hidden="true">
                        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="11" cy="11" r="7"></circle>
                            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                        </svg>
                    </span>
                    <input type="text" id="tocSearchInput" class="toc-search-input" placeholder="搜索目录喵..." autocomplete="off">
                    <button type="button" id="tocSearchClear" class="toc-search-clear" title="清空" aria-label="清空搜索">
                        <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round">
                            <line x1="6" y1="6" x2="18" y2="18"></line>
                            <line x1="18" y1="6" x2="6" y2="18"></line>
                        </svg>
                    </button>
                </div>
            </div>
            <div id="tocEmptyTip" class="toc-empty-tip" style="display:none;">没有找到匹配的条目</div>
            <ul id="tocList" class="toc-list-loading">${lis}</ul>
        </nav>`;
    }

    // ==================== 主渲染函数 ====================
    function renderLayout(options) {
        const opts = options || {};
        const currentFile = opts.currentFile || '';
        const pageTitle = opts.pageTitle || '';

        // 渲染顶栏
        const headerHolder = document.getElementById('header-placeholder');
        if (headerHolder) {
            headerHolder.innerHTML = buildHeader(pageTitle);
        }

        // 渲染侧边栏 + 内容区包裹
        const layoutHolder = document.getElementById('layout-placeholder');
        const docContent = document.getElementById('doc-content');

        if (layoutHolder && docContent && typeof TOC_DATA !== 'undefined') {
            layoutHolder.innerHTML = `
                <div class="main-container">
                    ${buildSidebar(TOC_DATA, currentFile)}
                    <main class="content-area" id="contentArea"></main>
                </div>`;

            // 把正文内容搬进内容区
            const contentArea = document.getElementById('contentArea');
            contentArea.innerHTML = docContent.innerHTML;
            docContent.remove();

            // 显示整个布局
            layoutHolder.style.display = 'block';

            // ==================== 移动端视口高度适配 ====================
            // 移动端浏览器地址栏会伸缩，100vh 会变化，导致内容被裁切
            // 用 JS 动态设置 --vh 变量，让 CSS 里的高度计算更稳定
            function setMobileVh() {
                const vh = window.innerHeight * 0.01;
                document.documentElement.style.setProperty('--vh', vh + 'px');
            }
            setMobileVh();
            // 监听窗口 resize / orientationchange
            window.addEventListener('resize', setMobileVh);
            window.addEventListener('orientationchange', setMobileVh);

            // 绑定目录点击
            document.querySelectorAll('#tocList li.toc-item').forEach((li) => {
                li.addEventListener('click', function () {
                    const file = this.dataset.file;
                    if (!file) return;
                    // 如果点的是当前页，不跳转
                    if (file === currentFile) return;
                    window.location.href = file;
                });
            });

            // ==================== 目录加载完成动画（逐条滑入） ====================
            playTocListEntrance();

            // 滚动到当前高亮项（动画播完再平滑滚动，避免抖动）
            setTimeout(() => {
                const activeItem = document.querySelector('#tocList li.active');
                if (activeItem) {
                    activeItem.scrollIntoView({ block: 'center', behavior: 'smooth' });
                }
            }, 420);

            // ==================== 目录搜索功能 ====================
            bindTocSearch();

            // ==================== 正文加载动画 ====================
            playContentEntrance();

            // ==================== 代码块复制按钮 ====================
            bindCodeCopyButtons();
        } else {
            // 兜底：如果缺东西，至少把正文显示出来
            if (docContent) {
                docContent.style.display = 'block';
            }
        }
    }

    // ==================== 目录搜索绑定 ====================
    function bindTocSearch() {
        const searchInput = document.getElementById('tocSearchInput');
        const clearBtn = document.getElementById('tocSearchClear');
        const emptyTip = document.getElementById('tocEmptyTip');
        const tocList = document.getElementById('tocList');
        if (!searchInput || !tocList) return;

        // 收集所有条目（保留原始 DOM 引用）
        const allItems = Array.from(tocList.querySelectorAll('li.toc-item'));
        const allGroups = Array.from(tocList.querySelectorAll('li.toc-group'));

        // 是否处于"搜索中"状态
        let isSearching = false;

        function resetItemAnimation(li) {
            li.classList.remove('toc-anim-in');
            // 强制 reflow，确保动画能重播
            void li.offsetWidth;
        }

        // 清空动画锁，避免连点导致动画叠加
        let clearAnimLock = false;

        // 真正的"显示全部"逻辑（不含动画，供清空动画的第二步调用）
        function showAllItems() {
            isSearching = false;
            allItems.forEach((li) => {
                resetItemAnimation(li);
                li.classList.remove('toc-clear-out');
                li.style.display = '';
                li.style.animationDelay = '';
            });
            allGroups.forEach((li) => {
                li.style.display = '';
                li.classList.remove('toc-clear-out');
            });
            if (emptyTip) emptyTip.style.display = 'none';
        }

        // 清空动画：先淡出所有可见条目，再恢复完整列表并逐条淡入
        function clearWithAnimation() {
            if (clearAnimLock) return;
            clearAnimLock = true;

            // 1) 找出当前所有可见的条目
            const visibleItems = allItems.filter(
                (li) => li.style.display !== 'none'
            );
            const visibleGroups = allGroups.filter(
                (li) => li.style.display !== 'none'
            );
            const allVisible = visibleItems.concat(visibleGroups);

            // 2) 给它们加淡出类
            allVisible.forEach((li) => {
                li.classList.remove('toc-enter', 'toc-anim-in');
                li.classList.add('toc-clear-out');
            });

            // 3) 淡出 180ms 后恢复完整列表，并让全部条目淡入
            setTimeout(() => {
                // 移除淡出类
                allItems.forEach((li) => li.classList.remove('toc-clear-out'));
                allGroups.forEach((li) => li.classList.remove('toc-clear-out'));

                // 恢复完整列表
                showAllItems();

                // 全部条目做一次"入场淡入"
                const allListItems = Array.from(tocList.querySelectorAll('li.toc-item, li.toc-group'));
                allListItems.forEach((li, index) => {
                    li.classList.remove('toc-enter');
                    void li.offsetWidth;
                    li.style.animationDelay = Math.min(index * 8, 200) + 'ms';
                    li.classList.add('toc-enter');
                });

                // 动画结束后清理
                const totalTime = Math.min(allListItems.length * 8, 200) + 360;
                setTimeout(() => {
                    allListItems.forEach((li) => {
                        li.classList.remove('toc-enter');
                        li.style.animationDelay = '';
                    });
                    clearAnimLock = false;
                }, totalTime);
            }, 180);
        }

        function applyFilter(keyword) {
            const kw = (keyword || '').trim().toLowerCase();

            // 空关键字：如果有搜索过（isSearching 为 true），走"清空动画"；否则直接显示
            if (!kw) {
                if (isSearching) {
                    clearWithAnimation();
                } else {
                    showAllItems();
                }
                return;
            }

            isSearching = true;
            let visibleCount = 0;
            let animIndex = 0;

            allItems.forEach((li) => {
                const text = (li.textContent || '').toLowerCase();
                if (text.includes(kw)) {
                    resetItemAnimation(li);
                    li.classList.remove('toc-clear-out');
                    li.style.display = '';
                    // 逐条延迟淡入，序号 * 18ms，最多延迟 260ms
                    li.style.animationDelay = Math.min(animIndex * 18, 260) + 'ms';
                    li.classList.add('toc-anim-in');
                    animIndex++;
                    visibleCount++;
                } else {
                    li.style.display = 'none';
                }
            });

            // 分组标题：如果该分组下没有任何可见条目，则隐藏
            allGroups.forEach((groupLi) => {
                let sibling = groupLi.nextElementSibling;
                let hasVisible = false;
                while (sibling && !sibling.classList.contains('toc-group')) {
                    if (sibling.classList.contains('toc-item') && sibling.style.display !== 'none') {
                        hasVisible = true;
                        break;
                    }
                    sibling = sibling.nextElementSibling;
                }
                groupLi.style.display = hasVisible ? '' : 'none';
            });

            if (emptyTip) {
                emptyTip.style.display = visibleCount === 0 ? 'block' : 'none';
                if (visibleCount === 0) {
                    // 重新触发空提示的淡入
                    emptyTip.classList.remove('toc-anim-in');
                    void emptyTip.offsetWidth;
                    emptyTip.classList.add('toc-anim-in');
                }
            }
        }

        // 输入实时过滤
        searchInput.addEventListener('input', function () {
            applyFilter(this.value);
        });

        // 回车：不提交（防止误触），只过滤
        searchInput.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                applyFilter(this.value);
            }
            if (e.key === 'Escape') {
                this.value = '';
                applyFilter('');
            }
        });

        // 清空按钮
        if (clearBtn) {
            clearBtn.addEventListener('click', function () {
                searchInput.value = '';
                applyFilter('');
                searchInput.focus();
                clearBtn.classList.remove('visible');
            });
        }

        // 显示清空按钮的逻辑：有内容时才显示（用 class 触发过渡）
        searchInput.addEventListener('input', function () {
            if (clearBtn) {
                if (this.value) {
                    clearBtn.classList.add('visible');
                } else {
                    clearBtn.classList.remove('visible');
                }
            }
        });
        // 初始化状态
        if (clearBtn) clearBtn.classList.remove('visible');
    }

    // ==================== 目录加载完成动画 ====================
    function playTocListEntrance() {
        const tocList = document.getElementById('tocList');
        if (!tocList) return;

        // 先移除 loading 类（保留初始不可见状态），再逐条触发动画
        const items = Array.from(tocList.querySelectorAll('li.toc-item, li.toc-group'));

        // 初始状态：全部隐藏
        items.forEach((li) => {
            li.classList.add('toc-loading');
            li.classList.remove('toc-enter');
        });

        // 移除 ul 的 loading 类（把 ul 本身从隐藏中释放，但子项仍隐藏）
        tocList.classList.remove('toc-list-loading');
        tocList.classList.add('toc-list-ready');

        // 逐条触发动画：每条延迟 14ms，最多延迟 400ms
        items.forEach((li, index) => {
            const delay = Math.min(index * 14, 400);
            setTimeout(() => {
                li.classList.remove('toc-loading');
                li.classList.add('toc-enter');
            }, delay);
        });

        // 动画播完后清理 class，恢复普通状态（避免影响后续 hover/搜索）
        const totalTime = Math.min(items.length * 14, 400) + 360;
        setTimeout(() => {
            items.forEach((li) => {
                li.classList.remove('toc-enter');
            });
        }, totalTime);
    }

    // ==================== 正文加载动画 ====================
    function playContentEntrance() {
        const contentArea = document.getElementById('contentArea');
        if (!contentArea) return;

        // 尊重用户的"减少动画"偏好：如果系统开启了减少动态效果，直接跳过
        if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            return;
        }

        // 纯 CSS 动画，不碰 DOM，爬虫安全
        // 先移除类（确保动画能重播），强制 reflow，再加类
        contentArea.classList.remove('content-entrance');
        void contentArea.offsetWidth;
        contentArea.classList.add('content-entrance');

        // 动画播完后清理类，恢复普通状态
        const onEnd = () => {
            contentArea.classList.remove('content-entrance');
            contentArea.removeEventListener('animationend', onEnd);
        };
        contentArea.addEventListener('animationend', onEnd);
    }

    // ==================== 代码块复制按钮 ====================
    function bindCodeCopyButtons() {
        const contentArea = document.getElementById('contentArea');
        if (!contentArea) return;

        // 找到正文里所有的 <pre> 代码块（不含行内 code）
        const preBlocks = contentArea.querySelectorAll('pre');

        preBlocks.forEach((pre) => {
            // 防止重复绑定
            if (pre.querySelector('.code-copy-btn')) return;

            // 给 pre 加个类，方便 CSS 定位
            pre.classList.add('has-copy-btn');

            // 创建按钮
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'code-copy-btn';
            btn.setAttribute('aria-label', '复制代码');
            btn.setAttribute('title', '复制代码');
            // 用内联 SVG 做"复制"图标，不用 emoji
            btn.innerHTML = `
                <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="9" y="9" width="11" height="11" rx="1.5"></rect>
                    <path d="M5 15V5a1 1 0 0 1 1-1h10"></path>
                </svg>
                <span class="code-copy-text">复制</span>
            `;

            // 点击：复制代码
            btn.addEventListener('click', function (e) {
                e.preventDefault();
                e.stopPropagation();

                // 取出 pre 里的纯代码文本（去掉按钮自身）
                let codeText = '';
                const codeEl = pre.querySelector('code');
                if (codeEl) {
                    // 克隆一份，避免把按钮文字也复制进去
                    const clone = codeEl.cloneNode(true);
                    // 移除可能存在的按钮
                    clone.querySelectorAll('.code-copy-btn').forEach((b) => b.remove());
                    codeText = clone.textContent;
                } else {
                    const clone = pre.cloneNode(true);
                    clone.querySelectorAll('.code-copy-btn').forEach((b) => b.remove());
                    codeText = clone.textContent;
                }

                // 复制到剪贴板
                copyTextToClipboard(codeText).then((ok) => {
                    if (ok) {
                        btn.classList.add('copied');
                        const textSpan = btn.querySelector('.code-copy-text');
                        if (textSpan) textSpan.textContent = '已复制';
                        // 1.4 秒后恢复
                        setTimeout(() => {
                            btn.classList.remove('copied');
                            if (textSpan) textSpan.textContent = '复制';
                        }, 1400);
                    } else {
                        // 复制失败：短暂显示"失败"
                        const textSpan = btn.querySelector('.code-copy-text');
                        if (textSpan) textSpan.textContent = '复制失败';
                        setTimeout(() => {
                            if (textSpan) textSpan.textContent = '复制';
                        }, 1400);
                    }
                });
            });

            // 把按钮插入 pre 开头
            pre.insertBefore(btn, pre.firstChild);
        });
    }

    // 复制文本到剪贴板（兼容新旧浏览器）
    function copyTextToClipboard(text) {
        return new Promise((resolve) => {
            // 优先用现代 API
            if (navigator.clipboard && window.isSecureContext) {
                navigator.clipboard.writeText(text).then(
                    () => resolve(true),
                    () => resolve(fallbackCopy(text))
                );
            } else {
                resolve(fallbackCopy(text));
            }
        });
    }

    // 兜底方案：用 textarea + execCommand
    function fallbackCopy(text) {
        try {
            const ta = document.createElement('textarea');
            ta.value = text;
            ta.style.position = 'fixed';
            ta.style.top = '-9999px';
            ta.style.left = '-9999px';
            ta.setAttribute('readonly', '');
            document.body.appendChild(ta);
            ta.select();
            const ok = document.execCommand('copy');
            document.body.removeChild(ta);
            return ok;
        } catch (e) {
            return false;
        }
    }

    // 暴露到全局
    global.renderLayout = renderLayout;

})(window);