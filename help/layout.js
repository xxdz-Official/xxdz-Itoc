/* LAYOUT_JS_VERSION: 3.1-static */
/* ============================================================
   layout.js - Itoc 帮助文档动态布局渲染（v3.1 调试日志 + 搜索兜底）
   本版改动：
     1. 每一步都 console.log，方便在 F12 Console 里排查
     2. bindInteractions 里每一步用 try/catch，某步出错不阻断后面的绑定
     3. bindTocSearch 里 applyFilter 打印过滤前后可见条目数
   ============================================================ */

(function (global) {

    var LOG = function () {
        try { console.log.apply(console, ['[Itoc]'].concat(Array.prototype.slice.call(arguments))); } catch (e) {}
    };
    var WARN = function () {
        try { console.warn.apply(console, ['[Itoc]'].concat(Array.prototype.slice.call(arguments))); } catch (e) {}
    };
    var ERR = function () {
        try { console.error.apply(console, ['[Itoc]'].concat(Array.prototype.slice.call(arguments))); } catch (e) {}
    };

    // ==================== 顶栏 HTML（兼容模式用） ====================
    function buildHeader(pageTitle) {
        return `
        <div class="header-row">
            <a class="logo-area" href="help.html" title="返回帮助文档首页">
                <img src="../icon.png" alt="Itoc logo" class="logo-img">
                <h1>Itoc 帮助文档${pageTitle ? ' - ' + pageTitle : ''}</h1>
            </a>
            <div class="top-bar">
                <a href="https://xxdz-official.github.io/xxdz-Itoc/" target="_blank" rel="noopener"><span>项目主页</span></a>
                <a href="https://message.bilibili.com/#/whisper/mid3461569935575626" target="_blank"><span>联系作者</span></a>
                <a href="https://miku66ccff.freeflarum.com/t/itoc" target="_blank"><span>交流论坛</span></a>
                <a href="https://github.com/xxdz-Official/xxdz-Itoc" target="_blank"><span>GitHub主页</span></a>
                <a href="../Mode.html"><span>插件市场</span></a>
                <a href="help.html"><span>帮助文档</span></a>
            </div>
        </div>`;
    }

    function buildSidebar(data, currentFile) {
        let lis = '';
        data.forEach((item) => {
            if (item.group) {
                lis += `<li class="toc-group"><span>${item.group}</span></li>`;
            } else if (item.title) {
                const active = item.file === currentFile ? ' active' : '';
                lis += `<li class="toc-item${active}" data-file="${item.file}"><a href="${item.file}" rel="noopener"><span>${item.title}</span></a></li>`;
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

        LOG('renderLayout 开始 currentFile=', currentFile, 'pageTitle=', pageTitle);

        try { injectFavicon(); } catch (e) { WARN('injectFavicon 出错', e); }

        const headerHolder = document.getElementById('header-placeholder');
        const layoutHolder = document.getElementById('layout-placeholder');
        const docContent = document.getElementById('doc-content');
        const tocList = document.getElementById('tocList');

        LOG('headerHolder?', !!headerHolder,
            'headerHasContent?', !!(headerHolder && headerHolder.innerHTML.trim().length > 0),
            'layoutHolder?', !!layoutHolder,
            'layoutHasContent?', !!(layoutHolder && layoutHolder.innerHTML.trim().length > 0),
            'tocList?', !!tocList);

        const isStaticLayout =
            headerHolder && headerHolder.innerHTML.trim().length > 0 &&
            layoutHolder && layoutHolder.innerHTML.trim().length > 0 &&
            tocList;

        LOG('isStaticLayout =', !!isStaticLayout);

        if (!isStaticLayout) {
            LOG('走兼容模式（用 TOC_DATA 生成布局）');
            try {
                if (headerHolder) headerHolder.innerHTML = buildHeader(pageTitle);
                if (layoutHolder && docContent && typeof TOC_DATA !== 'undefined') {
                    layoutHolder.innerHTML = `
                        <div class="main-container">
                            ${buildSidebar(TOC_DATA, currentFile)}
                            <main class="content-area" id="contentArea"></main>
                        </div>`;
                    const contentArea = document.getElementById('contentArea');
                    contentArea.innerHTML = docContent.innerHTML;
                    docContent.remove();
                    layoutHolder.style.display = 'block';
                } else {
                    if (docContent) docContent.style.display = 'block';
                    WARN('兼容模式缺少 TOC_DATA 或 layoutHolder/docContent');
                    return;
                }
            } catch (e) {
                ERR('兼容模式构建布局出错', e);
                return;
            }
        }

        LOG('调用 bindInteractions');
        bindInteractions();
        LOG('renderLayout 结束');
    }

    // ==================== 共用交互绑定（每步 try/catch） ====================
    function bindInteractions() {
        LOG('bindInteractions 开始');

        try {
            function setMobileVh() {
                const vh = window.innerHeight * 0.01;
                document.documentElement.style.setProperty('--vh', vh + 'px');
            }
            setMobileVh();
            window.addEventListener('resize', setMobileVh);
            window.addEventListener('orientationchange', setMobileVh);
            LOG('setMobileVh 绑定完成');
        } catch (e) { WARN('setMobileVh 出错', e); }

        try {
            const tocList = document.getElementById('tocList');
            if (tocList && tocList.classList.contains('toc-list-loading')) {
                LOG('playTocListEntrance 开始');
                playTocListEntrance();
            } else {
                LOG('playTocListEntrance 跳过（tocList 已不是 loading 状态）');
            }
        } catch (e) { WARN('playTocListEntrance 出错', e); }

        try {
            setTimeout(() => {
                try {
                    const activeItem = document.querySelector('#tocList li.active');
                    if (activeItem) {
                        activeItem.scrollIntoView({ block: 'center', behavior: 'smooth' });
                    }
                } catch (e) { WARN('scrollIntoView 出错', e); }
            }, 420);
            LOG('scrollIntoView 已排队');
        } catch (e) { WARN('scrollIntoView 排队出错', e); }

        try {
            LOG('bindTocSearch 开始');
            bindTocSearch();
            LOG('bindTocSearch 完成');
        } catch (e) { ERR('bindTocSearch 出错', e); }

        try {
            playContentEntrance();
            LOG('playContentEntrance 完成');
        } catch (e) { WARN('playContentEntrance 出错', e); }

        try {
            bindCodeCopyButtons();
            LOG('bindCodeCopyButtons 完成');
        } catch (e) { WARN('bindCodeCopyButtons 出错', e); }

        LOG('bindInteractions 结束');
    }

    // ==================== 目录搜索绑定（带详细调试） ====================
    function bindTocSearch() {
        const searchInput = document.getElementById('tocSearchInput');
        const clearBtn = document.getElementById('tocSearchClear');
        const emptyTip = document.getElementById('tocEmptyTip');
        const tocList = document.getElementById('tocList');

        LOG('searchInput?', !!searchInput, 'clearBtn?', !!clearBtn, 'emptyTip?', !!emptyTip, 'tocList?', !!tocList);

        if (!searchInput || !tocList) {
            WARN('缺少 searchInput 或 tocList，无法绑定搜索');
            return;
        }

        const allItems = Array.from(tocList.querySelectorAll('li.toc-item'));
        const allGroups = Array.from(tocList.querySelectorAll('li.toc-group'));
        LOG('allItems =', allItems.length, 'allGroups =', allGroups.length);

        if (allItems.length === 0) {
            WARN('⚠️ 目录里一个 li.toc-item 都没有！请检查 HTML 中 #tocList 是否有 <li class="toc-item">');
            return;
        }

        let isSearching = false;

        function resetItemAnimation(li) {
            li.classList.remove('toc-anim-in');
            void li.offsetWidth;
        }

        let clearAnimLock = false;

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
            LOG('showAllItems: 已显示全部', allItems.length, '条');
        }

        function clearWithAnimation() {
            if (clearAnimLock) return;
            clearAnimLock = true;
            LOG('clearWithAnimation 开始');
            const visibleItems = allItems.filter((li) => li.style.display !== 'none');
            const visibleGroups = allGroups.filter((li) => li.style.display !== 'none');
            const allVisible = visibleItems.concat(visibleGroups);
            allVisible.forEach((li) => {
                li.classList.remove('toc-enter', 'toc-anim-in');
                li.classList.add('toc-clear-out');
            });
            setTimeout(() => {
                allItems.forEach((li) => li.classList.remove('toc-clear-out'));
                allGroups.forEach((li) => li.classList.remove('toc-clear-out'));
                showAllItems();
                const allListItems = Array.from(tocList.querySelectorAll('li.toc-item, li.toc-group'));
                allListItems.forEach((li, index) => {
                    li.classList.remove('toc-enter');
                    void li.offsetWidth;
                    li.style.animationDelay = Math.min(index * 8, 200) + 'ms';
                    li.classList.add('toc-enter');
                });
                const totalTime = Math.min(allListItems.length * 8, 200) + 360;
                setTimeout(() => {
                    allListItems.forEach((li) => {
                        li.classList.remove('toc-enter');
                        li.style.animationDelay = '';
                    });
                    clearAnimLock = false;
                    LOG('clearWithAnimation 完成');
                }, totalTime);
            }, 180);
        }

        function applyFilter(keyword) {
            LOG('applyFilter 开始 keyword=', JSON.stringify(keyword));
            const kw = (keyword || '').trim().toLowerCase();
            if (!kw) {
                if (isSearching) clearWithAnimation();
                else showAllItems();
                return;
            }
            isSearching = true;
            let visibleCount = 0;
            let animIndex = 0;
            const groupDisplay = {};

            allItems.forEach((li) => {
                const text = (li.textContent || '').toLowerCase();
                if (text.includes(kw)) {
                    resetItemAnimation(li);
                    li.classList.remove('toc-clear-out');
                    li.style.display = '';
                    li.style.animationDelay = Math.min(animIndex * 18, 260) + 'ms';
                    li.classList.add('toc-anim-in');
                    animIndex++;
                    visibleCount++;
                } else {
                    li.style.display = 'none';
                }
            });
            LOG('applyFilter: 匹配到', visibleCount, '条');

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
                const gName = (groupLi.textContent || '').trim();
                groupDisplay[gName] = hasVisible ? 'block' : 'none';
            });
            LOG('分组显示状态:', groupDisplay);

            if (emptyTip) {
                emptyTip.style.display = visibleCount === 0 ? 'block' : 'none';
                if (visibleCount === 0) {
                    emptyTip.classList.remove('toc-anim-in');
                    void emptyTip.offsetWidth;
                    emptyTip.classList.add('toc-anim-in');
                }
            }
            LOG('applyFilter 结束');
        }

        searchInput.addEventListener('input', function () {
            LOG('input 事件触发 value=', JSON.stringify(this.value));
            applyFilter(this.value);
        });
        searchInput.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') { e.preventDefault(); applyFilter(this.value); }
            if (e.key === 'Escape') { this.value = ''; applyFilter(''); }
        });
        if (clearBtn) {
            clearBtn.addEventListener('click', function () {
                searchInput.value = '';
                applyFilter('');
                searchInput.focus();
                clearBtn.classList.remove('visible');
            });
        }
        searchInput.addEventListener('input', function () {
            if (clearBtn) {
                if (this.value) clearBtn.classList.add('visible');
                else clearBtn.classList.remove('visible');
            }
        });
        if (clearBtn) clearBtn.classList.remove('visible');

        LOG('bindTocSearch: 事件监听已绑定');
    }

    // ==================== 目录加载完成动画 ====================
    function playTocListEntrance() {
        const tocList = document.getElementById('tocList');
        if (!tocList) return;
        const items = Array.from(tocList.querySelectorAll('li.toc-item, li.toc-group'));
        items.forEach((li) => {
            li.classList.add('toc-loading');
            li.classList.remove('toc-enter');
        });
        tocList.classList.remove('toc-list-loading');
        tocList.classList.add('toc-list-ready');
        items.forEach((li, index) => {
            const delay = Math.min(index * 14, 400);
            setTimeout(() => {
                li.classList.remove('toc-loading');
                li.classList.add('toc-enter');
            }, delay);
        });
        const totalTime = Math.min(items.length * 14, 400) + 360;
        setTimeout(() => {
            items.forEach((li) => li.classList.remove('toc-enter'));
        }, totalTime);
    }

    // ==================== 正文加载动画 ====================
    function playContentEntrance() {
        const contentArea = document.getElementById('contentArea');
        if (!contentArea) return;
        if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
        contentArea.classList.remove('content-entrance');
        void contentArea.offsetWidth;
        contentArea.classList.add('content-entrance');
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
        contentArea.querySelectorAll('pre').forEach((pre) => {
            if (pre.querySelector('.code-copy-btn')) return;
            pre.classList.add('has-copy-btn');
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'code-copy-btn';
            btn.setAttribute('aria-label', '复制代码');
            btn.setAttribute('title', '复制代码');
            btn.innerHTML = `
                <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="9" y="9" width="11" height="11" rx="1.5"></rect>
                    <path d="M5 15V5a1 1 0 0 1 1-1h10"></path>
                </svg>
                <span class="code-copy-text">复制</span>
            `;
            btn.addEventListener('click', function (e) {
                e.preventDefault();
                e.stopPropagation();
                let codeText = '';
                const codeEl = pre.querySelector('code');
                if (codeEl) {
                    const clone = codeEl.cloneNode(true);
                    clone.querySelectorAll('.code-copy-btn').forEach((b) => b.remove());
                    codeText = clone.textContent;
                } else {
                    const clone = pre.cloneNode(true);
                    clone.querySelectorAll('.code-copy-btn').forEach((b) => b.remove());
                    codeText = clone.textContent;
                }
                copyTextToClipboard(codeText).then((ok) => {
                    if (ok) {
                        btn.classList.add('copied');
                        const textSpan = btn.querySelector('.code-copy-text');
                        if (textSpan) textSpan.textContent = '已复制';
                        setTimeout(() => {
                            btn.classList.remove('copied');
                            if (textSpan) textSpan.textContent = '复制';
                        }, 1400);
                    } else {
                        const textSpan = btn.querySelector('.code-copy-text');
                        if (textSpan) textSpan.textContent = '复制失败';
                        setTimeout(() => {
                            if (textSpan) textSpan.textContent = '复制';
                        }, 1400);
                    }
                });
            });
            pre.insertBefore(btn, pre.firstChild);
        });
    }

    function copyTextToClipboard(text) {
        return new Promise((resolve) => {
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

    function injectFavicon() {
        if (document.querySelector('link[rel="icon"][data-injected]')) return;
        const iconHref = '../icon.ico';
        const linkIcon = document.createElement('link');
        linkIcon.rel = 'icon';
        linkIcon.type = 'image/x-icon';
        linkIcon.href = iconHref;
        linkIcon.setAttribute('data-injected', '1');
        document.head.appendChild(linkIcon);
        const linkShortcut = document.createElement('link');
        linkShortcut.rel = 'shortcut icon';
        linkShortcut.type = 'image/x-icon';
        linkShortcut.href = iconHref;
        linkShortcut.setAttribute('data-injected', '1');
        document.head.appendChild(linkShortcut);
        const linkApple = document.createElement('link');
        linkApple.rel = 'apple-touch-icon';
        linkApple.href = iconHref;
        linkApple.setAttribute('data-injected', '1');
        document.head.appendChild(linkApple);
    }

    global.renderLayout = renderLayout;

})(window);
