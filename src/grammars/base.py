from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class GrammarInfo:
    key: str
    name: str
    description: str
    rules: list[str]


class GrammarPlugin(Protocol):
    key: str
    name: str
    description: str

    def tokenize(self, source: str):
        ...

    def parse_with_metrics(self, tokens):
        ...

    def info(self) -> GrammarInfo:
        ...
