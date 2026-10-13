"""One cited public row, plus the contract evidence object it produces."""

from dataclasses import dataclass
from uuid import UUID

from d1_contracts import EvidenceRow


@dataclass(frozen=True)
class CitedRow:
    source: str
    version: str
    subject_key: str
    text: str
    match_keys: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.source or not self.version:
            raise ValueError("source and version are required")

    def evidence(self, row_id: UUID) -> EvidenceRow:
        return EvidenceRow(
            id=row_id,
            source=self.source,
            version=self.version,
            subject_key=self.subject_key,
        )
