from dataclasses import dataclass


@dataclass
class Metadata:
    limit: int
    offset: int
    total: int
