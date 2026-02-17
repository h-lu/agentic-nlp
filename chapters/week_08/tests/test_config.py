"""
测试配置管理

测试模块：
- SystemConfig
- LLMConfig
- AgentConfig
- 配置加载和验证
"""

import pytest
import tempfile
import os
from pathlib import Path
from typing import Dict

from config import (
    LLMConfig,
    AgentConfig,
    RetrieverConfig,
    ObservabilityConfig,
    SystemConfig,
    create_sample_config
)


class TestLLMConfig:
    """测试 LLM 配置"""

    def test_llm_config_creation(self):
        """测试创建 LLM 配置"""
        config = LLMConfig(
            provider="openai",
            model="gpt-4o-mini",
            api_key="sk-test",
            temperature=0.7,
            max_tokens=2000
        )

        assert config.provider == "openai"
        assert config.model == "gpt-4o-mini"
        assert config.temperature == 0.7
        assert config.max_tokens == 2000

    def test_llm_config_defaults(self):
        """测试 LLM 配置默认值"""
        config = LLMConfig(
            provider="openai",
            model="gpt-4o-mini",
            api_key="sk-test"
        )

        assert config.temperature == 0.7
        assert config.max_tokens == 2000
        assert config.base_url is None

    def test_llm_config_provider_validation(self):
        """测试提供商验证"""
        # 有效提供商
        for provider in ["openai", "zhipu", "qwen", "deepseek"]:
            config = LLMConfig(
                provider=provider,
                model="test-model",
                api_key="sk-test"
            )
            assert config.provider == provider

        # 无效提供商
        with pytest.raises(ValueError, match="Invalid provider"):
            LLMConfig(
                provider="invalid_provider",
                model="test-model",
                api_key="sk-test"
            )

    def test_llm_config_provider_case_insensitive(self):
        """测试提供商名称大小写不敏感"""
        config = LLMConfig(
            provider="OPENAI",
            model="test-model",
            api_key="sk-test"
        )

        assert config.provider == "openai"

    def test_llm_config_temperature_bounds(self):
        """测试温度参数边界"""
        # 有效范围
        LLMConfig(
            provider="openai",
            model="test",
            api_key="sk-test",
            temperature=0.0
        )
        LLMConfig(
            provider="openai",
            model="test",
            api_key="sk-test",
            temperature=1.0
        )
        LLMConfig(
            provider="openai",
            model="test",
            api_key="sk-test",
            temperature=2.0
        )

        # 超出范围
        with pytest.raises(ValueError):
            LLMConfig(
                provider="openai",
                model="test",
                api_key="sk-test",
                temperature=-0.1
            )

        with pytest.raises(ValueError):
            LLMConfig(
                provider="openai",
                model="test",
                api_key="sk-test",
                temperature=2.1
            )

    def test_llm_config_max_tokens_bounds(self):
        """测试 max_tokens 边界"""
        # 有效
        LLMConfig(
            provider="openai",
            model="test",
            api_key="sk-test",
            max_tokens=1
        )
        LLMConfig(
            provider="openai",
            model="test",
            api_key="sk-test",
            max_tokens=128000
        )

        # 无效
        with pytest.raises(ValueError):
            LLMConfig(
                provider="openai",
                model="test",
                api_key="sk-test",
                max_tokens=0
            )


class TestAgentConfig:
    """测试 Agent 配置"""

    def test_agent_config_creation(self):
        """测试创建 Agent 配置"""
        llm_config = LLMConfig(
            provider="openai",
            model="gpt-4o-mini",
            api_key="sk-test"
        )

        agent_config = AgentConfig(
            name="planner",
            llm=llm_config,
            system_prompt="You are a planner.",
            enable_cache=True,
            timeout_seconds=30
        )

        assert agent_config.name == "planner"
        assert agent_config.llm.provider == "openai"
        assert agent_config.system_prompt == "You are a planner."
        assert agent_config.enable_cache is True
        assert agent_config.timeout_seconds == 30

    def test_agent_config_defaults(self):
        """测试 Agent 配置默认值"""
        llm_config = LLMConfig(
            provider="openai",
            model="test",
            api_key="sk-test"
        )

        agent_config = AgentConfig(
            name="test",
            llm=llm_config,
            system_prompt="test"
        )

        assert agent_config.enable_cache is True
        assert agent_config.timeout_seconds == 30

    def test_agent_config_timeout_bounds(self):
        """测试超时边界"""
        llm_config = LLMConfig(
            provider="openai",
            model="test",
            api_key="sk-test"
        )

        # 有效
        AgentConfig(
            name="test",
            llm=llm_config,
            system_prompt="test",
            timeout_seconds=1
        )
        AgentConfig(
            name="test",
            llm=llm_config,
            system_prompt="test",
            timeout_seconds=300
        )

        # 无效
        with pytest.raises(ValueError):
            AgentConfig(
                name="test",
                llm=llm_config,
                system_prompt="test",
                timeout_seconds=0
            )


class TestRetrieverConfig:
    """测试检索器配置"""

    def test_retriever_config_creation(self):
        """测试创建检索器配置"""
        config = RetrieverConfig(
            type="vector",
            top_k=10,
            score_threshold=0.8
        )

        assert config.type == "vector"
        assert config.top_k == 10
        assert config.score_threshold == 0.8

    def test_retriever_config_defaults(self):
        """测试检索器配置默认值"""
        config = RetrieverConfig()

        assert config.type == "vector"
        assert config.top_k == 5
        assert config.score_threshold == 0.7


