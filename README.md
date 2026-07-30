# urban-dollop

```mermaid
flowchart LR
    batch_sizes[batch-sizes] --> agents
    zones[zones] --> agents
    demand_slopes[demand-slopes] --> demand[demand]
    demand_thresholds[demand-thresholds] --> demand
    supply_slopes[supply-slopes] --> supply[supply]
    supply_thresholds[supply-thresholds] --> supply
    demand --> agents[agents]
    supply --> agents
    agents --> desire_lines[desire-lines]
    batch_sizes --> desire_lines
    desire_lines --> network_loads
    departures[departures] --> network_loads
    time_intervals[time-intervals] --> network_loads
    dwell_times[dwell-times] --> network_loads
    vehicle_velocities[vehicle-velocities] --> network_loads
    vehicle_capacities[vehicle-capacities] --> network_loads
    road_capacities[road-capacities] --> network_loads
    alternative_specific_constants[alternative-specific-constants] --> network_loads
    network[network] --> network_loads[network-loads]
    vehicles[vehicles] --> network_loads
    network --> network_emissions
    vehicles --> network_emissions
    network_loads[network-loads] --> network_emissions[network-emissions]
    copert_v_coefficients[copert-v-coefficients] --> network_emissions
    emission_factors[emission-factors] --> network_emissions
```
