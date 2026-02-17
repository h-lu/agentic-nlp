import React from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';
import styles from './index.module.css';

// =============================================================================
// 首页组件 - 可根据你的课程需求自定义
// =============================================================================

// SVG 图标组件
const BookIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
    <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
  </svg>
);

const CodeIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="16 18 22 12 16 6"/>
    <polyline points="8 6 2 12 8 18"/>
  </svg>
);

const GraduationIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M22 10v6M2 10l10-5 10 5-10 5z"/>
    <path d="M6 12v5c3 3 9 3 12 0v-5"/>
  </svg>
);

const LightbulbIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/>
    <path d="M9 18h6"/>
    <path d="M10 22h4"/>
  </svg>
);

const ArrowRightIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M5 12h14"/>
    <path d="m12 5 7 7-7 7"/>
  </svg>
);

// =============================================================================
// 课程特性配置 - 修改这里的配置以适应你的课程
// =============================================================================

// 特性数据 - 可配置为多个阶段或模块
const features = [
  {
    title: '基础篇',
    description: '掌握核心概念和基础知识，为后续学习打下坚实基础。',
    icon: BookIcon,
    weeks: 'Week 01-04',
  },
  {
    title: '进阶篇',
    description: '深入学习高级特性和技术，提升开发能力。',
    icon: CodeIcon,
    weeks: 'Week 05-08',
  },
  {
    title: '实战篇',
    description: '通过实际项目练习，掌握工程化开发流程。',
    icon: GraduationIcon,
    weeks: 'Week 09-12',
  },
  {
    title: '综合篇',
    description: '综合运用所学知识，完成课程综合项目。',
    icon: LightbulbIcon,
    weeks: 'Week 13-16',
  },
];

// 快速开始步骤 - 可自定义
const quickStartSteps = [
  {
    number: '01',
    title: '阅读课程大纲',
    description: '了解课程目标、评估方式和参考资料',
    link: '/docs/syllabus',
    linkText: '查看大纲',
  },
  {
    number: '02',
    title: '配置开发环境',
    description: '安装必要的开发工具和环境',
    link: '/docs/weeks/01',
    linkText: '开始配置',
  },
  {
    number: '03',
    title: '开始学习',
    description: '从第一周开始，逐步掌握课程内容',
    link: '/docs/weeks/01',
    linkText: '开始学习',
  },
];

// =============================================================================
// 子组件
// =============================================================================

// 特性卡片组件
function FeatureCard({ title, description, icon: Icon, weeks }: typeof features[0]) {
  return (
    <div className={clsx('card', styles.featureCard)}>
      <div className={styles.featureIcon}>
        <Icon />
      </div>
      <div className={styles.featureWeeks}>{weeks}</div>
      <Heading as="h3" className={styles.featureTitle}>
        {title}
      </Heading>
      <p className={styles.featureDescription}>{description}</p>
    </div>
  );
}

// 首页头部组件
function HomepageHeader() {
  const { siteConfig } = useDocusaurusContext();
  return (
    <header className={styles.heroBanner}>
      <div className="container">
        <Heading as="h1" className={styles.heroTitle}>
          {siteConfig.title}
        </Heading>
        <p className={styles.heroSubtitle}>{siteConfig.tagline}</p>
        <div className={styles.buttons}>
          <Link
            className={clsx('button', styles.buttonPrimary)}
            to="/docs/syllabus">
            开始学习
          </Link>
          <Link
            className={clsx('button', styles.buttonSecondary)}
            to="/docs/weeks/01">
            浏览课程
          </Link>
        </div>
      </div>
    </header>
  );
}

// 快速开始卡片组件
function QuickStartCard({
  number,
  title,
  description,
  link,
  linkText,
}: typeof quickStartSteps[0]) {
  return (
    <div className={clsx('card', styles.quickStartCard)}>
      <div className={styles.quickStartNumber}>{number}</div>
      <Heading as="h3">{title}</Heading>
      <p>{description}</p>
      <Link to={link} className={styles.quickStartLink}>
        {linkText}
        <ArrowRightIcon />
      </Link>
    </div>
  );
}

// =============================================================================
// 主页面组件
// =============================================================================

export default function Home(): JSX.Element {
  const { siteConfig } = useDocusaurusContext();
  return (
    <Layout
      title={`${siteConfig.title}`}
      description="课程网站 - 系统化学习路径">
      <HomepageHeader />
      <main className={styles.mainContent}>
        {/* 课程阶段 */}
        <section className={styles.featuresSection}>
          <div className="container">
            <Heading as="h2" className={styles.sectionTitle}>
              课程阶段
            </Heading>
            <div className={styles.featuresGrid}>
              {features.map((feature, idx) => (
                <FeatureCard key={idx} {...feature} />
              ))}
            </div>
          </div>
        </section>

        {/* 快速开始 */}
        <section className={styles.quickStartSection}>
          <div className="container">
            <Heading as="h2" className={styles.sectionTitle}>
              快速开始
            </Heading>
            <div className={styles.quickStartGrid}>
              {quickStartSteps.map((step, idx) => (
                <QuickStartCard key={idx} {...step} />
              ))}
            </div>
          </div>
        </section>
      </main>
    </Layout>
  );
}
