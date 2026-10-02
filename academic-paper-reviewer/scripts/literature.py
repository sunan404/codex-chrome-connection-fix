"""Future retrieval contracts; deliberately no fabricated external results."""
from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class ExternalRecord:
    provider: str
    identifier: str
    url: str
    retrieved_at: str
    status: str
    text: str = ""
    metadata: dict = field(default_factory=dict)
    inspected_quotes: list[dict] = field(default_factory=list)


class LiteratureProvider(Protocol):
    def paper_search(self, query: str) -> list[ExternalRecord]: ...
    def paper_fetch(self, identifier: str) -> ExternalRecord: ...
    def citation_lookup(self, reference: str) -> list[ExternalRecord]: ...
    def related_papers(self, query: str) -> list[ExternalRecord]: ...


class UnavailableProvider:
    def _unavailable(self, value):
        raise NotImplementedError("External literature retrieval is not implemented in MVP; record NOT_VERIFIED.")

    paper_search = _unavailable
    paper_fetch = _unavailable
    citation_lookup = _unavailable
    related_papers = _unavailable
