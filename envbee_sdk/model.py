# ------------------------------------
# Copyright (c) envbee
# Licensed under the MIT License.
# ------------------------------------


from dataclasses import dataclass
from enum import Enum


class VariableType(Enum):
    STRING = "STRING"
    NUMBER = "NUMBER"
    BOOLEAN = "BOOLEAN"
    JSON = "JSON"


@dataclass
class Variable:
    id: int
    type: VariableType
    name: str
    description: str | None


@dataclass
class VariableValue:
    id: int
    variable_id: int
    content: dict


@dataclass
class Metadata:
    limit: int
    offset: int
    total: int