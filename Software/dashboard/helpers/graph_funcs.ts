import { Variable, GraphType, GraphData } from '@/helpers/graph_types';

function getYValues(graph: GraphData){
    var yValues: any = {};

    for (let unit1 of graph.unitData1) {
      yValues[unit1.yValue] = 1;
    }

    for (let unit2 of graph.unitData2) {
      yValues[unit2.yValue] = 1;
    }

    return yValues;
}

const changeToLine = (variable: Variable): Variable => {
  variable.graphType = GraphType.Line;
  return variable;
}
const changeToBar = (variable: Variable): Variable => {
  variable.graphType = GraphType.Bar;
  return variable;
}

export { getYValues, changeToLine, changeToBar };