# Copyright (c) 2024 iiPython

# Modules
import json
from nightwatch.config import config_path

# Main module
class AdminModule:
    def __init__(self) -> None:
        self.banfile = config_path.parent / "bans.json"
        self.banned_users = json.loads(self.banfile.read_text()) if self.banfile.is_file() else {}

    def save(self) -> None:
        self.banfile.write_text(json.dumps(self.banned_users, indent = 4))

    def add_ban(self, ip: str, username: str) -> None:
        self.banned_users[ip] = username
        self.save()

    def unban(self, ip: str) -> None:
        del self.banned_users[ip]
        self.save()

admin_module = AdminModule()
