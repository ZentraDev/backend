from dataclasses import dataclass


@dataclass
class Message:
    id: int
    content: str
    sender_id: int
    sender_name: str
    conversation_id: int
