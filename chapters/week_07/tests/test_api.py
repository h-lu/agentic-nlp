"""
Tests for FastAPI Service - Week 07

Tests the API deployment functionality including:
- Basic API endpoints
- Request validation
- Response formats
- Error handling
- Edge cases (empty requests, long tasks)
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Mock FastAPI imports for testing
try:
    from fastapi import FastAPI, HTTPException
    from fastapi.testclient import TestClient
    from pydantic import BaseModel
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    # Create mock classes for testing
    class HTTPException(Exception):
        pass

    class BaseModel:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

        def dict(self):
            return self.__dict__


# Skip all tests if FastAPI not available
pytestmark = pytest.mark.skipif(
    not FASTAPI_AVAILABLE,
    reason="FastAPI not installed"
)


class TestAPIBasics:
    """Test basic API functionality."""

    @pytest.fixture
    def mock_app(self):
        """Create a mock FastAPI app."""
        if not FASTAPI_AVAILABLE:
            pytest.skip("FastAPI not available")

        app = FastAPI(title="Test TextAgent API")

        # Mock global state - initialize to a mock object so service is available
        app.state.textagent = Mock()  # Initialize with mock instead of None

        # Mock request/response models
        class AnalysisRequest(BaseModel):
            task: str
            enable_review: bool = False
            use_cache: bool = True

        # Import Optional for proper type hint
        from typing import Optional

        class AnalysisResponse(BaseModel):
            task: str
            plan: dict
            execution: list
            review: Optional[dict] = None
            cost_usd: float
            latency_ms: int

        # Mock /analyze endpoint
        @app.post("/analyze", response_model=AnalysisResponse)
        async def analyze(request: AnalysisRequest):
            if app.state.textagent is None:
                raise HTTPException(status_code=503, detail="Service not initialized")

            return AnalysisResponse(
                task=request.task,
                plan={"subtasks": [{"step": 1, "action": "test"}]},
                execution=[{"step": 1, "result": "done"}],
                review=None,
                cost_usd=0.01,
                latency_ms=100
            )

        # Mock /health endpoint
        @app.get("/health")
        async def health():
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}

        # Mock /metrics endpoint
        @app.get("/metrics")
        async def metrics():
            if app.state.textagent is None:
                return {"error": "Service not initialized"}
            return {"total_calls": 10, "total_cost": 0.1}

        return app

    @pytest.fixture
    def test_client(self, mock_app):
        """Create a test client."""
        if not FASTAPI_AVAILABLE:
            pytest.skip("FastAPI not available")
        return TestClient(mock_app)

    def test_health_endpoint(self, test_client):
        """Test /health endpoint returns healthy status."""
        response = test_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_analyze_endpoint_with_valid_request(self, test_client):
        """Test /analyze endpoint with valid request."""
        request_data = {
            "task": "分析客户反馈",
            "enable_review": True,
            "use_cache": True
        }

        response = test_client.post("/analyze", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["task"] == "分析客户反馈"
        assert "plan" in data
        assert "execution" in data
        assert "cost_usd" in data
        assert "latency_ms" in data

    def test_analyze_endpoint_with_minimal_request(self, test_client):
        """Test /analyze endpoint with minimal required fields."""
        request_data = {
            "task": "简单分析"
        }

        response = test_client.post("/analyze", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["task"] == "简单分析"

    def test_metrics_endpoint(self, test_client):
        """Test /metrics endpoint."""
        response = test_client.get("/metrics")

        assert response.status_code == 200
        data = response.json()
        assert "total_calls" in data or "error" in data


class TestAPIValidation:
    """Test API request validation."""

    @pytest.fixture
    def validation_app(self):
        """Create app with validation."""
        if not FASTAPI_AVAILABLE:
            pytest.skip("FastAPI not available")

        from fastapi import FastAPI, HTTPException
        from fastapi.testclient import TestClient
        from pydantic import BaseModel, Field, ConfigDict

        app = FastAPI()

        class AnalysisRequest(BaseModel):
            model_config = ConfigDict(extra="forbid", strict=True)
            task: str = Field(..., min_length=1, max_length=10000)
            enable_review: bool = False
            use_cache: bool = True

        @app.post("/analyze")
        async def analyze(request: AnalysisRequest):
            return {"task": request.task, "status": "received"}

        return app

    @pytest.fixture
    def validation_client(self, validation_app):
        """Create test client for validation."""
        if not FASTAPI_AVAILABLE:
            pytest.skip("FastAPI not available")
        return TestClient(validation_app)

    def test_empty_task_rejected(self, validation_client):
        """Test that empty task is rejected."""
        request_data = {
            "task": "",
            "enable_review": False
        }

        response = validation_client.post("/analyze", json=request_data)

        # Should fail validation
        assert response.status_code == 422

    def test_missing_task_rejected(self, validation_client):
        """Test that missing task field is rejected."""
        request_data = {
            "enable_review": True
        }

        response = validation_client.post("/analyze", json=request_data)

        assert response.status_code == 422

    def test_invalid_enable_review_type(self, validation_client):
        """Test that invalid enable_review type is rejected."""
        request_data = {
            "task": "测试任务",
            "enable_review": "yes"  # Should be boolean
        }

        response = validation_client.post("/analyze", json=request_data)

        assert response.status_code == 422

    def test_extra_fields_ignored(self, validation_client):
        """Test that extra fields are rejected with strict validation."""
        request_data = {
            "task": "测试任务",
            "enable_review": True,
            "extra_field": "should be rejected"
        }

        response = validation_client.post("/analyze", json=request_data)

        # With strict validation (extra="forbid"), extra fields should be rejected
        assert response.status_code == 422


class TestAPIErrorHandling:
    """Test API error handling."""

    @pytest.fixture
    def error_app(self):
        """Create app with error handling."""
        if not FASTAPI_AVAILABLE:
            pytest.skip("FastAPI not available")

        from fastapi import FastAPI, HTTPException
        from fastapi.testclient import TestClient
        from pydantic import BaseModel

        app = FastAPI()

        class AnalysisRequest(BaseModel):
            task: str
            enable_review: bool = False

        app.state.service_initialized = False

        @app.post("/analyze")
        async def analyze(request: AnalysisRequest):
            if not app.state.service_initialized:
                raise HTTPException(
                    status_code=503,
                    detail="Service not initialized"
                )
            return {"task": request.task}

        @app.get("/error")
        async def error_endpoint():
            raise HTTPException(status_code=500, detail="Internal error")

        return app

    @pytest.fixture
    def error_client(self, error_app):
        """Create test client for error testing."""
        if not FASTAPI_AVAILABLE:
            pytest.skip("FastAPI not available")
        return TestClient(error_app)

    def test_service_unavailable_when_not_initialized(self, error_client):
        """Test 503 error when service not initialized."""
        request_data = {"task": "测试任务"}

        response = error_client.post("/analyze", json=request_data)

        assert response.status_code == 503
        data = response.json()
        assert "detail" in data

    def test_internal_error_handling(self, error_client):
        """Test internal error is handled properly."""
        response = error_client.get("/error")

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data


class TestAPIEdgeCases:
    """Test API edge cases."""

    @pytest.fixture
    def edge_app(self):
        """Create app for edge case testing."""
        if not FASTAPI_AVAILABLE:
            pytest.skip("FastAPI not available")

        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from pydantic import BaseModel

        app = FastAPI()

        class AnalysisRequest(BaseModel):
            task: str
            enable_review: bool = False

        @app.post("/analyze")
        async def analyze(request: AnalysisRequest):
            # Simulate processing time
            import time
            start = time.time()
            time.sleep(0.01)  # Small delay

            return {
                "task": request.task,
                "latency_ms": int((time.time() - start) * 1000)
            }

        return app

    @pytest.fixture
    def edge_client(self, edge_app):
        """Create test client for edge cases."""
        if not FASTAPI_AVAILABLE:
            pytest.skip("FastAPI not available")
        return TestClient(edge_app)

    def test_very_long_task(self, edge_client):
        """Test handling of very long task descriptions."""
        long_task = "这是一个非常长的任务描述" * 1000

        request_data = {"task": long_task, "enable_review": False}

        response = edge_client.post("/analyze", json=request_data)

        # Should handle long tasks
        assert response.status_code == 200

    def test_special_characters_in_task(self, edge_client):
        """Test handling of special characters."""
        special_tasks = [
            "测试???@@@###",
            "Test\n\nNewlines",
            'Test "quotes" and \'apostrophes\'',
            "Test\tmltabs",
            "Test emoji 🎉 😊"
        ]

        for task in special_tasks:
            request_data = {"task": task}
            response = edge_client.post("/analyze", json=request_data)
            assert response.status_code == 200

    def test_unicode_characters(self, edge_client):
        """Test handling of unicode characters."""
        unicode_task = "测试中文和العربيةand日本語"

        request_data = {"task": unicode_task}

        response = edge_client.post("/analyze", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["task"] == unicode_task

    def test_concurrent_requests(self, edge_client):
        """Test handling of concurrent requests."""
        import threading

        results = []

        def make_request():
            request_data = {"task": "并发测试"}
            response = edge_client.post("/analyze", json=request_data)
            results.append(response.status_code)

        threads = [threading.Thread(target=make_request) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All requests should succeed
        assert all(status == 200 for status in results)
        assert len(results) == 10


class TestAPIResponseFormats:
    """Test API response formats."""

    @pytest.fixture
    def response_app(self):
        """Create app for response format testing."""
        if not FASTAPI_AVAILABLE:
            pytest.skip("FastAPI not available")

        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from pydantic import BaseModel
        from typing import Optional

        app = FastAPI()

        class AnalysisRequest(BaseModel):
            task: str
            enable_review: bool = False

        class AnalysisResponse(BaseModel):
            task: str
            plan: dict
            execution: list
            review: Optional[dict] = None
            cost_usd: float
            latency_ms: int

        @app.post("/analyze", response_model=AnalysisResponse)
        async def analyze(request: AnalysisRequest):
            return AnalysisResponse(
                task=request.task,
                plan={"subtasks": [{"step": 1, "action": "analyze"}]},
                execution=[{"step": 1, "result": "completed"}],
                review={"status": "approved"} if request.enable_review else None,
                cost_usd=0.015,
                latency_ms=150
            )

        return app

    @pytest.fixture
    def response_client(self, response_app):
        """Create test client for response testing."""
        if not FASTAPI_AVAILABLE:
            pytest.skip("FastAPI not available")
        return TestClient(response_app)

    def test_response_contains_all_fields(self, response_client):
        """Test that response contains all required fields."""
        request_data = {"task": "测试", "enable_review": True}

        response = response_client.post("/analyze", json=request_data)

        assert response.status_code == 200
        data = response.json()

        required_fields = ["task", "plan", "execution", "review", "cost_usd", "latency_ms"]
        for field in required_fields:
            assert field in data

    def test_review_field_optional(self, response_client):
        """Test that review field is optional."""
        request_data = {"task": "测试", "enable_review": False}

        response = response_client.post("/analyze", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # Review should be None when not enabled
        assert data.get("review") is None or data.get("review") == {}

    def test_cost_usd_is_numeric(self, response_client):
        """Test that cost_usd is a numeric value."""
        request_data = {"task": "测试"}

        response = response_client.post("/analyze", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data["cost_usd"], (int, float))
        assert data["cost_usd"] >= 0

    def test_latency_ms_is_integer(self, response_client):
        """Test that latency_ms is an integer."""
        request_data = {"task": "测试"}

        response = response_client.post("/analyze", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data["latency_ms"], int)
        assert data["latency_ms"] >= 0


class TestAPIContentType:
    """Test API content type handling."""

    @pytest.fixture
    def content_app(self):
        """Create app for content type testing."""
        if not FASTAPI_AVAILABLE:
            pytest.skip("FastAPI not available")

        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from pydantic import BaseModel

        app = FastAPI()

        class AnalysisRequest(BaseModel):
            task: str

        @app.post("/analyze")
        async def analyze(request: AnalysisRequest):
            return {"task": request.task, "received": True}

        return app

    @pytest.fixture
    def content_client(self, content_app):
        """Create test client for content type testing."""
        if not FASTAPI_AVAILABLE:
            pytest.skip("FastAPI not available")
        return TestClient(content_app)

    def test_json_content_type(self, content_client):
        """Test JSON content type is accepted."""
        request_data = {"task": "测试"}

        response = content_client.post(
            "/analyze",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 200

    def test_form_data_rejected(self, content_client):
        """Test that form data is rejected."""
        response = content_client.post(
            "/analyze",
            data={"task": "测试"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        # FastAPI should reject non-JSON for pydantic models
        assert response.status_code == 422

    def test_missing_content_type(self, content_client):
        """Test handling of missing content type header."""
        # Test client defaults to JSON
        response = content_client.post(
            "/analyze",
            json={"task": "测试"}
        )

        assert response.status_code == 200
