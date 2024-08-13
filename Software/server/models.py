from pydantic import BaseModel
from typing import List
from optimisation.models import *

# class AlgoDecisions(BaseModel):
# 	day: int
# 	tick: int
# 	power_import: float
# 	power_store: float
# 	deferables_supplied: List[float]

# class TickOutcomes(BaseModel):
# 	day: int
# 	tick: int
# 	cost: float
# 	avg_pv_power: float
# 	storage_soc: float
# 	avg_storage_power: float
# 	avg_import_export_power: float
# 	avg_red_power: float
# 	avg_blue_power: float
# 	avg_yellow_power: float
# 	avg_grey_power: float

class FullTick(BaseModel):
	day: int
	tick: int
	demand: float
	sun: int
	buy_price: int
	sell_price: int
	# outcomes
	cost: float
	avg_pv_power: float
	storage_soc: float
	avg_storage_power: float
	avg_import_export_power: float
	avg_red_power: float
	avg_blue_power: float
	avg_yellow_power: float
	avg_grey_power: float

	# algo decisions
	algo_import_power: float
	algo_store_power: float
	algo_blue_power: float
	algo_yellow_power: float
	algo_grey_power: float
