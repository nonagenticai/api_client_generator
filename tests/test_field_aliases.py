"""Renamed fields/parameters must keep their wire names.

Regression: sanitize_field_name renames reserved names (``id`` -> ``id_``,
``type`` -> ``type_``) and camelCase (``createdAt`` -> ``created_at``). Without
an alias the generated models rejected real payloads carrying ``"id"`` and the
client sent ``id_`` on the wire.
"""

import importlib
import sys
from pathlib import Path
from typing import Any, Iterator

import pytest
from pydantic import ValidationError

from apigen.core.code_gen import PydanticClientGenerator
from apigen.parsers.openapi.parser import OpenAPIParser
from apigen.utils.naming import sanitize_field_name

# Whatever the sanitizer makes of camelCase, the wire name must survive as alias.
CREATED = sanitize_field_name("createdAt")
PAGE = sanitize_field_name("pageSize")

SPEC = {
    "openapi": "3.0.3",
    "info": {"title": "Alias Probe", "version": "1.0.0"},
    "paths": {
        "/items/{id}": {
            "get": {
                "operationId": "getItem",
                "parameters": [
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "string"}},
                    {"name": "pageSize", "in": "query", "schema": {"type": "integer"}},
                    {"name": "X-Request-Id", "in": "header", "schema": {"type": "string"}},
                ],
                "responses": {
                    "200": {
                        "description": "ok",
                        "content": {
                            "application/json": {"schema": {"$ref": "#/components/schemas/Item"}}
                        },
                    }
                },
            }
        }
    },
    "components": {
        "schemas": {
            "Item": {
                "type": "object",
                "required": ["id", "type"],
                "properties": {
                    "id": {"type": "string"},
                    "type": {"type": "string"},
                    "createdAt": {"type": "string"},
                    "name": {"type": "string"},
                },
            }
        }
    },
}


@pytest.fixture(scope="module")
def generated(tmp_path_factory: pytest.TempPathFactory) -> Iterator[tuple[Path, Any]]:
    out = tmp_path_factory.mktemp("gen")
    spec = OpenAPIParser().parse(SPEC, service_name="alias_probe")
    PydanticClientGenerator(out).generate(spec, format_code=False, generate_tests=False)
    sys.path.insert(0, str(out))
    try:
        yield out / "alias_probe", importlib.import_module("alias_probe.models")
    finally:
        sys.path.remove(str(out))
        for mod in [m for m in sys.modules if m.startswith("alias_probe")]:
            del sys.modules[mod]


def test_ir_keeps_wire_names() -> None:
    spec = OpenAPIParser().parse(SPEC, service_name="alias_probe")
    item = next(m for m in spec.models if m.name == "Item")
    aliases = {f.name: f.alias for f in item.fields}
    assert aliases == {"id_": "id", "type_": "type", CREATED: "createdAt", "name": None}
    params = {p.name: p.key for p in spec.endpoints[0].parameters}
    assert params == {"id_": "id", PAGE: "pageSize", "x_request_id": "X-Request-Id"}


def test_model_round_trips_id(generated: tuple[Path, Any]) -> None:
    _, models = generated
    payload = {"id": "abc", "type": "doc", "createdAt": "2026-10-21", "name": "n"}
    item = models.Item.model_validate(payload)
    assert item.id_ == "abc"
    assert item.type_ == "doc"
    assert getattr(item, CREATED) == "2026-10-21"
    assert item.model_dump(by_alias=True) == payload
    # populate_by_name keeps construction by Python name working.
    assert models.Item(id_="abc", type_="doc").model_dump(by_alias=True)["id"] == "abc"


def test_model_rejects_missing_wire_id(generated: tuple[Path, Any]) -> None:
    _, models = generated
    with pytest.raises(ValidationError):
        models.Item.model_validate({"type": "doc"})


def test_client_uses_wire_names(generated: tuple[Path, Any]) -> None:
    client_dir, _ = generated
    src = (client_dir / "client.py").read_text()
    assert 'path.replace("{" + \'id\' + "}", str(id_))' in src
    assert f"params['pageSize'] = {PAGE}" in src
    assert "headers['X-Request-Id'] = x_request_id" in src
    assert "params['id_']" not in src and "'{id_}'" not in src
