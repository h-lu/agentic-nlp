# Week 01 starter_code

# solution.py - 参考解决方案
# 包含本章所有任务的参考代码

"""
Week 01 参考解决方案

包含：
1. 基础 API 调用
2. 文本分类
3. 文本摘要
4. 实体抽取
5. LLM Client 类
6. 成本估算

运行前请确保设置了 OPENAI_API_KEY 环境变量。
"""

import os
from typing import Optional
from openai import OpenAI, APIError, AuthenticationError, RateLimitError

# 初始化客户端
def get_client() -> OpenAI:
    """获取 OpenAI 客户端实例"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("请设置 OPENAI_API_KEY 环境变量")
    return OpenAI(api_key=api_key)


# 任务 1：基础 API 调用
def basic_call(prompt: str, system_prompt: str = "你是一个有帮助的助手。") -> str:
    """
    基础 LLM API 调用
    
    Args:
        prompt: 用户输入
        system_prompt: 系统提示
    
    Returns:
        LLM 的回复
    """
    client = get_client()
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    
    return response.choices[0].message.content


# 任务 2：文本分类
def classify_text(text: str, categories: list[str]) -> str:
    """
    对文本进行分类
    
    Args:
        text: 待分类的文本
        categories: 类别列表
    
    Returns:
        分类结果
    """
    prompt = f"""请将以下文本分类到其中一个类别中。

类别：{', '.join(categories)}

文本：
{text}

只输出类别名称，不要其他解释。"""

    return basic_call(prompt)


# 任务 3：文本摘要
def summarize_text(text: str, max_words: int = 50) -> str:
    """
    生成文本摘要
    
    Args:
        text: 原始文本
        max_words: 摘要最大字数
    
    Returns:
        摘要文本
    """
    prompt = f"""请为以下文本生成一个简洁的摘要，不超过{max_words}字。

文本：
{text}

摘要："""

    return basic_call(prompt)


# 任务 4：实体抽取
def extract_entities(text: str, entity_types: list[str]) -> dict:
    """
    从文本中抽取实体
    
    Args:
        text: 原始文本
        entity_types: 实体类型列表
    
    Returns:
        抽取结果字典
    """
    import json
    
    prompt = f"""请从以下文本中抽取指定的实体类型，以 JSON 格式返回。

实体类型：{', '.join(entity_types)}

文本：
{text}

返回格式示例：
{{"人名": [], "地名": [], "机构": []}}

只返回 JSON，不要其他内容。"""

    result = basic_call(prompt)
    
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        return {"error": "无法解析 JSON", "raw": result}


# 任务 5：LLM Client 类
class LLMClient:
    """统一的 LLM 客户端封装"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7
    ):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("请提供 API Key 或设置 OPENAI_API_KEY 环境变量")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        self.temperature = temperature
        self.total_tokens = 0
    
    def call(
        self,
        prompt: str,
        system_prompt: str = "你是一个有帮助的助手。",
        temperature: Optional[float] = None
    ) -> str:
        """通用调用方法"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature or self.temperature
            )
            
            self.total_tokens += response.usage.total_tokens
            return response.choices[0].message.content
            
        except AuthenticationError:
            raise ValueError("API Key 无效")
        except RateLimitError:
            raise RuntimeError("请求频率超限，请稍后重试")
        except APIError as e:
            raise RuntimeError(f"API 错误: {e}")
    
    def classify(self, text: str, categories: list[str]) -> str:
        """文本分类"""
        prompt = f"分类以下文本到 {categories} 中的一个，只输出类别名：\n\n{text}"
        return self.call(prompt, system_prompt="你是一个文本分类助手。", temperature=0)
    
    def summarize(self, text: str, max_words: int = 50) -> str:
        """文本摘要"""
        prompt = f"用不超过{max_words}字总结以下文本：\n\n{text}"
        return self.call(prompt, temperature=0.5)
    
    def extract(self, text: str, entity_types: list[str]) -> dict:
        """实体抽取"""
        import json
        prompt = f"从以下文本中抽取 {entity_types}，返回 JSON：\n\n{text}"
        result = self.call(prompt, temperature=0)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"raw": result}


# 任务 6：成本估算
def estimate_cost(
    text: str,
    model: str = "gpt-4o-mini",
    input_price: float = 0.15,
    output_price: float = 0.60
) -> dict:
    """
    估算处理文本的成本
    
    Args:
        text: 输入文本
        model: 模型名称
        input_price: 输入 Token 价格（$/M）
        output_price: 输出 Token 价格（$/M）
    
    Returns:
        成本估算结果
    """
    try:
        import tiktoken
        
        # 获取编码器
        try:
            enc = tiktoken.encoding_for_model(model)
        except KeyError:
            enc = tiktoken.get_encoding("cl100k_base")
        
        input_tokens = len(enc.encode(text))
        # 假设输出约为输入的 20%
        estimated_output_tokens = int(input_tokens * 0.2)
        
        cost_input = (input_tokens / 1_000_000) * input_price
        cost_output = (estimated_output_tokens / 1_000_000) * output_price
        
        return {
            "input_tokens": input_tokens,
            "estimated_output_tokens": estimated_output_tokens,
            "total_tokens": input_tokens + estimated_output_tokens,
            "cost_input": cost_input,
            "cost_output": cost_output,
            "total_cost": cost_input + cost_output
        }
        
    except ImportError:
        return {"error": "请安装 tiktoken: pip install tiktoken"}


# 使用示例
if __name__ == "__main__":
    # 测试基础调用
    print("=== 基础调用 ===")
    response = basic_call("什么是 LLM？用一句话回答。")
    print(f"回复: {response}")
    
    # 测试分类
    print("\n=== 文本分类 ===")
    text = "苹果公司发布新款 iPhone，股价应声上涨 3%。"
    category = classify_text(text, ["科技", "财经", "娱乐", "体育"])
    print(f"分类: {category}")
    
    # 测试摘要
    print("\n=== 文本摘要 ===")
    summary = summarize_text(text, max_words=30)
    print(f"摘要: {summary}")
    
    # 测试成本估算
    print("\n=== 成本估算 ===")
    cost = estimate_cost(text)
    print(f"Token 数: {cost.get('total_tokens', 'N/A')}")
    print(f"预估成本: ${cost.get('total_cost', 0):.6f}")
