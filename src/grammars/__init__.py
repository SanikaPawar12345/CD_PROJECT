from src.grammars.default import DefaultExpressionGrammar, StrictExpressionGrammar


_REGISTRY = {
    "default": DefaultExpressionGrammar(),
    "strict-v1": StrictExpressionGrammar(),
}


def get_grammar(key: str):
    normalized = (key or "default").strip().lower()
    if normalized not in _REGISTRY:
        available = ", ".join(sorted(_REGISTRY))
        raise ValueError(f"Unknown grammar '{key}'. Available: {available}")
    return _REGISTRY[normalized]


def list_grammars() -> list[dict[str, str]]:
    return [
        {
            "key": plugin.key,
            "name": plugin.name,
            "description": plugin.description,
            "rules": plugin.info().rules,
        }
        for plugin in _REGISTRY.values()
    ]
