# Copyright (c) 2024 iiPython

# Modules
from typing import Annotated, Optional
from pydantic import BaseModel, StringConstraints

# Models
class IdentifyModel(BaseModel):
    name: Annotated[str, StringConstraints(min_length = 3, max_length = 32)]
    color: Annotated[str, StringConstraints(min_length = 6, max_length = 6)]

class MessageModel(BaseModel):
    text: Annotated[str, StringConstraints(min_length = 1, max_length = 300)]

class AdminModel(BaseModel):
    code: Optional[str] = None
    command: Optional[list[str]] = None
