from dataclasses import dataclass, field
from typing import List, Optional
from .enums import PublicationBias

@dataclass
class JournalSpecification:
    name: str
    bias: PublicationBias
    filters: List[str] = field(default_factory=list) # e.g. "replication_only"

# Define Journals
journals: List[JournalSpecification] = [
    JournalSpecification(
        name="General Science",
        bias=PublicationBias.WEAK, 
        filters=[]
    ),
    JournalSpecification(
        name="Replication Reports",
        bias=PublicationBias.NONE,
        filters=["replication_only"]
    )
]

# Helper to find by name
def get_journal(name: str) -> Optional[JournalSpecification]:
    for j in journals:
        if j.name == name:
            return j
    return None
