import paho.mqtt.client as paho
import json
from pydantic import BaseModel
from random import random

# required to not recieve same msg as one sent
RCV = "rcv/"
SND = "snd/"

SUN_TOPIC = "sun"
EXT_GRID_TOPIC = "external-grid"
STORAGE_TOPIC = "storage"
LOAD_TOPICS = ["loadR","loadB","loadK","loadY"]

class SMPS(BaseModel):
	SMPS: str
	power_in: int
	power_out: int

class MClient():
    def __init__(self, smps_type, broker_addr="localhost", broker_port=9001, keepalive=120):
        self.client = paho.Client(paho.CallbackAPIVersion.VERSION2, transport="websockets")
        self.client.on_connect = self.handle_connect
        self.client.on_message = handle_msg
        self.type = smps_type
        self.tick = 0

        # client.username_pw_set(username="quintuplee", password="solar1")

        if self.client.connect(broker_addr, broker_port, keepalive=keepalive) != 0:
            raise Exception("Failed to connect to Broker")
        else:
            self.client.loop_start()
        
    def send_sun_data(self, smps: SMPS):
        self.client.publish("pico/"+SUN_TOPIC, json.dumps({"target": self.type, "payload": 10}), 0)
        self.tick += 1

    def send_ext_grid_smps(self, smps: SMPS):
        self.client.publish("pico/"+EXT_GRID_TOPIC, json.dumps({"target": self.type, "payload": {"import": 10, "export": None}}), 0)

    def send_storage_smps(self, smps: SMPS):
        self.client.publish("pico/"+STORAGE_TOPIC, json.dumps({"target": self.type, "payload": {"type": "soc", "value": 10}}), 0)
        self.client.publish("pico/"+STORAGE_TOPIC, json.dumps({"target": self.type, "payload": {"type": "power", "value": 10}}), 0)

    def send_load(self, load_num, smps: SMPS):
        if not (load_num >= 1 and load_num <= 4): raise Exception("Invalid value for load_num, when sending data to the load")

        self.client.publish("pico/"+LOAD_TOPICS[load_num - 1], json.dumps({"target": self.type, "payload": 10}), 0)

    def end(self):
        self.client.disconnect()

    def handle_connect(self, client, userdata, flags, rc, o):
        if rc != 0: raise Exception("Failed to connect to Broker")
        client.subscribe(SND+self.type)
        print("Connected to Broker")

    

# def handle_connect(client, userdata, flags, rc, o):
#     if rc != 0: raise Exception("Failed to connect to Broker")
#     print("Connected to Broker")
#     client.subscribe(SND+SUN_TOPIC)

def handle_msg(client, userdata, message):
    # when it recieves data from the server
    # send a response on the effect of the change
    # topic = message.topic
    print(f"Message received: {message.payload.decode()} on topic {message.topic}")

def gen_smps(smps_type: str):
    smps = SMPS(SMPS=smps_type, power_in=int(random() * 10), power_out=int(random() * 10))
    # smps.SMPS = smps_type
    # smps.power_in = random() * 10
    # smps.power_out = random() * 10

    return smps