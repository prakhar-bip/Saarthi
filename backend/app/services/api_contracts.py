import re
from typing import Any, Dict, Iterable, List, Set, Tuple


INTERNAL_ENTITY_KEYWORDS = {
    "token",
    "refreshtoken",
    "session",
    "audit",
    "log",
    "synclog",
    "setting",
    "config",
    "permission",
    "role",
    "userrole",
    "mapping",
    "relation",
    "association",
    "link",
}


CRUD_METHODS = ("GET_LIST", "POST", "GET_ITEM", "PUT", "DELETE")


def get_entity_name(entity: Any) -> str:
    if isinstance(entity, dict):
        return str(entity.get("entity_name") or entity.get("name") or "").strip()
    if isinstance(entity, str):
        return entity.strip()
    return ""


def split_identifier(value: str) -> List[str]:
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value)
    spaced = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", spaced)
    return [part.lower() for part in re.split(r"[^A-Za-z0-9]+", spaced) if part]


def normalize_identifier(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def pluralize_resource(words: Iterable[str]) -> str:
    parts = [word for word in words if word]
    if not parts:
        return "items"
    last = parts[-1]
    if last.endswith("y") and len(last) > 1 and last[-2] not in "aeiou":
        parts[-1] = f"{last[:-1]}ies"
    elif last.endswith(("s", "x", "z", "ch", "sh")):
        parts[-1] = f"{last}es"
    else:
        parts[-1] = f"{last}s"
    return "-".join(parts)


def resource_name_for_entity(entity_name: str) -> str:
    words = split_identifier(entity_name)
    return pluralize_resource(words)


def entity_resource_variants(entity_name: str) -> Set[str]:
    words = split_identifier(entity_name)
    singular = "-".join(words)
    plural = pluralize_resource(words)
    compact_singular = normalize_identifier(singular)
    compact_plural = normalize_identifier(plural)
    naive_plural = f"{compact_singular}s" if compact_singular else ""
    
    variants = {singular, plural, compact_singular, compact_plural, naive_plural}
    if words:
        last_word = words[-1]
        last_word_plural = pluralize_resource([last_word])
        variants.add(last_word)
        variants.add(last_word_plural)
        
    return {v for v in variants if v}


def is_internal_system_entity(entity_name: str) -> bool:
    name_clean = normalize_identifier(entity_name)
    return any(keyword in name_clean for keyword in INTERNAL_ENTITY_KEYWORDS)


def endpoint_resource_tokens(endpoint: Dict[str, Any]) -> Set[str]:
    tokens: Set[str] = set()
    raw_values = [
        endpoint.get("resource"),
        endpoint.get("path"),
        endpoint.get("url"),
        endpoint.get("route"),
        endpoint.get("route_path"),
    ]
    for raw in raw_values:
        if not raw:
            continue
        text = str(raw).strip().lower()
        if not text:
            continue
        tokens.add(text.strip("/"))
        for segment in text.strip("/").split("/"):
            if not segment or segment.startswith("{") or segment.startswith(":"):
                continue
            if segment in {"api", "v1", "v2", "auth"}:
                continue
            tokens.add(segment)
            tokens.add(normalize_identifier(segment))
    return tokens


def endpoint_matches_entity(endpoint: Dict[str, Any], entity_name: str) -> bool:
    if not isinstance(endpoint, dict):
        return False
    variants = entity_resource_variants(entity_name)
    tokens = endpoint_resource_tokens(endpoint)
    return bool(variants.intersection(tokens))


def endpoint_is_item_path(endpoint: Dict[str, Any]) -> bool:
    path = str(endpoint.get("path") or endpoint.get("route_path") or "").lower()
    return bool(re.search(r"(\{[^/]*id[^/]*\}|:[^/]*id\b|/id\b)", path))


def endpoint_crud_key(endpoint: Dict[str, Any]) -> str:
    method = str(endpoint.get("method") or endpoint.get("http_method") or "GET").upper()
    if method == "GET":
        return "GET_ITEM" if endpoint_is_item_path(endpoint) else "GET_LIST"
    return method


def field_type_for_api(raw_type: Any) -> str:
    type_text = str(raw_type or "string").lower()
    if any(token in type_text for token in ("int", "long")):
        return "integer"
    if any(token in type_text for token in ("float", "double", "decimal", "number")):
        return "number"
    if any(token in type_text for token in ("bool",)):
        return "boolean"
    if any(token in type_text for token in ("list", "array", "[]")):
        return "array"
    if any(token in type_text for token in ("dict", "object", "json", "map")):
        return "object"
    return "string"


def request_fields_for_entity(entity: Any) -> Dict[str, Dict[str, Any]]:
    fields: Dict[str, Dict[str, Any]] = {}
    if not isinstance(entity, dict):
        return {"name": {"type": "string", "required": True}}
    for field in entity.get("fields", []) or []:
        if not isinstance(field, dict):
            continue
        name = str(field.get("name") or "").strip()
        if not name or name.lower() in {"id", "_id", "created_at", "updated_at", "createdat", "updatedat"}:
            continue
        fields[name] = {
            "type": field_type_for_api(field.get("type") or field.get("field_type")),
            "required": bool(field.get("required", False)),
        }
    return fields or {"name": {"type": "string", "required": True}}


def build_crud_endpoint(entity: Any, crud_key: str, requires_auth: bool) -> Dict[str, Any]:
    entity_name = get_entity_name(entity) or "Item"
    resource = resource_name_for_entity(entity_name)
    collection_path = f"/api/v1/{resource}"
    item_path = f"{collection_path}/{{id}}"
    entity_key = normalize_identifier(entity_name) or "item"
    fields = request_fields_for_entity(entity)

    definitions: Dict[str, Tuple[str, str, Dict[str, Any], List[Dict[str, Any]], Dict[str, Any]]] = {
        "GET_LIST": (
            "GET",
            collection_path,
            {},
            [
                {"name": "limit", "type": "integer", "required": False, "default": 20},
                {"name": "offset", "type": "integer", "required": False, "default": 0},
            ],
            {"status": "success", resource.replace("-", "_"): "array"},
        ),
        "POST": (
            "POST",
            collection_path,
            fields,
            [],
            {"status": "success", entity_key: "object", "message": f"{entity_name} created successfully."},
        ),
        "GET_ITEM": (
            "GET",
            item_path,
            {},
            [],
            {"status": "success", entity_key: "object"},
        ),
        "PUT": (
            "PUT",
            item_path,
            fields,
            [],
            {"status": "success", entity_key: "object", "message": f"{entity_name} updated successfully."},
        ),
        "DELETE": (
            "DELETE",
            item_path,
            {},
            [],
            {"status": "success", "message": f"{entity_name} deleted successfully."},
        ),
    }
    method, path, request_body, query_parameters, response_payload = definitions[crud_key]
    return {
        "group_name": f"{entity_name} API",
        "path": path,
        "method": method,
        "description": f"{method} {path} for {entity_name} records.",
        "request_body": request_body,
        "query_parameters": query_parameters,
        "response_payload": response_payload,
        "requires_auth": requires_auth,
        "roles_allowed": [],
    }


def ensure_entity_crud_endpoints(
    api_architecture: Dict[str, Any],
    db_architecture: Dict[str, Any],
    requires_auth: bool,
) -> Dict[str, Any]:
    reconciled = dict(api_architecture or {})
    endpoints = list(reconciled.get("endpoints") or [])
    entities = db_architecture.get("entities", []) if isinstance(db_architecture, dict) else []

    for entity in entities:
        entity_name = get_entity_name(entity)
        if not entity_name or is_internal_system_entity(entity_name):
            continue

        existing_keys = {
            endpoint_crud_key(endpoint)
            for endpoint in endpoints
            if isinstance(endpoint, dict) and endpoint_matches_entity(endpoint, entity_name)
        }
        for crud_key in CRUD_METHODS:
            if crud_key not in existing_keys:
                endpoints.append(build_crud_endpoint(entity, crud_key, requires_auth))

    reconciled["endpoints"] = endpoints
    if not isinstance(reconciled.get("future_agent_context"), dict):
        reconciled["future_agent_context"] = {}
    notes = reconciled["future_agent_context"].setdefault("important_notes_for_backend_agents", [])
    if isinstance(notes, list):
        note = "API endpoints are deterministically reconciled against db_architecture.entities before validation."
        if note not in notes:
            notes.append(note)
    return reconciled
