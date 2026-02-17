import ExecutionEnvironment from '@docusaurus/ExecutionEnvironment';

// Mermaid 客户端渲染模块
// 使用 mermaid v10+ 的 mermaid.run() API

export function onInitialRouteRender() {
  if (!ExecutionEnvironment.canUseDOM) return;

  // 动态加载 mermaid
  import('mermaid').then((mermaid) => {
    mermaid.default.initialize({
      startOnLoad: false,
      theme: 'default',
      securityLevel: 'loose',
      flowchart: {
        useMaxWidth: true,
        htmlLabels: true,
      },
    });

    console.log('[Mermaid] Initialized');

    // 先处理代码块，清理 HTML 实体
    processMermaidBlocks();

    // 然后运行 mermaid
    setTimeout(() => {
      mermaid.default.run({
        querySelector: '.mermaid-code',
        postRenderCallback: function(id) {
          console.log('[Mermaid] Rendered:', id);
        }
      });
    }, 300);
  }).catch(err => {
    console.error('[Mermaid] Failed to load:', err);
  });
}

export function onRouteDidUpdate() {
  if (!ExecutionEnvironment.canUseDOM) return;

  import('mermaid').then((mermaid) => {
    processMermaidBlocks();
    setTimeout(() => {
      mermaid.default.run({
        querySelector: '.mermaid-code',
      });
    }, 300);
  }).catch(err => {
    console.error('[Mermaid] Failed to load:', err);
  });
}

// 预处理 mermaid 代码块
function processMermaidBlocks() {
  const blocks = document.querySelectorAll('.language-mermaid');
  console.log('[Mermaid] Found blocks:', blocks.length);

  blocks.forEach((block, index) => {
    if (block.hasAttribute('data-mermaid-processed')) return;

    // 获取纯文本内容
    let code = block.textContent || '';

    // 解码 HTML 实体
    code = decodeHtmlEntities(code);

    // 创建新的 pre 元素供 mermaid 处理
    const pre = document.createElement('pre');
    pre.className = 'mermaid-code';
    pre.setAttribute('data-mermaid-processed', 'true');
    pre.textContent = code;

    // 找到容器并替换
    const container = block.closest('.codeBlockContainer_Ckt0') ||
                      block.closest('.codeBlockContent_biex') ||
                      block.closest('[class*="codeBlockContainer"]') ||
                      block.parentElement;

    if (container) {
      container.replaceWith(pre);
    } else {
      block.replaceWith(pre);
    }

    console.log(`[Mermaid] Processed block ${index}`);
  });
}

// 解码 HTML 实体
function decodeHtmlEntities(text) {
  const textarea = document.createElement('textarea');
  textarea.innerHTML = text;
  let decoded = textarea.value;

  // 额外处理常见的 HTML 实体
  decoded = decoded
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&amp;/g, '&')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&apos;/g, "'")
    .replace(/<br\s*\/?>/gi, '<br/>')  // 标准化 br 标签
    .replace(/\u00a0/g, ' ')  // 替换 non-breaking space
    .trim();

  return decoded;
}
