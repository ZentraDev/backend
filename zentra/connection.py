from dataclasses import dataclass

from starlette.websockets import WebSocket


@dataclass
class Connection:
    id: int
    name: str
    nonce: str
    websocket: WebSocket
