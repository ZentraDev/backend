from typing import TypedDict, Literal


class NestedDataT(TypedDict):
    ack: int


class DataT(TypedDict):
    data: NestedDataT
    type: Literal["PONG"]
