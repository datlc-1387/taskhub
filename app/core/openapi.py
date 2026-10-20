from collections.abc import Callable
from typing import Any

from fastapi import FastAPI

from app.schemas.common import ErrorResponse

_ERROR_DESCRIPTIONS = {
    "401": "Missing, invalid or expired access token",
    "403": "Not enough permission or account locked",
    "404": "Resource not found or not visible to you",
    "422": "Invalid input",
}


def install_error_responses(app: FastAPI) -> None:
    generate: Callable[[], dict[str, Any]] = app.openapi

    def openapi() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema
        schema = generate()
        schema.setdefault("components", {}).setdefault("schemas", {})["ErrorResponse"] = (
            ErrorResponse.model_json_schema(ref_template="#/components/schemas/{model}")
        )
        error_content = {
            "application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}
        }
        for path_item in schema["paths"].values():
            for operation in path_item.values():
                params = operation.get("parameters", [])
                codes: list[str] = []
                if operation.get("security"):
                    codes += ["401", "403"]
                if any(p["in"] == "path" for p in params):
                    codes.append("404")
                if params or "requestBody" in operation:
                    codes.append("422")
                responses = operation.setdefault("responses", {})
                for code in codes:
                    responses[code] = {
                        "description": _ERROR_DESCRIPTIONS[code],
                        "content": error_content,
                    }
        return schema

    app.openapi = openapi  # type: ignore[method-assign]
