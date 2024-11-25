# Copyright (c) 2024 iiPython

from datetime import datetime

class User:
    def __init__(self, name: str, hex: str, admin: bool) -> None:
        self.name, self.hex, self.admin = name, hex, admin

    def __repr__(self) -> str:
        return f"<User name='{self.name}' hex='{self.hex}' admin={self.admin}>"

    @staticmethod
    def from_payload(payload: dict):
        return User(**payload)

class Message:
    def __init__(self, user: dict, message: str, time: int | datetime) -> None:
        self.user, self.text = User.from_payload(user), message
        self.time = time if isinstance(time, datetime) else datetime.fromtimestamp(time)

    def __repr__(self) -> str:
        return f"<Message user={self.user} text='{self.text}'>"

    @staticmethod
    def from_payload(payload: dict):
        return Message(**payload)

class Server:
    def __init__(self, address: str, name: str, users: list[User]) -> None:
        self.address, self.name, self.users = address, name, users

    def __repr__(self) -> str:
        return f"<Server address='{self.address}' name='{self.name}' users=[{','.join(str(u) for u in self.users)}]"
