"use client";
import mqtt from "mqtt";

const picoTopic = "pico";
const serverTopic = "server";
const uiTopic = "ui";

const prec = 2;
const mppt_target_topic = "mppt";

class MQTTClient {
  private client: any;
  public pvArrayPower: number = 0;
  public loadPowers: number[] = [0, 0, 0, 0];
  public devices: ({name: string, lastHeard: number})[] = [];
  public mppt: boolean = false;

  constructor(
    setCurrentPV: any,
    setLoadPowers: any,
    setImportPower: any,
    setExportPower: any,
    setSoc: any,
    setSocPower: any,
    setOverride: any,
    setVBus: any,
    address: string = "35.178.119.19",
    port: number = 9001
  ) {
    console.log("running constructor")
    if(this.devices.length == 0) {
      for(let [key, val] of Object.entries(Device)) {
        this.devices.push({name: val, lastHeard: 0})
      }
      // console.log(this.devices);
    }

    this.client = mqtt.connect(`ws://${address}:${port}`);
    this.client.on("connect", () => console.log("Connected to MQTT Broker"));
    this.client.on("error", (err: any) => console.error(err));
    this.client.on("message", (topic: any, message: any) => {
      // console.log(`Received message on topic ${topic}: ${message.toString()}`);
      const msgObj = JSON.parse(message.toString());

      // this is data that is to be sent and stored on the server
      if (topic === serverTopic && "target" in msgObj && "payload" in msgObj) {
        // console.log("Received data from server")
        // send data to server
        switch (msgObj.target) {
          case Device.PV_ARRAY: {
            setCurrentPV(msgObj.payload.toFixed(prec));
            break;
          }
          case Device.LOADR: {
            setLoadPowers((prev: number[]) => {
              const old = [...prev];
              old[0] = msgObj.payload.toFixed(prec);
              return old;
            });
            break;
          }
          case Device.LOADB: {
            setLoadPowers((prev: number[]) => {
              const old = [...prev];
              old[1] = msgObj.payload.toFixed(prec);
              return old;
            });
            break;
          }
          case Device.LOADY: {
            setLoadPowers((prev: number[]) => {
              const old = [...prev];
              old[2] = msgObj.payload.toFixed(prec);
              return old;
            });
            break;
          }
          case Device.LOADK: {
            setLoadPowers((prev: number[]) => {
              const old = [...prev];
              old[3] = msgObj.payload.toFixed(prec);
              return old;
            });
            break;
          }
          case Device.EXTERNAL_GRID: {
            console.log(msgObj.payload);
            if (msgObj.payload.import_power)
              setImportPower(msgObj.payload.import_power.toFixed(prec));
            else if (msgObj.payload.export_power)
              setExportPower(msgObj.payload.export_power.toFixed(prec));
            break;
          }
          case Device.STORAGE: {
            if (msgObj.payload.type == "soc")
              setSoc(msgObj.payload.value.toFixed(prec));
            else if(msgObj.payload.type == "power") setSocPower(msgObj.payload.value.toFixed(prec));
            else setVBus(msgObj.payload.value.toFixed(prec));
            break;
          }
        }
      } else if (
        topic == uiTopic &&
        "target" in msgObj &&
        "payload" in msgObj
      ) {
        if (msgObj.target == "override") {
          setOverride(msgObj.payload);
        } else if(msgObj.target == mppt_target_topic && msgObj.payload == "req") {
          this.send_mppt_status(this.mppt);
        }
      }

      for(let i = 0; i < this.devices.length; i++) {
        if(this.devices[i].name == msgObj.target) {
          this.devices[i].lastHeard = Date.now();
          break;
        }
      }

      // console.log(this.devices);
    });

    this.client.subscribe(serverTopic, (err: any) => {
      if (err) console.error(err);
    });
    this.client.subscribe(uiTopic, (err: any) => {
      if (err) console.error(err);
    });
  }

  send_irradiance(val: number) {
    this.client.publish(
      `${picoTopic}/${Device.PV_ARRAY}`,
      JSON.stringify({ target: Device.PV_ARRAY, payload: val })
    );
  }

  send_storage_power(val: number) {
    this.client.publish(
      `${picoTopic}/${Device.STORAGE}`,
      JSON.stringify({ target: Device.STORAGE, payload: val })
    );
    // console.log("here")
  }

  send_load_power(val: number, load: string) {
    this.client.publish(
      `${picoTopic}/${load}`,
      JSON.stringify({ target: load, payload: val })
    );
  }

  send_mppt_status(mppt: boolean) {
    this.client.publish(mppt_target_topic, JSON.stringify({target: "mppt", payload: mppt}));
  }

  send_override_status(override: boolean) {
    this.client.publish(
      serverTopic,
      JSON.stringify({ target: "override", payload: override })
    );
  }

  ask_override_status() {
    this.client.publish(
      serverTopic,
      JSON.stringify({ target: "override", payload: "req" })
    );
  }
}

// Devices, taken from the MQTT pico client
enum Device {
  STORAGE = "storage",
  EXTERNAL_GRID = "external-grid",
  PV_ARRAY = "pv-array",
  LOADR = "loadR",
  LOADY = "loadY",
  LOADB = "loadB",
  LOADK = "loadK",
}

export { MQTTClient, Device };