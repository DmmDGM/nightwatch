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
    """The name of this user."""
    hex: str
    """The hex color code of this user, without a leading hashtag."""
    admin: bool
    """Status of whether or not this user is an admin."""
    bot: bool
    """Status of whether or not this user is a bot."""

    def __repr__(self) -> str:
        return f"<User name='{self.name}' hex='{self.hex}' admin={self.admin} bot={self.bot}>"

@dataclass
class Message:
    user: User
    """The :User: object who sent this message."""
    message: str
    """The raw text content of this message."""
    time: int
    """The time this message was sent in seconds since the epoch."""

    def __repr__(self) -> str:
        return f"<Message user='{self.user}' message='{self.message}' time={self.time}>"

@dataclass
class RicsInfo:
    name: str
    """The name of the RICS server we are connected to."""
    users: list[User]
    """List of :User: objects that are connected to this server."""
    chat_logs: list[Message]
    """List of :Message: objects consisting of chat logs.
    This will be the last 25 messages sent if you just joined, otherwise it will build over time."""

    def __repr__(self) -> str:
        return f"<RicsInfo name='{self.name}' users=[...] chat_logs=[...]>"
