import { themes as prismThemes } from 'prism-react-renderer';
import type { Config } from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';

// =============================================================================
// Docusaurus 配置文件
// 《LLM 时代的文本智能与商务应用》课程站点
// =============================================================================

const config: Config = {
  // 站点基本信息
  title: 'LLM 时代的文本智能与商务应用',
  tagline: '用工程化 + Agentic 工作流掌握 LLM 时代的文本应用开发',
  favicon: 'img/favicon.ico',

  // 站点 URL 配置（部署时根据实际情况修改）
  url: 'https://agentic-nlp.netlify.app',
  baseUrl: '/',

  // GitHub 配置
  organizationName: 'h-lu',
  projectName: 'agentic-nlp',

  // 错误处理配置
  onBrokenLinks: 'warn',
  onBrokenMarkdownLinks: 'warn',

  // 国际化配置
  i18n: {
    defaultLocale: 'zh-Hans',
    locales: ['zh-Hans'],
  },

  // 预设配置
  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          editUrl: 'https://github.com/h-lu/agentic-nlp/tree/main/templates/docusaurus-site/site/',
          showLastUpdateAuthor: false,
          showLastUpdateTime: false,
          breadcrumbs: true,
          remarkPlugins: [remarkMath],
          rehypePlugins: [rehypeKatex],
        },
        blog: false,
        theme: {
          customCss: ['./src/css/custom.css'],
        },
      } satisfies Preset.Options,
    ],
  ],

  // 主题配置
  themeConfig: {
    image: 'img/docusaurus-social-card.jpg',

    colorMode: {
      defaultMode: 'light',
      disableSwitch: false,
      respectPrefersColorScheme: true,
    },

    // 导航栏配置
    navbar: {
      title: 'LLM 时代的文本智能',
      logo: {
        alt: 'Course Logo',
        src: 'img/logo.svg',
      },
      items: [
        {
          to: '/docs/syllabus',
          label: '教学大纲',
          position: 'left',
        },
        {
          to: '/docs/weeks/01',
          label: '课程内容',
          position: 'left',
        },
        {
          to: '/docs/glossary',
          label: '术语表',
          position: 'left',
        },
        {
          href: 'https://github.com/h-lu/agentic-nlp',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },

    // 页脚配置 - 根据需要修改
    footer: {
      style: 'dark',
      links: [
        {
          title: '课程',
          items: [
            {
              label: '教学大纲',
              to: '/docs/syllabus',
            },
            {
              label: '第一周',
              to: '/docs/weeks/01',
            },
            {
              label: '术语表',
              to: '/docs/glossary',
            },
          ],
        },
        {
          title: '更多',
          items: [
            {
              label: 'GitHub',
              href: 'https://github.com/h-lu/agentic-nlp',
            },
          ],
        },
      ],
      copyright: `Copyright \u00a9 ${new Date().getFullYear()} LLM 时代的文本智能与商务应用. Built with Docusaurus.`,
    },

    // 代码高亮配置
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['java', 'python', 'bash', 'json', 'yaml'],
    },

    // 文档侧边栏配置
    docs: {
      sidebar: {
        hideable: true,
        autoCollapseCategories: true,
      },
    },

    // 目录配置
    tableOfContents: {
      minHeadingLevel: 2,
      maxHeadingLevel: 4,
    },
  } satisfies Preset.ThemeConfig,

  // 插件配置 - 本地搜索
  plugins: [
    [
      '@easyops-cn/docusaurus-search-local',
      {
        hashed: true,
        language: ['zh', 'en'],
        highlightSearchTermsOnTargetPage: true,
        searchResultLimits: 8,
        searchResultContextMaxLength: 50,
        indexDocs: true,
        indexBlog: false,
        indexPages: true,
        explicitSearchResultPath: true,
      },
    ],
  ],

  // 主题配置
  themes: [],

  customFields: {
    courseName: 'LLM 时代的文本智能与商务应用',
    courseVersion: '2026.1',
  },
};

export default config;
