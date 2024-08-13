"use server";
require("dotenv").config();
import { MongoClient, Db } from "mongodb";

var client: MongoClient | undefined;
var db: Db | undefined;
const connString = process.env.MONGO_URL;
if (connString == undefined)
  throw new Error("Can't Find Database Connection String");
else {
  client = new MongoClient(connString);
  db = client.db("smartgrid");
}

async function getTick(yValues: any) {
  var res = await db
    ?.collection("ticks")
    .find({}, { projection: { _id: 0, ...yValues, day: 1, tick: 1 } })
    .sort({
      day: 1,
      tick: 1,
    })
    .toArray();
  return res;
}

async function getDayAndTick(){
  const res = await fetch("https://icelec50015.azurewebsites.net/demand");
  const data = await res.json();
  return {
    day: data.day,
    tick: data.tick
  }
}

async function getValuesOnTick(yValues: any, day: number, tick: number) {
  var res = await db
    ?.collection("ticks")
    .findOne({tick: tick, day: day}, { projection: { _id: 0, ...yValues, day: 1, tick: 1 } });
  return res;
}

async function getAllDays(){
  return await db?.collection("days").find().sort({day: 1}).toArray();
}

async function getDeferrableData(day: number){
  return await db?.collection("ticks").find({day: day}, {projection: {
    _id: 0,
    day: 1,
    tick: 1,
    avg_blue_power: 1,
    avg_yellow_power: 1,
    avg_grey_power: 1,
    algo_blue_power: 1,
    algo_yellow_power: 1,
    algo_grey_power: 1,
  }}).sort({tick: 1}).toArray();
}


export { getTick, getDayAndTick, getValuesOnTick, getAllDays, getDeferrableData };
