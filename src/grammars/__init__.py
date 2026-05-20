from src.grammars.default import DefaultExpressionGrammar, StrictExpressionGrammar
from src.grammars.c import CGrammar
from src.grammars.regex import RegexGrammar


_CANONICAL_REGISTRY = {
    "default": DefaultExpressionGrammar(),
    "c": CGrammar(),
    "regex": RegexGrammar(),
}

_ALIASES = {
    "strict-v1": "default",
    "c-subset-v1": "c",
    "regex-v1": "regex",
}


def get_grammar(key: str):
    normalized = (key or "default").strip().lower()
    normalized = _ALIASES.get(normalized, normalized)
    if normalized not in _CANONICAL_REGISTRY:
        available = ", ".join(sorted(_CANONICAL_REGISTRY))
        raise ValueError(f"Unknown grammar '{key}'. Available: {available}")
    return _CANONICAL_REGISTRY[normalized]


def list_grammars() -> list[dict[str, str]]:
    return [
        {
            "key": plugin.key,
            "name": plugin.name,
            "description": plugin.description,
            "rules": plugin.info().rules,
        }
        for plugin in _CANONICAL_REGISTRY.values()
    ]
