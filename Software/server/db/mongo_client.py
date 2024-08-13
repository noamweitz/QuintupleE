from pymongo import MongoClient
from models import *

class DBClient:

    def __init__(self):
        self.client = MongoClient(
            "mongodb+srv://smartgrid_user:OzVu9hnKiaJULToP@autodocs.kwrryjv.mongodb.net/?retryWrites=true&w=majority&appName=Autodocs"
        )
        db = self.client["smartgrid"]
        self.day_db = db["days"]
        self.tick_db = db["ticks"]

    def insert_day(self, day: Day):
        self.day_db.insert_one(day.model_dump())

    def insert_tick(self, tick: FullTick):
        self.tick_db.insert_one(tick.model_dump())