class TestObservabilityConfig:
    """测试可观测性配置"""

    def test_observability_config_creation(self):
        """测试创建可观测性配置"""
        config = ObservabilityConfig(
            enable_logging=True,
            enable_tracing=True,
            log_level="DEBUG",
            tracing_endpoint="https://api.example.com"
        )

        assert config.enable_logging is True
        assert config.enable_tracing is True
        assert config.log_level == "DEBUG"
        assert config.tracing_endpoint == "https://api.example.com"

    def test_observability_config_defaults(self):
        """测试可观测性配置默认值"""
        config = ObservabilityConfig()

        assert config.enable_logging is True
        assert config.enable_tracing is True
        assert config.log_level == "INFO"
        assert config.tracing_endpoint is None


class TestSystemConfig:
    """测试系统配置"""

    @pytest.fixture
    def valid_config_dict(self):
        """有效的配置字典"""
        return {
            "agents": {
                "planner": {
                    "name": "planner",
                    "llm": {
                        "provider": "openai",
                        "model": "gpt-4o-mini",
                        "api_key": "sk-test",
                        "temperature": 0.7
                    },
                    "system_prompt": "You are a planner."
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
                "log_level": "INFO"
            }
        }

    def test_system_config_from_dict(self, valid_config_dict):
        """测试从字典创建系统配置"""
        config = SystemConfig.from_dict(valid_config_dict)

        assert "planner" in config.agents
        assert config.agents["planner"].name == "planner"
        assert config.retriever.type == "vector"
        assert config.observability.enable_logging is True

    def test_system_config_from_yaml_file(self, valid_config_dict):
        """测试从 YAML 文件加载配置"""
        import yaml

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(valid_config_dict, f)
            temp_path = f.name

        try:
            config = SystemConfig.from_yaml(temp_path)

            assert "planner" in config.agents
            assert config.retriever.type == "vector"
        finally:
            os.unlink(temp_path)

    def test_system_config_missing_file(self):
        """测试加载不存在的配置文件"""
        with pytest.raises(FileNotFoundError):
            SystemConfig.from_yaml("/nonexistent/path/config.yaml")

    def test_system_config_invalid_yaml(self):
        """测试加载无效的 YAML"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [unclosed")
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Invalid YAML"):
                SystemConfig.from_yaml(temp_path)
        finally:
            os.unlink(temp_path)

    def test_system_config_invalid_provider(self, valid_config_dict):
        """测试无效的提供商"""
        valid_config_dict["agents"]["planner"]["llm"]["provider"] = "invalid"

        with pytest.raises(ValueError):
            SystemConfig.from_dict(valid_config_dict)

    def test_system_config_to_yaml(self, valid_config_dict):
        """测试保存配置到 YAML"""
        config = SystemConfig.from_dict(valid_config_dict)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name

        try:
            config.to_yaml(temp_path)

            # 读取并验证
            loaded = SystemConfig.from_yaml(temp_path)
            assert loaded.agents["planner"].name == "planner"
        finally:
            os.unlink(temp_path)


class TestCreateSampleConfig:
    """测试示例配置创建"""

    def test_create_sample_config_file(self):
        """测试创建示例配置文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yaml")

            config = create_sample_config(config_path)

            assert os.path.exists(config_path)

            # 验证配置内容
            assert "planner" in config.agents
            assert "executor" in config.agents
            assert "retriever" in config.agents
            assert "reviewer" in config.agents

    def test_create_sample_config_structure(self):
        """测试示例配置的结构"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yaml")
            config = create_sample_config(config_path)

            # 验证每个 Agent 的配置
            for agent_name in ["planner", "executor", "retriever", "reviewer"]:
                agent = config.agents[agent_name]
                assert agent.name == agent_name
                assert agent.llm.provider == "openai"
                assert agent.llm.model == "gpt-4o-mini"
                assert agent.system_prompt is not None

            # 验证检索器配置
            assert config.retriever.type == "vector"
            assert config.retriever.top_k == 5

            # 验证可观测性配置
            assert config.observability.enable_logging is True
            assert config.observability.enable_tracing is True


@pytest.mark.parametrize("provider,expected_valid", [
    ("openai", True),
    ("OPENAI", True),
    ("zhipu", True),
    ("qwen", True),
    ("deepseek", True),
    ("invalid", False),
    ("", False),
    ("OpenAI", True),  # 混合大小写
])
def test_provider_validation(provider, expected_valid):
    """参数化测试：提供商验证"""
    if expected_valid:
        config = LLMConfig(
            provider=provider,
            model="test",
            api_key="sk-test"
        )
        assert config.provider == provider.lower()
    else:
        with pytest.raises(ValueError):
            LLMConfig(
                provider=provider,
                model="test",
                api_key="sk-test"
            )


@pytest.mark.parametrize("temperature,should_fail", [
    (0.0, False),
    (0.5, False),
    (1.0, False),
    (2.0, False),
    (-0.1, True),
    (2.1, True),
    (-1.0, True),
    (3.0, True),
])
def test_temperature_validation(temperature, should_fail):
    """参数化测试：温度参数验证"""
    if should_fail:
        with pytest.raises(ValueError):
            LLMConfig(
                provider="openai",
                model="test",
                api_key="sk-test",
                temperature=temperature
            )
    else:
        config = LLMConfig(
            provider="openai",
            model="test",
            api_key="sk-test",
            temperature=temperature
        )
        assert config.temperature == temperature
