import { GraphData, FormatString, GraphType } from "@/helpers/graph_types";
import { Colours } from "@/helpers/graph_data";
import React, { useState, useEffect } from "react";
import {
  Line,
  LineChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceArea,
  ComposedChart,
  Legend,
  Bar,
} from "recharts";
import {
  MagnifyingGlassMinusIcon,
  ArrowsPointingOutIcon,
  ArrowsPointingInIcon,
  TrashIcon,
} from "@heroicons/react/24/outline";

export default function Graph({
  data,
  animation = false,
}: {
  data: GraphData;
  animation: boolean;
}) {
  const [graphFullScreen, setGraphFullScreen] = useState<Boolean>(false);

  return (
    <>
      {graphFullScreen && (
        <div className="fixed w-full h-full z-10 bg-black/50 backdrop-blur-sm top-0 left-0 flex justify-center items-center p-[50px]">
          <Plot
            className="h-[80%]"
            data={data}
            animation={animation}
            graphFullScreen={graphFullScreen}
            setGraphFullScreen={setGraphFullScreen}
          ></Plot>
        </div>
      )}
      <Plot
        className="h-[500px]"
        data={data}
        animation={animation}
        graphFullScreen={graphFullScreen}
        setGraphFullScreen={setGraphFullScreen}
      ></Plot>
    </>
  );
}

function Plot({
  data,
  graphFullScreen,
  setGraphFullScreen,
  className,
  animation = false,
}: {
  data: GraphData;
  graphFullScreen: Boolean;
  setGraphFullScreen: React.Dispatch<React.SetStateAction<Boolean>>;
  className: string;
  animation: boolean;
}) {
  const [leftZoom, setLeftZoom] = useState<number | undefined>(undefined);
  const [rightZoom, setRightZoom] = useState<number | undefined>(undefined);
  const [leftDom, setLeftDom] = useState<number>(0);
  const [rightDom, setRightDom] = useState<number>(data.data.length);

  const handleMouseDown = (e: any) => {
    if (leftZoom == undefined) {
      // first click sets the value of the left zoom point
      setLeftZoom(e.activeTooltipIndex);
    } else {
      setLeftZoom(undefined);
      setRightZoom(undefined);
    }
  };

  const handleMouseUp = (e: any) => {
    if (leftZoom != undefined && rightZoom != undefined) {
      // second click sets the value of the right zoom click

      if (leftZoom < rightZoom) {
        setLeftDom(leftZoom - 1);
        setRightDom(rightZoom - 1);
      } else {
        // incase first selected the RHS
        setLeftDom(rightZoom - 1);
        setRightDom(leftZoom - 1);
      }
    }

    setLeftZoom(undefined);
    setRightZoom(undefined);
  };

  const handleZoomOut = () => {
    setLeftDom(0);
    setRightDom(data.data.length);
    setLeftZoom(undefined);
    setRightZoom(undefined);
  };

  const makeBigger = () => setGraphFullScreen(true);
  const makeSmaller = () => setGraphFullScreen(false);

  return (
    <div
      className={`w-full bg-blue flex flex-col justify-center items-center bg-primary rounded-2xl ${className}`}
    >
      {/* title */}
      <h2 className="text-secondary text-2xl font-bold">{data.title}</h2>
      {/* Control buttons */}
      <div className="w-full flex p-1 pb-4">
        <button
          className="bg-secondary p-2 rounded-full ml-auto"
          onClick={handleZoomOut}
        >
          <MagnifyingGlassMinusIcon className="size-6 text-primary" />
        </button>

        <button
          className="bg-secondary p-2 rounded-full ml-[10px] mr-[50px]"
          onClick={!graphFullScreen ? makeBigger : makeSmaller}
        >
          {!graphFullScreen ? (
            <ArrowsPointingOutIcon className="size-6 text-primary" />
          ) : (
            <ArrowsPointingInIcon className="size-6 text-white" />
          )}
        </button>
      </div>
      <ResponsiveContainer height="80%" width="90%">
        <ComposedChart
          data={data.data.slice(leftDom, rightDom)}
          onMouseDown={handleMouseDown}
          onMouseMove={(e: any) => {
            if (leftZoom) setRightZoom(e.activeTooltipIndex);
          }}
          onMouseUp={handleMouseUp}
          margin={{ bottom: 30 }}
          className="select-none"
        >
          <XAxis
            // allowDataOverflow
            dataKey={data.xValue}
            label={{
              value: FormatString(data.xValue),
              position: "insideBottom",
              offset: -8,
            }}
            padding={{ left: 5, right: 5 }}
          />

          {data.unitData1.length > 0 && (
            <YAxis
              // allowDataOverflow
              label={{
                value: data.unitData1[0].getYUnit(),
                angle: -90,
                position: "insideLeft",
                offset: 10,
              }}
              yAxisId="left"
            />
          )}

          {data.unitData2.length > 0 && (
            <YAxis
              // allowDataOverflow
              label={{
                value: data.unitData2[0].getYUnit(),
                angle: -90,
                position: "insideRight",
                offset: 10,
              }}
              yAxisId="right"
              orientation="right"
            />
          )}

          <CartesianGrid stroke="#ccc" />

          {data.unitData1.map((vari, i) =>
            vari.graphType == GraphType.Line ? (
              <Line
                key={i}
                isAnimationActive={animation}
                type="monotone"
                dataKey={vari.yValue}
                stroke={
                  vari.colour != undefined
                    ? vari.colour
                    : Colours[i % Colours.length]
                }
                activeDot={{ r: 5 }}
                dot={{ r: 0 }}
                yAxisId="left"
                strokeWidth={2}
              />
            ) : (
              <Bar
                key={i}
                type="monotone"
                dataKey={vari.yValue}
                fill={
                  vari.colour != undefined
                    ? vari.colour
                    : Colours[i % Colours.length]
                }
                yAxisId="left"
              />
            )
          )}

          {data.unitData2.map((vari, i) =>
            vari.graphType == GraphType.Line ? (
              <Line
                key={i + data.unitData1.length}
                isAnimationActive={animation}
                type="monotone"
                dataKey={vari.yValue}
                stroke={
                  vari.colour != undefined
                    ? vari.colour
                    : Colours[(i + data.unitData1.length) % Colours.length]
                }
                activeDot={{ r: 5 }}
                dot={{ r: 0 }}
                yAxisId="right"
              />
            ) : (
              <Bar
                key={i}
                type="monotone"
                dataKey={vari.yValue}
                fill={
                  vari.colour != undefined
                    ? vari.colour
                    : Colours[i % Colours.length]
                }
                yAxisId="right"
              />
            )
          )}

          <Tooltip content={CustomTooltip}></Tooltip>

          <Legend
            wrapperStyle={{
              paddingTop: "10px",
            }}
          />

          {leftZoom && rightZoom && (
            <ReferenceArea
              yAxisId="left"
              isFront={true}
              x1={leftZoom}
              x2={rightZoom}
            ></ReferenceArea>
          )}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

// tooltip show when hovering over datapoint
function CustomTooltip({ active, payload, label }: any) {
  let data = [];
  if (active && payload && payload.length > 0 && payload[0].payload) {
    // console.log(payload[0].payload);
    for (let key in payload[0].payload) {
      // console.log(key, payload[0].payload[key]);
      data.push([FormatString(key), payload[0].payload[key]]);
    }
  }

  return active ? (
    <div className="text-black bg-white p-3 rounded-md bg-opacity-90">
      {data.map((d, i) => (
        <p key={i}>
          {d[0]}: {d[1]}
        </p>
      ))}
    </div>
  ) : undefined;
}
