"""
Pytest 配置和共享 fixtures
"""

import sys
from pathlib import Path

# 添加 examples 目录到 Python 路径
examples_dir = Path(__file__).parent.parent / "examples"
sys.path.insert(0, str(examples_dir))

# 为示例模块创建别名（去掉文件名开头的数字）
import importlib.util

def load_module(module_name, file_name):
    """动态加载示例模块"""
    module_path = examples_dir / file_name
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# 加载所有示例模块
load_module("architecture", "01_architecture.py")
load_module("config", "02_config.py")
load_module("business_value", "03_business_value.py")
load_module("ab_testing", "04_ab_testing.py")
load_module("canary_deployment", "05_canary_deployment.py")
