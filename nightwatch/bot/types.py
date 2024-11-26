# Copyright (c) 2024 iiPython

# Modules
import typing
from dataclasses import dataclass, fields, is_dataclass

# Typing
T = typing.TypeVar("T")

def from_dict(cls: typing.Type[T], data: dict) -> T:
    if not is_dataclass(cls):
        raise ValueError(f"{cls} is not a dataclass")

    field_types = {f.name: f.type for f in fields(cls)}
    instance_data = {}

    for key, value in data.items():
        if key in field_types:
            field_type = field_types[key]
            if is_dataclass(field_type) and isinstance(value, dict):
                instance_data[key] = from_dict(field_type, value)  # type: ignore

            else:
                instance_data[key] = value

    return cls(**instance_data)

@dataclass
class User:
    name: str
    hex: str
    admin: bool
    bot: bool

    def __repr__(self) -> str:
        return f"<User name='{self.name}' hex='{self.hex}' admin={self.admin} bot={self.bot}>"

@dataclass
class Message:
    user: User
    message: str
    time: int

    def __repr__(self) -> str:
        return f"<Message user='{self.user}' message='{self.message}' time={self.time}>"

@dataclass
class RicsInfo:
    name: str
    users: list[User]
    chat_logs: list[Message]

    def __repr__(self) -> str:
        return f"<RicsInfo name='{self.name}' users=[...] chat_logs=[...]>"
