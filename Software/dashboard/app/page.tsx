"use client";

import React, { useEffect, useRef, useState } from "react";
import { getDayAndTick, getValuesOnTick } from "./actions";
import { LiveGraphs, AllVars, AllGraphs } from "@/helpers/graph_data";
import { getYValues } from "@/helpers/graph_funcs";
import Graph from "@/components/Graph/Graph";
import { GraphData, LiveData, Variable } from "@/helpers/graph_types";
import SmallCard from '@/components/Card/SmallCard';

export default function Home() {
  const [day, setDay] = useState(0);
  const [tick, setTick] = useState(0);
  const [graphData, setGraphData] = useState<GraphData[]>(AllGraphs);
  const [liveData, setLiveData] = useState<LiveData>({cost: 0, buy: 0, sell: 0})
  const [forceRender, setForceRender] = useState(0);

  const changeGraphData = async (prevDay: number, prevTick: number) => {
    const nextDay = prevTick == 59 ? prevDay + 1 : prevDay;
    const nextTick = (prevTick + 1) % 60;
    setDay(nextDay);
    setTick(nextTick);

    // console.log(prevDay, prevTick);

    let tmpGraphData = [...graphData];

    // console.log(day, tick);

    for (let graph of tmpGraphData) {
      const yValues = getYValues(graph);

      let data = await getValuesOnTick(yValues, nextDay, nextTick);
      // console.log(data);
      if (data) {
        graph.data.push(data);
      }
    }

    // fetch cost, buy and sell prices
    let data = await getValuesOnTick({[AllVars.cost.yValue]: 1, [AllVars.buy.yValue]: 1, [AllVars.sell.yValue]: 1}, nextDay, nextTick); 
    if (data){
      setLiveData({
        cost: data[AllVars.cost.yValue],
        buy: data[AllVars.buy.yValue],
        sell: data[AllVars.sell.yValue]
      });
    }

    setGraphData([...tmpGraphData]);
    // setGraphData(tmpGraphData);
    setForceRender((forceRender + 1)%2);

    console.log(graphData);
  };

  useEffect(() => {
    // get the current day and tick
    // check if data from the last tick is available
    getDayAndTick().then((res) =>{
      setDay(res.tick == 0 ? res.day - 1 : res.day);
      setTick(res.tick == 0 ? 59 : res.tick - 1);
    });
  }, []);

  useEffect(()=>{
    const timoutId = setTimeout(() => {
      changeGraphData(day, tick);
    }, 5000);

    return () => clearTimeout(timoutId);
  }, [tick, day, graphData])

  return (
    <main key={forceRender} className="mx-20 my-5">
      <div className="grid gap-5 2xl:grid-cols-2">
        <SmallCard
          className="!w-full"
          top={<p>Day and Tick</p>}
          middle={<p>Tick: {tick}</p>}
          bottom={<p>Day: {day}</p>}
          />

        <SmallCard
          className="!w-full"
          top={<p>Cost</p>}
          middle={<p>{liveData.cost.toFixed(2)} ¢</p>}
          bottom={<p>Buy Price: {liveData.buy} ¢/J | Sell Price: {liveData.sell} ¢/J </p>}
          />
      </div>
      <div className="w-full mt-6 grid gap-5 2xl:grid-cols-2">
        {graphData.map((data, i) => (
          <Graph key={i} data={data} animation={false} />
        ))}
      </div>
    </main>
  );
}
