"""
查询重写器（Query Rewriter）

使用 LLM 将用户的模糊查询改写为更清晰、更完整的查询。
"""

from typing import Optional
from openai import OpenAI


class QueryRewriter:
    """LLM 查询重写器"""

    def __init__(self, llm_client: Optional[OpenAI] = None):
        """
        Args:
            llm_client: OpenAI 客户端，如果不提供则自动创建
        """
        self.llm = llm_client or OpenAI()

    def rewrite(self, query: str) -> str:
        """
        改写查询

        将用户的模糊查询改写为更清晰、更完整的查询。

        Args:
            query: 用户的原始查询

        Returns:
            改写后的查询
        """
        # 智能判断：长查询不需要重写
        if len(query) >= 15:
            return query

        prompt = f"""你是企业内部知识库的查询优化助手。你的任务是把用户的模糊查询改写得更清晰、更完整，便于从知识库中检索相关文档。

改写原则：
1. 保留用户的原始意图
2. 补充缺失的关键信息（比如"报销"改为"费用报销申请流程和所需材料"）
3. 使用正式、完整的表达
4. 不要改变问题的核心含义
5. 改写后的查询应该是可以直接用于检索的自然语言查询

示例：
- "报销" → "费用报销申请流程和所需材料"
- "请假" → "员工年假申请流程和审批要求"
- "GPU" → "GPU计算资源申请流程和配置要求"
- "远程办公" → "员工远程办公申请流程和审批要求"
- "TB" → "TB级别存储空间申请流程和配额限制"

原始查询：{query}

改写后的查询（只返回改写后的文本，不要解释）："""

        response = self.llm.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        return response.choices[0].message.content.strip()

    def rewrite_with_expansion(self, query: str, num_variants: int = 3) -> list[str]:
        """
        查询扩展：生成多个改写版本

        生成多个不同角度的查询变体，用于更全面的检索。

        Args:
            query: 用户的原始查询
            num_variants: 生成的变体数量

        Returns:
            改写后的查询列表（包含原始查询）
        """
        prompt = f"""你是企业内部知识库的查询优化助手。你的任务是根据用户的原始查询，生成 {num_variants} 个不同的查询变体，以便从知识库中更全面地检索相关文档。

生成原则：
1. 每个变体应该从不同角度表达同一个问题
2. 使用不同的关键词和表达方式
3. 保持问题的核心含义不变
4. 变体之间应该有差异，不要只是简单的同义词替换
5. 每个变体应该是完整的查询语句

原始查询：{query}

生成 {num_variants} 个查询变体（每行一个）："""

        response = self.llm.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        content = response.choices[0].message.content.strip()
        variants = [line.strip() for line in content.split('\n') if line.strip()]

        # 清理可能的序号前缀
        cleaned_variants = []
        for v in variants:
            # 移除 "1. ", "2. " 等前缀
            v = v.lstrip('0123456789. ')
            if v:
                cleaned_variants.append(v)

        # 确保包含原始查询
        return [query] + cleaned_variants[:num_variants]
