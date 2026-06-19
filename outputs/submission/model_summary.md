# NYC FHV Dispatch Modeling Summary

## Question 1: Hourly Demand Prediction
Model: HistGradientBoosting Poisson model blended with the best historical baseline.
Output: q1_hourly_prediction.xlsx with 1464 rows, 61 zones, and 24 hours.
Validation MAE: 1.9031; RMSE: 3.5816; best baseline MAE: 1.9820.

## Question 2: FHV Pricing
Model: Taxi reference price regression plus cost floor and minimum-profit constraint.
Output: q2_fhv_pricing.xlsx with 115 priced FHV orders.
Average FHV price: 15.92; average estimated profit rate: 56.03%.

## Question 3: Noon Vehicle Allocation
Model: Greedy integer allocation by marginal profit, demand, and service capacity.
Output: q3_vehicle_allocation.xlsx with N=50, 100, and 200 vehicle plans.
Estimated incremental profit for N=100: 2133.61.

## Question 4: Three Base Locations
Model: Exhaustive weighted p-median over Brooklyn zone triples.
Output: q4_base_location.xlsx with selected bases and zone assignments.
Optimal base zones: 65;111;222 (Downtown Brooklyn/MetroTech;Green-Wood Cemetery;Starrett City) with weighted dispatch-time cost 25558.48.

## Assumptions
- Weather features use a deterministic replaceable hourly template because no external weather file was supplied.
- OD pairs with insufficient taxi samples use centroid-distance fallback calibrated by historical average speed.
- Vehicle counts are parameterized as 50, 100, and 200 because the problem statement does not fix an added fleet size.
