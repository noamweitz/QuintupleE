from pydantic import BaseModel


class Deferable(BaseModel):
    start: int
    end: int
    energy: float


class Day(BaseModel):
    day: int
    deferables: list[Deferable]


class Tick(BaseModel):
    day: int
    tick: int
    demand: float
    sun: int
    buy_price: int
    sell_price: int
