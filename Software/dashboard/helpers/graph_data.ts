import { GraphData, Variable, FormatString, GraphType } from '@/helpers/graph_types';
import { changeToLine, changeToBar } from './graph_funcs';

const red = "#fa5246";
const blue = "#3da9fc";
const grey = "#5f6c7b";
const yellow = "#ffd803";

const x = "tick"

const AllVars = {
    irradiance: new Variable("sun", "%", GraphType.Line),
    real_pv_power: new Variable("avg_pv_power", "Watts", GraphType.Line),
    real_import_power: new Variable("avg_import_export_power", "Watts", GraphType.Line),
    algo_import_power: new Variable("algo_import_power", "Watts", GraphType.Line),
    buy: new Variable("buy_price", "Cents", GraphType.Line),
    sell: new Variable("sell_price", "Cents", GraphType.Line),
    real_storage_power: new Variable("avg_storage_power", "Watts", GraphType.Line),
    algo_storage_power: new Variable("algo_store_power", "Watts", GraphType.Line),
    exp_instant_demand: new Variable("demand", "Watts", GraphType.Line),
    real_instant_demand: new Variable("avg_red_power", "Watts", GraphType.Line),
    soc: new Variable("storage_soc", "%", GraphType.Line),
    algo_blue_def: new Variable("algo_blue_power", "Watts", GraphType.Line),
    algo_grey_def: new Variable("algo_grey_power", "Watts", GraphType.Line),
    algo_yellow_def: new Variable("algo_yellow_power", "Watts", GraphType.Line),
    real_blue_def: new Variable("avg_blue_power", "Watts", GraphType.Line),
    real_grey_def: new Variable("avg_grey_power", "Watts", GraphType.Line),
    real_yellow_def: new Variable("avg_yellow_power", "Watts", GraphType.Line),
    breal_blue_def: new Variable("avg_blue_power", "Watts", GraphType.Bar),
    breal_grey_def: new Variable("avg_grey_power", "Watts", GraphType.Bar),
    breal_yellow_def: new Variable("avg_yellow_power", "Watts", GraphType.Bar),
    cost: new Variable("cost", "Cents", GraphType.Line),
}

const AllGraphs: GraphData[] = [
    {
        title: "Cost and Instant Demand",
        xValue: x,
        unitData1: [AllVars.cost],
        unitData2: [AllVars.exp_instant_demand],
        data: [],
    },
    {
        title: "Irradiance vs Real PV Power",
        xValue: x,
        unitData1: [AllVars.irradiance],
        unitData2: [AllVars.real_pv_power],
        data: [],
    },
    {
        title: "Real and Expected Import Power vs Buy and Sell Prices",
        xValue: x,
        unitData1: [AllVars.real_import_power, AllVars.algo_import_power],
        unitData2: [AllVars.buy, AllVars.sell],
        data: [],
    },
    {
        title: "SOC, Real and Expected Import Power",
        xValue: x,
        unitData1: [AllVars.soc],
        unitData2: [AllVars.real_storage_power, AllVars.algo_storage_power],
        data: [],
    },
    {
        title: "Storage Power vs Buy and Sell Prices",
        xValue: x,
        unitData1: [AllVars.real_storage_power, AllVars.algo_storage_power],
        unitData2: [AllVars.buy, AllVars.sell],
        data: [],
    },
    {
        title: "Instant Demand vs Expected Instant Demand",
        xValue: x,
        unitData1: [AllVars.real_instant_demand, AllVars.exp_instant_demand],
        unitData2: [],
        data: [],
    },
    {
        title: "Deferrable 1 (Blue)",
        xValue: x,
        unitData1: [AllVars.real_blue_def, AllVars.algo_blue_def],
        unitData2: [AllVars.buy, AllVars.sell],
        data: [],
    },
    {
        title: "Deferrable 2 (Grey)",
        xValue: x,
        unitData1: [AllVars.real_grey_def, AllVars.algo_grey_def],
        unitData2: [AllVars.buy, AllVars.sell],
        data: [],
    },
    {
        title: "Deferrable 3 (Yellow)",
        xValue: x,
        unitData1: [AllVars.real_yellow_def, AllVars.algo_yellow_def],
        unitData2: [AllVars.buy, AllVars.sell],
        data: [],
    },
]

const Colours = [
	"#2D6EFF",
	"#F25F4C",
	"#2CB67D",
	"#FF8906",
	"#E53170",
	"#000000",
	"#fec7d7",
	"#994ff3",
]

var LiveGraphs: GraphData[] = [
    {
        title: "SOC",
        xValue: x,
        unitData1: [AllVars.soc],
        unitData2: [],
        data: [],
    },
    {
        title: "Demands",
        xValue: x,
        unitData1: [AllVars.real_instant_demand, AllVars.real_blue_def, AllVars.real_grey_def, AllVars.real_yellow_def],
        unitData2: [],
        data: [],
    },
    {
        title: "Demands",
        xValue: x,
        unitData1: [AllVars.real_instant_demand, AllVars.real_blue_def, AllVars.real_grey_def, AllVars.real_yellow_def],
        unitData2: [],
        data: [],
    }

]


export { AllGraphs, AllVars, x, Colours, LiveGraphs }