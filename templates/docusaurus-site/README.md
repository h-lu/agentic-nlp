# Docusaurus 课程网站模板

基于 Docusaurus 3.x 的课程网站生成模板，支持自动构建和 Netlify 一键部署。

## 目录

- [特性](#特性)
- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [配置说明](#配置说明)
- [本地开发](#本地开发)
- [部署到 Netlify](#部署到-netlify)
- [复用到其他课程](#复用到其他课程)
- [自定义样式](#自定义样式)
- [故障排除](#故障排除)

---

## 特性

- 自动生成课程章节页面
- 支持多阶段课程结构
- 每周独立页面（讲义、作业、评分标准、代码、术语、锚点）
- Markdown + YAML 源文件
- 响应式设计 + 暗色模式
- 本地搜索
- Netlify 自动部署

---

## 快速开始

### 前置要求

| 工具 | 版本要求 |
|------|---------|
| Node.js | >= 18.0 |
| Python | >= 3.8 |
| npm | >= 8.0 |

### 安装依赖

```bash
cd templates/docusaurus-site
make install
```

### 本地开发

```bash
make dev
```

访问 http://localhost:3000 查看站点。

### 生产构建

```bash
make build
```

输出目录：`dist/`（项目根目录）

---

## 项目结构

```
templates/docusaurus-site/
├── Makefile                   # 便捷命令
├── scripts/
│   └── build_site.py          # 构建脚本（解析 chapters/ 生成 MDX）
└── site/                      # Docusaurus 站点
    ├── docusaurus.config.ts   # 站点配置 ⚙️
    ├── sidebars.ts            # 侧边栏（自动生成）
    ├── src/
    │   ├── pages/index.tsx    # 首页
    │   └── css/custom.css     # 自定义样式 🎨
    └── package.json           # 依赖

# 课程内容（项目根目录）
chapters/
├── TOC.md                     # 课程目录
├── SYLLABUS.md                # 教学大纲
├── GLOSSARY.md                # 术语表
└── week_XX/                   # 每周内容
    ├── CHAPTER.md             # 讲义
    ├── ASSIGNMENT.md          # 作业
    ├── RUBRIC.md              # 评分标准
    ├── ANCHORS.yml            # 锚点
    ├── TERMS.yml              # 术语
    ├── examples/              # 示例代码
    └── starter_code/          # 起始代码

shared/
├── glossary.yml               # 全局术语表
└── style_guide.md             # 风格指南
```

---

## 配置说明

### 站点配置 (`site/docusaurus.config.ts`)

```typescript
const config: Config = {
  // 基本信息
  title: '你的课程名称',
  tagline: '课程标语',
  url: 'https://your-course.netlify.app',  // Netlify 域名
  baseUrl: '/',

  // GitHub 信息
  organizationName: 'your-username',
  projectName: 'your-repo',

  // 导航栏
  navbar: {
    title: '课程名',
    items: [
      { to: '/docs/syllabus', label: '教学大纲', position: 'left' },
      { to: '/docs/weeks/01', label: '课程内容', position: 'left' },
      { href: 'https://github.com/...', label: 'GitHub', position: 'right' },
    ],
  },

  // 页脚
  footer: {
    links: [...],
    copyright: `Copyright © ${new Date().getFullYear()} 你的课程名`,
  },
};
```

### Makefile 配置

```makefile
# 内容目录（相对于 templates/docusaurus-site/）
CHAPTERS_DIR := ../../chapters
SHARED_DIR := ../../shared

# 输出目录
OUTPUT_DIR := ../../dist
```

---

## 本地开发

### Makefile 命令

| 命令 | 说明 |
|------|------|
| `make install` | 安装 npm 依赖 |
| `make dev` | 生成文档 + 启动开发服务器 |
| `make build` | 生成文档 + 构建生产版本 |
| `make clean` | 清理构建产物 |
| `make help` | 显示所有命令 |

### 手动执行

```bash
# 仅生成 MDX 文件
python scripts/build_site.py --chapters-dir ../../chapters --shared-dir ../../shared

# 启动 Docusaurus 开发服务器
cd site && npm start

# 构建
cd site && npm run build
```

---

## 部署到 Netlify

### 1. 复制配置文件

确保项目根目录有 `netlify.toml`：

```toml
# netlify.toml
[build]
  command = "pip install pyyaml && cd templates/docusaurus-site && make install build"
  publish = "dist"
  environment = { NODE_VERSION = "20" }

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

### 2. 连接 GitHub 仓库

1. 登录 [Netlify](https://app.netlify.com)
2. 点击 "Add new site" → "Import an existing project"
3. 选择 GitHub，授权并选择仓库
4. Netlify 会自动检测 `netlify.toml` 配置
5. 点击 "Deploy site"

### 3. 自定义域名（可选）

1. Site settings → Domain management → Add custom domain
2. 按提示配置 DNS
3. 启用 HTTPS

### 4. 自动部署

每次推送到 `main` 分支，Netlify 会自动：
1. 安装 Python 和 npm 依赖
2. 执行构建命令
3. 发布 `dist/` 目录

---

## 复用到其他课程

### 步骤 1：复制模板文件

```bash
# 复制到新项目根目录
cp -r templates/docusaurus-site/ /path/to/new-project/
cp netlify.toml /path/to/new-project/
```

### 步骤 2：创建内容目录

```bash
mkdir -p /path/to/new-project/chapters
mkdir -p /path/to/new-project/shared
```

### 步骤 3：修改配置

编辑 `templates/docusaurus-site/site/docusaurus.config.ts`：

| 配置项 | 修改为 |
|--------|--------|
| `title` | 新课程名称 |
| `tagline` | 新课程标语 |
| `url` | Netlify 分配的域名 |
| `organizationName` | GitHub 用户名 |
| `projectName` | GitHub 仓库名 |
| `navbar.items` | 新的导航链接 |
| `footer.links` | 新的页脚链接 |
| `copyright` | 新的版权信息 |

### 步骤 4：检查目录结构

```
your-new-course/
├── chapters/              # ✅ 必需
│   ├── TOC.md
│   ├── SYLLABUS.md
│   └── week_01/
│       ├── CHAPTER.md
│       └── ...
├── shared/                # ✅ 必需
│   └── glossary.yml
├── templates/             # ✅ 从本模板复制
│   └── docusaurus-site/
├── netlify.toml           # ✅ 从本模板复制
└── .gitignore             # 添加 dist/
```

### 步骤 5：验证

```bash
cd /path/to/new-project/templates/docusaurus-site
make install
make dev
# 访问 http://localhost:3000 验证
```

---

## 自定义样式

### 主题色

编辑 `site/src/css/custom.css`：

```css
:root {
  --ifm-color-primary: #3B82F6;        /* 主色 */
  --ifm-color-primary-dark: #2563EB;   /* 深色 */
  --ifm-color-primary-light: #60A5FA;  /* 浅色 */
}
```

### 字体

```css
:root {
  --ifm-font-family-base: 'Inter', -apple-system, sans-serif;
}
```

### 暗色模式

```css
[data-theme='dark'] {
  --ifm-color-primary: #60A5FA;
  --ifm-background-color: #0F172A;
}
```

### ⚠️ 注意事项

**不要在 `.navbar` 上使用 `backdrop-filter`**，会导致移动端侧边栏无法显示：

```css
/* ❌ 错误 - 会导致移动端菜单失效 */
.navbar {
  backdrop-filter: blur(12px);
}

/* ✅ 正确 */
.navbar {
  background-color: rgba(255, 255, 255, 0.95);
}
```

参考：[GitHub Issue #6996](https://github.com/facebook/docusaurus/issues/6996)

---

## 故障排除

### Node 版本问题

```bash
node --version  # 应 >= 18.0

# 使用 nvm 切换
nvm install 20
nvm use 20
```

### 依赖安装失败

```bash
cd site
rm -rf node_modules package-lock.json
npm install
```

### Python 模块缺失

```bash
pip install pyyaml
```

### 构建脚本错误

```bash
python scripts/build_site.py --chapters-dir ../../chapters --shared-dir ../../shared --verbose
```

### MDX 语法错误

MDX 中 `{...}` 会被解析为 JavaScript 表达式，需要转义：

```markdown
<!-- ❌ 错误 -->
使用 {id} 作为标识符

<!-- ✅ 正确 -->
使用 `{id}` 作为标识符
```

### 移动端侧边栏不显示

1. 检查 `.navbar` 是否有 `backdrop-filter` 属性
2. 检查 CSS 是否设置了干扰 `transform` 或 `position` 的样式
3. 清除浏览器缓存后重试

### Netlify 构建失败

1. 检查 `netlify.toml` 路径是否正确
2. 确保 `NODE_VERSION` 设置为 20
3. 查看 Netlify 构建日志定位错误

---

## 许可证

MIT
