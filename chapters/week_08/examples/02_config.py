"""
示例 2: 配置管理

展示了如何使用 Pydantic 进行配置管理，实现配置与代码分离。
核心概念：
- SystemConfig.from_yaml: 从 YAML 文件加载配置
- 配置验证：利用 Pydantic 自动验证
"""

from pydantic import BaseModel, Field, field_validator
from typing import Dict, Optional, Any
import yaml
from pathlib import Path


class LLMConfig(BaseModel):
    """LLM 配置"""
    provider: str = Field(..., description="LLM 提供商: openai, zhipu, qwen")
    model: str = Field(..., description="模型名称")
    api_key: str = Field(..., description="API 密钥")
    base_url: Optional[str] = Field(None, description="自定义 API 地址")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="温度参数")
    max_tokens: int = Field(2000, ge=1, le=128000, description="最大 token 数")

    @field_validator('provider')
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """验证提供商是否支持"""
        valid_providers = {'openai', 'zhipu', 'qwen', 'deepseek'}
        if v.lower() not in valid_providers:
            raise ValueError(f"Invalid provider: {v}. Must be one of {valid_providers}")
        return v.lower()


class AgentConfig(BaseModel):
    """Agent 配置"""
    name: str
    llm: LLMConfig
    system_prompt: str
    enable_cache: bool = True
    timeout_seconds: int = Field(30, ge=1, le=300)


class RetrieverConfig(BaseModel):
    """检索器配置"""
    type: str = "vector"
    top_k: int = Field(5, ge=1, le=100)
    score_threshold: float = Field(0.7, ge=0.0, le=1.0)


class ObservabilityConfig(BaseModel):
    """可观测性配置"""
    enable_logging: bool = True
    enable_tracing: bool = True
    log_level: str = "INFO"
    tracing_endpoint: Optional[str] = None


class SystemConfig(BaseModel):
    """系统配置

    从 YAML 文件加载完整系统配置，支持多环境
    """
    agents: Dict[str, AgentConfig]
    retriever: RetrieverConfig
    observability: ObservabilityConfig

    @classmethod
    def from_yaml(cls, path: str) -> "SystemConfig":
        """从 YAML 文件加载配置

        Args:
            path: YAML 文件路径

        Returns:
            SystemConfig 实例

        Raises:
            FileNotFoundError: 文件不存在
            yaml.YAMLError: YAML 格式错误
            ValidationError: 配置验证失败
        """
        file_path = Path(path)

        if not file_path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        try:
            with open(file_path, encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {e}")

        # 使用 Pydantic 验证
        return cls.model_validate(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SystemConfig":
        """从字典创建配置（用于测试）"""
        return cls.model_validate(data)

    def to_yaml(self, path: str) -> None:
        """保存配置到 YAML 文件"""
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(self.model_dump(mode='json'), f, allow_unicode=True)


def create_sample_config(output_path: str = "config/development.yaml") -> None:
    """创建示例配置文件"""
    import os

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)

    config = SystemConfig.from_dict({
        "agents": {
            "planner": {
                "name": "planner",
                "llm": {
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "api_key": "sk-test-key",
                    "temperature": 0.7,
                    "max_tokens": 2000
                },
                "system_prompt": "You are a planning agent.",
                "enable_cache": True,
                "timeout_seconds": 30
            },
            "executor": {
                "name": "executor",
                "llm": {
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "api_key": "sk-test-key",
                    "temperature": 0.5,
                    "max_tokens": 2000
                },
                "system_prompt": "You are an executor agent.",
                "enable_cache": True,
                "timeout_seconds": 60
            },
            "retriever": {
                "name": "retriever",
                "llm": {
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "api_key": "sk-test-key",
                    "temperature": 0.3,
                    "max_tokens": 1000
                },
                "system_prompt": "You are a retriever agent.",
                "enable_cache": True,
                "timeout_seconds": 30
            },
            "reviewer": {
                "name": "reviewer",
                "llm": {
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "api_key": "sk-test-key",
                    "temperature": 0.2,
                    "max_tokens": 1000
                },
                "system_prompt": "You are a reviewer agent.",
                "enable_cache": False,
                "timeout_seconds": 30
            }
        },
        "retriever": {
            "type": "vector",
            "top_k": 5,
            "score_threshold": 0.7
        },
        "observability": {
            "enable_logging": True,
            "enable_tracing": True,
            "log_level": "INFO",
            "tracing_endpoint": "https://api.langsmith.com"
        }
    })

    config.to_yaml(output_path)
    return config


if __name__ == "__main__":
    # 创建示例配置
    config = create_sample_config()
    print("Config created successfully")
    print(f"Planner model: {config.agents['planner'].llm.model}")
    print(f"Retriever top_k: {config.retriever.top_k}")
