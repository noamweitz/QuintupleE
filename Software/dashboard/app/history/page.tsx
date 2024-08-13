"use client";

import React, { useEffect, useRef, useState } from "react";
import Graph from "@/components/Graph/Graph";
import { getTick } from "../actions";
import { GraphData, Variable } from "@/helpers/graph_types";
import { AllVars, AllGraphs } from "@/helpers/graph_data";
import { getYValues } from "@/helpers/graph_funcs";
import DeferrableTable from "@/components/DeferrableTable/DeferrableTable";

export default function History() {
  const [graphData, setGraphData] = useState<GraphData[]>([]);

  useEffect(() => {
    if (graphData.length == 0) {
      for (let graph of AllGraphs) {
        const yValues = getYValues(graph);

        // console.log(yValues);
        // console.log(graph.title);

        getTick(yValues).then((data: any) => {
          setGraphData((prev) => {
            let gData = graph;
            gData.data = data;
            return [...prev, gData];
          });
        });
      }
    }
  }, []);

  return (
    <main className="w-full mt-6 grid gap-5 2xl:grid-cols-2 px-8">
      {graphData.map((data, i) => (
        <Graph key={i} data={data} animation={false} />
      ))}

      <div className="flex w-full justify-center items-center col-span-2 p-20">
        <DeferrableTable />
      </div>
    </main>
  );
}
