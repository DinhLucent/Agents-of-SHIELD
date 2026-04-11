"""Lightweight schema validator for frozen control-plane contracts."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ContractValidationError(ValueError):
    """Raised when an artifact does not match its frozen contract."""


class ContractValidator:
    """Validate runtime artifacts against small JSON-based schemas."""

    def __init__(self, schema_dir: Path | None = None) -> None:
        base_dir = Path(__file__).resolve().parent
        self.schema_dir = schema_dir or (base_dir / "schemas")

    def validate(self, contract_name: str, payload: Any) -> None:
        schema = self._load_schema(contract_name)
        errors: list[str] = []
        self._validate_node(path="$", schema=schema, value=payload, errors=errors)
        if errors:
            raise ContractValidationError(
                f"{contract_name} contract validation failed: " + "; ".join(errors)
            )

    def _load_schema(self, contract_name: str) -> dict[str, Any]:
        schema_path = self.schema_dir / f"{contract_name}.schema.json"
        if not schema_path.exists():
            raise FileNotFoundError(f"Missing contract schema: {schema_path}")
        return json.loads(schema_path.read_text(encoding="utf-8"))

    def _validate_node(
        self,
        path: str,
        schema: dict[str, Any],
        value: Any,
        errors: list[str],
    ) -> None:
        expected_type = schema.get("type")
        if expected_type and not self._matches_type(expected_type, value):
            errors.append(f"{path} expected {expected_type}, got {type(value).__name__}")
            return

        if expected_type == "object":
            if not isinstance(value, dict):
                return
            for required_key in schema.get("required", []):
                if required_key not in value:
                    errors.append(f"{path}.{required_key} is required")

            properties = schema.get("properties", {})
            for key, property_schema in properties.items():
                if key in value:
                    self._validate_node(f"{path}.{key}", property_schema, value[key], errors)

            if "additionalPropertiesSchema" in schema:
                for key, extra_value in value.items():
                    if key not in properties:
                        self._validate_node(
                            f"{path}.{key}",
                            schema["additionalPropertiesSchema"],
                            extra_value,
                            errors,
                        )

        if expected_type == "array":
            if not isinstance(value, list):
                return
            item_schema = schema.get("items")
            if item_schema:
                for index, item in enumerate(value):
                    self._validate_node(f"{path}[{index}]", item_schema, item, errors)

    def _matches_type(self, expected_type: str | list[str], value: Any) -> bool:
        if isinstance(expected_type, list):
            return any(self._matches_type(candidate, value) for candidate in expected_type)

        type_map: dict[str, tuple[type[Any], ...]] = {
            "object": (dict,),
            "array": (list,),
            "string": (str,),
            "integer": (int,),
            "number": (int, float),
            "boolean": (bool,),
            "null": (type(None),),
        }
        allowed_types = type_map.get(expected_type)
        if not allowed_types:
            return True
        if expected_type == "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        if expected_type == "number":
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        return isinstance(value, allowed_types)
