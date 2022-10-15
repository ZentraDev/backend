import json
import logging
from dataclasses import asdict
from typing import Dict

from zentra import Connection, Message

log = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self._current_message_count: int = 0
        self.active_connections: Dict[int, Connection] = {}
        self.conversation_history: Dict[int, list[Message]] = {}

    @property
    def next_connection_id(self) -> int:
        return len(self.active_connections.keys()) + 1

    @property
    def next_message_id(self) -> int:
        self._current_message_count += 1
        return self._current_message_count

    def register(self, connection: Connection):
        log.info("Registered a connection for %s", connection.name)
        self.active_connections[connection.id] = connection

    def disconnect(self, connection: Connection):
        log.info("Disconnected a connection for %s", connection.id)
        self.active_connections.pop(connection.id, None)

    async def send_message_in_conversation(self, message: Message) -> None:
        if message.conversation_id in self.conversation_history:
            self.conversation_history[message.conversation_id].append(message)
        else:
            self.conversation_history[message.conversation_id] = [message]

        packet = {"type": "NEW_MESSAGE", "data": asdict(message)}
        for connection in self.active_connections.values():
            await connection.websocket.send_json(packet)
