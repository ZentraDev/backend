import json
import logging
from dataclasses import asdict
from itertools import count
from typing import Dict

from starlette.websockets import WebSocketDisconnect
from websockets.exceptions import ConnectionClosedOK

from zentra import Connection, Message

log = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self._current_message_count: count = count(1)
        self._connection_counter: count = count(1)
        self.active_connections: Dict[int, Connection] = {}
        self.conversation_history: Dict[int, list[Message]] = {}

    @property
    def next_connection_id(self) -> int:
        return next(self._connection_counter)

    @property
    def next_message_id(self) -> int:
        return next(self._current_message_count)

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
        to_disconnect: list[Connection] = []
        for connection in self.active_connections.values():
            try:
                await connection.websocket.send_json(packet)
            except (WebSocketDisconnect, ConnectionClosedOK):
                to_disconnect.append(connection)

        for c in to_disconnect:
            self.disconnect(c)
            print(f"INFO:    {c.id} disconnected")
