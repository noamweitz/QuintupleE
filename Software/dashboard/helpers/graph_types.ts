enum GraphType {
    Bar = 0,
    Line = 1,
}

class Variable {
    yValue: string;
    yUnit: string;
    graphType: GraphType;
    colour: string | undefined;

    constructor(yValue: string, yUnit: string, graphType: GraphType, colour?: string) {
        this.yValue = yValue;
        this.yUnit = yUnit;
        this.graphType = graphType;
        this.colour = colour;
    }

    getYUnit() {
        return FormatString(this.yUnit);
    }
    getYLabel() {
        return FormatString(this.yValue);
    }
}

interface GraphData {
    title: string;
    xValue: string;
    unitData1: Variable[];
    unitData2: Variable[];
    data: any;
}

function FormatString(s: string){
    return s.split("_").map((word) => word.charAt(0).toUpperCase() + word.slice(1)).join(" ");
}

interface LiveData {
    cost: number,
    buy: number,
    sell: number,
}


export { Variable, FormatString, GraphType }
export type { GraphData, LiveData }