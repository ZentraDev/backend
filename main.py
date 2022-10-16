import asyncio
import json
import secrets

from fastapi import FastAPI, Path, Header, HTTPException
from starlette.requests import Request
from starlette.responses import Response
from starlette.staticfiles import StaticFiles
from starlette.status import HTTP_204_NO_CONTENT
from starlette.templating import Jinja2Templates
from starlette.websockets import WebSocketDisconnect, WebSocket
from websockets.exceptions import ConnectionClosedOK

from zentra import (
    ConnectionManager,
    Message,
    Connection,
    DataT,
    Detail,
    MessageSend,
    WSHello,
    WSPing,
    WSMessageSend,
    ConversationIDs,
    ConversationMessages,
    ConversationMessage,
)

app = FastAPI(
    title="Zentra Backend",
    description="Messages are sorted in order based on ID, "
    "that is a message with an ID of 5 is newer then a message with an ID of 4.\n\n"
    "Message ID's are generated globally and not per conversation.",
)
templates = Jinja2Templates(directory="templates")
# app.mount("/static", StaticFiles(directory="static"), name="static")
manager = ConnectionManager()


@app.get("/", include_in_schema=False)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get(
    "/conversations/ids",
    response_model=ConversationIDs,
    tags=["API"],
    description="Fetch an array of all current conversation id's.",
)
async def fetch_conversation_ids():
    return {"data": list(manager.conversation_history.keys())}


@app.get(
    "/conversations/{conversation_id}/messages",
    response_model=ConversationMessages,
    responses={404: {"model": Detail}},
    description="Fetch all messages for a given conversation.",
    tags=["API"],
)
async def fetch_messages(
    conversation_id: int = Path(
        description="The ID of the conversation you wish to receive messages for."
    ),
):
    conversations = manager.conversation_history.get(conversation_id)
    if not conversations:
        raise HTTPException(status_code=404, detail="Conversation does not exist.")

    return {"data": conversations}


@app.get(
    "/conversations/all/messages/latest",
    response_model=ConversationMessages,
    description="Fetch the most recent message for all conversations.",
    tags=["API"],
)
async def fetch_all_latest_messages():
    data = []
    for conversation in manager.conversation_history.values():
        msg = conversation[-1]
        data.append(msg)

    return {"data": data}


@app.get(
    "/conversations/{conversation_id}/messages/latest",
    response_model=ConversationMessage,
    responses={404: {"model": Detail}},
    description="Fetch the most recent message for a given conversation.",
    tags=["API"],
)
async def fetch_latest_message(
    conversation_id: int = Path(
        description="The ID of the conversation you wish to receive a message for."
    ),
):
    conversations = manager.conversation_history.get(conversation_id)
    if not conversations:
        raise HTTPException(status_code=404, detail="Conversation does not exist.")

    return {"data": conversations[-1]}


@app.post(
    "/conversations/{conversation_id}/messages",
    status_code=HTTP_204_NO_CONTENT,
    responses={401: {"model": Detail}},
    description="Send a new message out to all connected clients.\n\n"
    "It is up to the connected clients to decide if they wish to display it.",
    tags=["API"],
)
async def send_message(
    data: MessageSend,
    conversation_id: int = Path(
        description="The ID of the conversation you wish to send this message to."
    ),
    x_connection_id: int = Header(
        default=None, description="Your websocket connections id."
    ),
    x_nonce: str = Header(
        default=None, description="Your websocket connections nonce."
    ),
):
    connection: Connection | None = manager.active_connections.get(x_connection_id)
    if not connection or (connection and connection.nonce != x_nonce):
        raise HTTPException(status_code=401, detail="Invalid header credentials.")

    message: Message = Message(
        id=manager.next_message_id,
        content=data.content,
        sender_name=connection.name,
        sender_id=connection.id,
        conversation_id=conversation_id,
    )
    await manager.send_message_in_conversation(message)

    return Response(status_code=HTTP_204_NO_CONTENT)


@app.get(
    "/ws/{name}",
    name="Entrypoint",
    description="Establish a websocket connection to this URL before responding to the hello event detailed below.",
    status_code=101,
    tags=["Websocket"],
)
async def websocket_documentation(
    name: str = Path(description="The name you wish to use when talking to others."),
):
    return Response(status_code=HTTP_204_NO_CONTENT)


@app.get(
    "/ws/events/hello",
    name="Hello event",
    description="This event is received when you open an initial websocket connection. It requires no response.\n\n"
    "Clients should store the connection id and nonce for later API requests.",
    tags=["Websocket"],
    response_model=WSHello,
)
async def websocket_hello():
    return Response(status_code=HTTP_204_NO_CONTENT)


@app.get(
    "/ws/events/ping",
    name="ping event",
    description="Whenever this event is sent, it is expected the client responds. "
    "The response should be in the same format as provided, however, the `type` field "
    "should instead be set to `PONG`\n\nFailure to respond as expected currently does nothing, "
    "however it may prompt a force disconnection in the future.",
    tags=["Websocket"],
    response_model=WSPing,
)
async def websocket_ping():
    return Response(status_code=HTTP_204_NO_CONTENT)


@app.get(
    "/ws/events/message",
    name="new message event",
    description="This is sent to all connected clients whenever a POST request is made to the send message route.\n\n"
    "Connected clients should determine client side if this requires displaying or discarding.",
    tags=["Websocket"],
    response_model=WSMessageSend,
)
async def websocket_message():
    return Response(status_code=HTTP_204_NO_CONTENT)


@app.websocket("/ws/{name}")
async def websocket_endpoint(websocket: WebSocket, name: str):
    try:
        conn_id = manager.next_connection_id
        nonce = secrets.token_hex(32)
        connection: Connection = Connection(
            id=conn_id,
            name=name,
            websocket=websocket,
            nonce=nonce,
        )
        manager.register(connection)

        await websocket.accept()
        await websocket.send_json(
            {
                "type": "HELLO",
                "data": {"connection_id": connection.id, "nonce": connection.nonce},
            }
        )

        try:
            current_ack = 0
            while True:
                await asyncio.sleep(30)
                await websocket.send_json(
                    {
                        "type": "PING",
                        "data": {"ack": current_ack},
                    }
                )
                data: str = await websocket.receive_text()
                data: DataT = json.loads(data)
                # TODO Do something with mis-responded pings?
                if data.get("type") != "PONG":
                    print(f"ERROR    {connection.id} sent type {data['type']}")
                    continue

                nested_data = data.get("data")
                if not nested_data:
                    print(
                        f"ERROR    {connection.id} failed to send the required data field"
                    )
                    continue

                sent_ack = nested_data.get("ack")
                if sent_ack != current_ack:
                    print(
                        f"ERROR    {connection.id} sent ack {sent_ack}, expected {current_ack}"
                    )
                    continue

                current_ack += 1

        except (WebSocketDisconnect, ConnectionClosedOK):
            manager.disconnect(connection)
            print(f"INFO:    {connection.id} disconnected")
    except Exception as e:
        raise e
