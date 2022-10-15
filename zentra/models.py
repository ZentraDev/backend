from typing import Literal

from pydantic import Field, BaseModel


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
    content: str = Field(description="The message content.")
    conversation_id: int = Field(
        description="The conversation this message is meant to be in."
    )
    sender_name: str = Field(
        description="The name of the person who sent this message."
    )
    sender_connection_id: int = Field(
        description="The connection id for the person who sent this message."
    )


class WSMessageSend(BaseModel):
    type: Literal["NEW_MESSAGE"]
    data: WSMessageSendData
