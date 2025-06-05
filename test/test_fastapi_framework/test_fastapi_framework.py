import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel
from typing import Callable, List, Optional, Literal


from src.controllers.frameworks import FastApiFramework


# --- Mock definitions for models/interfaces ---

class FastApiGetResponse(BaseModel):
    message: str

class FastApiPostResponse(BaseModel):
    message: str
    data: dict

# Simulate what ApiEndPointProtocolFunction could be (a simple callable)
ApiEndPointProtocolFunction = Callable[..., dict]

# Minimal version of EndpointSpec for testing
class EndpointSpec:
    def __init__(
        self,
        path: str,
        handler: ApiEndPointProtocolFunction,
        required_params: List[Literal["GET", "POST"]],
        response_model: Optional[BaseModel] = None,
    ):
        self.path = path
        self.handler = handler
        self.required_params = required_params
        self.response_model = response_model


# --- Dummy handlers ---

def dummy_get_handler():
    return {"message": "GET success"}

def dummy_post_handler(data: dict):
    return {"message": "POST success", "data": data}


# --- Fixtures ---

@pytest.fixture
def fastapi_framework():
    return FastApiFramework(app_type=FastAPI, title="My API", version="1.0.0")


# --- Tests ---

def test_init_success():
    framework = FastApiFramework(app_type=FastAPI, title="API", version="1.0.0")
    assert isinstance(framework._app, FastAPI)

def test_init_invalid_type():
    with pytest.raises(TypeError):
        FastApiFramework(app_type=dict)  # Not a FastAPI subclass


def test_add_route_success(fastapi_framework):
    fastapi_framework.add_route(
        path="/test",
        endpoint=dummy_get_handler,
        methods=["GET"],
        response_model=FastApiGetResponse
    )
    client = TestClient(fastapi_framework._app)
    response = client.get("/test")
    assert response.status_code == 200
    assert response.json() == {"message": "GET success"}


def test_add_route_missing_path(fastapi_framework):
    with pytest.raises(ValueError):
        fastapi_framework.add_route(
            path="",
            endpoint=dummy_get_handler,
            methods=["GET"]
        )


def test_add_route_invalid_method(fastapi_framework):
    with pytest.raises(ValueError):
        fastapi_framework.add_route(
            path="/bad-method",
            endpoint=dummy_get_handler,
            methods=["INVALID"]
        )


def test_add_route_invalid_status_code(fastapi_framework):
    with pytest.raises(ValueError):
        fastapi_framework.add_route(
            path="/status",
            endpoint=dummy_get_handler,
            methods=["GET"],
            status_code=9999
        )


def test_run_application_invalid_host(fastapi_framework):
    with pytest.raises(ValueError):
        fastapi_framework.run_application(host=None)


def test_run_application_invalid_port(fastapi_framework):
    with pytest.raises(ValueError):
        fastapi_framework.run_application(port=99999)


def test_run_application_import_error(monkeypatch, fastapi_framework):
    monkeypatch.setitem(__import__("sys").modules, "uvicorn", None)
    with pytest.raises(ImportError):
        fastapi_framework.run_application()


def test_from_constructor():
    spec = EndpointSpec(
        path="/constructor",
        handler=dummy_get_handler,
        required_params=["GET"],
        response_model=FastApiGetResponse
    )

    framework = FastApiFramework.from_constructor(
        app_type=FastAPI,
        title="Constructor API",
        version="2.0",
        api_spec=(spec,)
    )

    client = TestClient(framework._app)
    response = client.get("/constructor")
    assert response.status_code == 200
    assert response.json()["message"] == "GET success"
