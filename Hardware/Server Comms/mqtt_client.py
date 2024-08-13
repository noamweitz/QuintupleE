import machine
import ubinascii
from wifi import init
import json


# topics
PICO_TOPIC = "pico"
SERVER_TOPIC = "server"
UI_TOPIC = "ui"
MPPT_TOPIC = "mppt"

# MQTT broker settings
MQTT_CLIENT_ID = ubinascii.hexlify(machine.unique_id())
MQTT_BROKER = "35.178.119.19"
MQTT_BROKER_PORT = 1883


# all devices
# topics to subscribe to
class DEVICE:
    STORAGE = "storage"
    EXTERNAL_GRID = "external-grid"
    PV_ARRAY =  "pv-array"
    LOADR = "loadR"
    LOADY = "loadY"
    LOADB = "loadB"
    LOADK = "loadK"


class MClient:
    def __init__(self, device: str):
        init()

        from umqtt.robust import MQTTClient

        client = MQTTClient(
            client_id=MQTT_CLIENT_ID,
            server=MQTT_BROKER,
            port=MQTT_BROKER_PORT,
            keepalive=1000,
        )

        print("Connecting to broker")

        client.set_callback(self.on_mqtt_msg)
        client.connect()

        self.client = client
        self.client.subscribe(f"{PICO_TOPIC}/{device}")

        # print(f"Waiting for messages on {PICO_TOPIC}/{device}")

        self.desired_power = 0
        self.power_req = 0
        self.irradiance = 0
        self.mppt = False

        self.device = device

        # if it is the PV array
        # subscribe to mppt topic and sync the mppt value with the ui
        if device == DEVICE.PV_ARRAY:
            self.client.subscribe(MPPT_TOPIC)
            self.sync_mppt_status()
    
    def on_mqtt_msg(self, topic, msg):
        try:
            msg_str = msg.decode()

            data = json.loads(msg_str)
            if "target" not in data or "payload" not in data:
                raise Exception("Invalid message format")
        
            elif data["target"] == DEVICE.STORAGE:
                self.desired_power = data["payload"]
                # print(f"desired_power: {self.desired_power}")

            elif data["target"] == DEVICE.PV_ARRAY:
                self.irradiance = data["payload"]
                print(f"Irradiance: {self.irradiance}")

            elif data["target"] == MPPT_TOPIC:
                self.mppt = data["payload"]
                print(f"mppt: {self.mppt}")
                
            # this is for all loads
            elif data["target"] == self.device:
                self.power_req = data["payload"]
                print(f"power_req: {self.power_req}")


        except Exception as e:
            print(f"Error when processing message: {e}\nRecieved: {topic.decode()}, {msg.decode()}")

    def check_msg(self):
        self.client.check_msg()
    
    def send_external_grid(self, import_p, export_p):
        self.client.publish(SERVER_TOPIC, json.dumps({"target": DEVICE.EXTERNAL_GRID, "payload":{"import_power": import_p, "export_power": export_p}}))

    def send_load_power(self, power):
        self.client.publish(SERVER_TOPIC, json.dumps({"target": self.device, "payload": power}))

    def sync_mppt_status(self):
        self.client.publish(UI_TOPIC, json.dumps({"target": MPPT_TOPIC, "payload": "req"}))

    def get_mppt_status(self):
        self.check_msg()
        return self.mppt

    # def send_shunt_current(self, current):
    #     self.client.publish(UI_TOPIC, json.dumps({"target": self.device, "payload": current}))

    def get_power_req(self):
        self.check_msg()
        return self.power_req if self.power_req > 0.01 else -1
    
    def get_desired_power(self):
        self.check_msg()
        
        if(abs(self.desired_power) <= 2):
            return self.desired_power
        else: return 0

    def get_irradiance(self):
        self.check_msg()
        return self.irradiance
    
    def send_v_bus(self, v_bus):
        self.client.publish(SERVER_TOPIC, json.dumps({"target": DEVICE.STORAGE, "payload": {"type": "v-bus", "value": v_bus}}))

    # percentage of the capacitor
    def send_soc(self, soc):
        # TODO: check if this needs to be changed to the UI
        self.client.publish(SERVER_TOPIC, json.dumps({"target": DEVICE.STORAGE, "payload": {"type": "soc", "value":soc}}))
    
    # the power used to charge the capacitor
    def send_storage_power(self, power):
        self.client.publish(SERVER_TOPIC, json.dumps({"target": DEVICE.STORAGE, "payload": {"type": "power", "value":power}}))
    
    # 
    def send_pv_power(self, power):
        self.client.publish(SERVER_TOPIC, json.dumps({"target": DEVICE.PV_ARRAY, "payload": power}))

