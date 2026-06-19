# NYC FHV Dispatch Modeling Summary

## Question 1: Hourly Demand Prediction
Model: HistGradientBoosting Poisson model blended with the best historical baseline.
Output: q1_hourly_prediction.xlsx with 1464 rows, 61 zones, and 24 hours.
Validation MAE: 1.9167; RMSE: 3.6289; best baseline MAE: 1.9820.

## Question 2: FHV Pricing
Model: Taxi reference price regression plus cost floor and minimum-profit constraint.
Output: q2_fhv_pricing.xlsx with 115 priced FHV orders.
Average FHV price: 15.96; average estimated profit rate: 56.18%.

## Question 3: Noon Vehicle Allocation
Model: Greedy integer allocation by marginal profit, demand, and service capacity.
Output: q3_vehicle_allocation.xlsx with N=50, 100, and 200 vehicle plans.
Estimated incremental profit for N=100: 2183.85.
When predicted noon demand is fully covered, remaining vehicles are held idle/reserve; for N=200, 176 vehicles are allocated and 24 remain idle.

## Question 4: Three Base Locations
Model: Exhaustive weighted p-median over Brooklyn zone triples.
Output: q4_base_location.xlsx with selected bases and zone assignments.
Optimal base zones: 33;111;222 (Brooklyn Heights;Green-Wood Cemetery;Starrett City) with weighted dispatch-time cost 26190.96.
Feasibility note: zone-level base IDs identify service areas; the final physical depot should be placed on feasible parking or dispatch property inside the selected TLC zone.

## Sensitivity Analysis
Output: sensitivity_analysis.xlsx with 16 scenarios covering vehicle counts and pricing parameters.
The vehicle-count analysis reports N=25,50,75,100,150,200,250; pricing analysis varies minimum profit rate and competitive discount.

## Assumptions
- Weather features use Open-Meteo historical hourly reanalysis for Brooklyn when network access is available, with a deterministic template fallback for reproducibility.
- OD pairs with insufficient taxi samples use centroid-distance fallback calibrated by historical average speed.
- Vehicle counts are parameterized as 50, 100, and 200 because the problem statement does not fix an added fleet size.
