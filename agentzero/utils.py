from enum import Enum


class ChatRoles(Enum):
    USR = "user"
    AI = "assistant"
    SYS = "system"


class Message:
    """
    OpenAI chat model compatible message class.
    """

    name: str | None
    role: ChatRoles
    content: str

    def __init__(self, name: str, role: ChatRoles, content: str):
        self.name = name
        self.role = role
        self.content = content

    def __dict__(self):
        if self.role == ChatRoles.SYS:
            return {
                "role": self.role.value,
                "content": self.content,
            }

        return {
            "name": self.name,
            "role": self.role.value,
            "content": self.content,
        }
