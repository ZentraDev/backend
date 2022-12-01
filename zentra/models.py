import datetime
from typing import Literal

from pydantic import Field, BaseModel

from zentra import Message


class Detail(BaseModel):
    detail: str = Field(description="Information on why this request failed.")


class MessageSend(BaseModel):
    content: str = Field(description="The message content you wish to send.")


class WSHelloData(BaseModel):
    nonce: str = Field(description="Your assigned connection nonce.")
    connection_id: int = Field(description="Your assigned connection id.")


class WSHello(BaseModel):
    type: Literal["HELLO"]
    data: WSHelloData


class WSPingData(BaseModel):
    ack: int = Field(description="The ack you are expected to reply with.")


class WSPing(BaseModel):
    type: Literal["PING"]
    data: WSPingData


class WSMessageSendData(BaseModel):
    id: int = Field(description="The ID of this message.")
    content: str = Field(description="The message content.")
    conversation_id: int = Field(
        description="The conversation this message is meant to be in."
    )
    sender_name: str = Field(
        description="The name of the person who sent this message."
    )
    sender_id: int = Field(
        description="The connection id for the person who sent this message."
    )


class WSMessageSend(BaseModel):
    type: Literal["NEW_MESSAGE"]
    data: WSMessageSendData


class ConversationIDs(BaseModel):
    data: list[int] = Field(description="A list of the current ids for conversations.")


class ConversationMessages(BaseModel):
    data: list[Message] = Field(
        description="A list of the current messages for this action."
    )


class ConversationMessage(BaseModel):
    data: Message = Field(description="The latest message for this conversation.")


class RateLimited(BaseModel):
    retry_after: float = Field(
        description="How many seconds before you can retry this route."
    )
    resets_at: datetime.datetime = Field(
        description="The exact datetime this ratelimit expires."
    )
