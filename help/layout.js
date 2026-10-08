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
            <div class="logo-area">
                <img src="../icon.png" alt="Itoc logo" class="logo-img">
                <h1>Itoc 帮助文档${pageTitle ? ' - ' + pageTitle : ''}</h1>
            </div>
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
            <h3>📖 目录</h3>
            <ul id="tocList">${lis}</ul>
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

            // 滚动到当前高亮项
            const activeItem = document.querySelector('#tocList li.active');
            if (activeItem) {
                activeItem.scrollIntoView({ block: 'center' });
            }
        } else {
            // 兜底：如果缺东西，至少把正文显示出来
            if (docContent) {
                docContent.style.display = 'block';
            }
        }
    }

    // 暴露到全局
    global.renderLayout = renderLayout;

})(window);