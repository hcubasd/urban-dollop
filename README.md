# urban-dollop

urban-dollop is a Python library for urban freight simulation. It generalizes
[MASS-GT](https://github.com/orgs/mass-gt/repositories) — a multi-agent freight
simulation system developed at TU Delft — separating reusable model structure from
study-area-specific parameters so the same pipeline can be applied to any city.

---

## Modules

| Module | MASS-GT source | Status |
|---|---|---|
| Parcel demand generation | `parcel_dmnd` | implemented |
| Parcel consolidation (UCCs + microhubs) | `parcel_dmnd` | implemented |
| Parcel delivery scheduling | `parcel_schd` | implemented |
| Network / route assignment | `traf` | planned |
| Emission calculation (COPERT V + grade) | `traf` + grade extension | planned |
| KPI indicators | `outp` | planned |
| Service trip demand | `service` | planned |
| Freight shipment demand | `ship` | planned |
| Freight tour scheduling | `tour` | planned |
| Firm synthesizer | `fs` | planned |

---

## Installation

```bash
pip install urban-dollop
```

---

## Pipeline

```mermaid
flowchart LR
    A[generate-demand] --> B[consolidate-uccs] --> C[consolidate-microhubs] --> D[schedule-deliveries]
```

Each step reads and writes `parcel_demand.csv`. The consolidation steps are optional
and composable — run either, both, or neither between demand generation and scheduling.
All steps are configured via `urban-dollop.toml` in the working directory.

---

## Usage

### generate-demand

Estimates daily parcel delivery demand by zone and carrier. Reads zone
socioeconomics, depot locations, carrier market shares, and a travel-time skim.
Writes one `parcel_demand.csv` row per `(origin_zone, destination_zone, carrier)` triple.

**Canonical output — `parcel_demand.csv`:**

| field | type | description |
|---|---|---|
| `origin_zone_id` | `int` | zone of the carrier depot serving this flow |
| `destination_zone_id` | `int` | zone receiving the parcels |
| `carrier` | `str` | carrier name |
| `n_parcels` | `int` | number of parcels |

**Canonical inputs:**

| file | field | type | description |
|---|---|---|---|
| `zones.gpkg` | `zone_id` | `int` | unique zone identifier |
| `zones.gpkg` | `households` | `float` | household count (linear formulation) |
| `zones.gpkg` | `employment` | `float` | employee count (linear formulation) |
| `depots.gpkg` | `depot_id` | `int` | unique depot identifier |
| `depots.gpkg` | `zone_id` | `int` | zone the depot is located in |
| `depots.gpkg` | `carrier` | `str` | carrier name |
| `carrier_shares.csv` | `name` | `str` | carrier name |
| `carrier_shares.csv` | `share` | `float` | market share fraction (all shares must sum to 1.0) |

**Config — `[parcel_demand]` in `urban-dollop.toml`:**

```toml
[parcel_demand]
parcels_per_household = 0.178   # daily parcels generated per household
parcels_per_employee  = 0.029   # daily parcels generated per employee
delivery_success_b2c  = 0.80    # first-attempt delivery success rate, B2C
delivery_success_b2b  = 0.95    # first-attempt delivery success rate, B2B
# calibration_target = 50000    # optional: scale output to a known study-area total
```

All four rates are required and study-area specific — there are no defaults.
`calibration_target` is optional; when set, all zone demands are scaled
proportionally so the study-area total matches the target.

**CLI:**

```bash
urban-dollop generate-demand data/
urban-dollop generate-demand --logit data/
urban-dollop generate-demand --outdir results/ data/
```

Reads `zones.gpkg`, `depots.gpkg`, `carrier_shares.csv`, and `skim_time.mtx`
(or `.mtx.gz`) from `data/`. Writes `parcel_demand.csv` to the current directory
by default. Add `--logit` to use the ordered logit formulation (see below).

If your files use different column names, pass a mapping in the API call:

```python
zones = LinearZone.from_file("zones.gpkg", columns={"zone_id": "id", "households": "hh"})
```

#### Ordered logit formulation

Use `--logit` when your zone data has population and an integer urbanization
classification instead of household and employment counts. Demand is derived from
an ordered logit over urbanization level following the HARMONY v3 formulation.

**Additional zone fields required (instead of `households` / `employment`):**

| file | field | type | description |
|---|---|---|---|
| `zones.gpkg` | `population` | `float` | total resident population |
| `zones.gpkg` | `urbanization_level` | `int` | integer urbanization class |

A `zones.gpkg` with all five columns works for both formulations — each loads only
what it needs.

**Config — `[parcel_demand_logit]` in `urban-dollop.toml`:**

```toml
[parcel_demand_logit]
beta_urbanization  = {1 = 2.0, 2 = 1.2, 3 = 0.4, 4 = -0.3, 5 = -1.0}
mu_thresholds      = [-0.5, 1.0, 2.0, 2.8, 3.5, 4.0, 5.5, 7.0]
# calibration_target      = 50000   # optional
# monthly_to_daily_divisor = 60.0   # optional: survey-month → daily conversion
# parcel_levels = [0, 1, 2, 3, 4, 5, 10, 15, 20]  # optional: survey response categories
```

`beta_urbanization` and `mu_thresholds` are required and must be estimated from a
household survey for your study area. The Dutch estimates from HARMONY v3
(de Bok et al. 2025) are **not** appropriate defaults for other countries.
`parcel_levels` defaults to the HARMONY v3 survey response categories
`[0, 1, 2, 3, 4, 5, 10, 15, 20]`; override this if your survey used different
discrete options. `monthly_to_daily_divisor` controls the conversion from
monthly survey responses to a daily rate and defaults to `60.0`.

#### Python API

```python
from urban_dollop import LinearZone, Depot, Carrier, SkimMatrix
from urban_dollop import generate_parcel_demand, ParcelDemandConfig, ParcelDemand

zones    = LinearZone.from_file("zones.gpkg")
depots   = Depot.from_file("depots.gpkg")
carriers = Carrier.from_file("carrier_shares.csv")
skim     = SkimMatrix.from_file("skim_time.mtx", zones)

demands = generate_parcel_demand(
    zones, depots, carriers, skim,
    config=ParcelDemandConfig(
        parcels_per_household=0.178,
        parcels_per_employee=0.029,
        delivery_success_b2c=0.80,
        delivery_success_b2b=0.95,
        calibration_target=50000,
    ),
)
ParcelDemand.to_file(demands, "parcel_demand.csv")
```

For the logit formulation, replace `LinearZone` with `LogitZone` and
`generate_parcel_demand` with `generate_logit_demand` / `LogitDemandConfig`.

---

### consolidate-uccs

Reroutes a fraction of parcels destined for UCC catchment zones through Urban
Consolidation Centres. Each rerouted flow is split into two legs:
leg A (origin → nearest UCC) and leg B (UCC → original destination).
Non-catchment parcels pass through unchanged.

The nearest UCC is selected per demand record by minimising the total two-leg
distance: `dist(origin → UCC) + dist(UCC → destination)`.

Reads `parcel_demand.csv` from the input directory. Overwrites it with the
rerouted demand by default.

**Canonical inputs:**

| file | field | type | description |
|---|---|---|---|
| `uccs.csv` | `ucc_id` | `int` | unique UCC identifier |
| `uccs.csv` | `zone_id` | `int` | zone the UCC is located in |
| `ucc_catchment_zones.csv` | `zone_id` | `int` | zone whose inbound parcels are eligible for UCC rerouting |
| `skim_distance.mtx` | — | `float32` | zone-to-zone travel distance matrix |

**Config — `[ucc_consolidation]` in `urban-dollop.toml`:**

```toml
[ucc_consolidation]
probability = 0.30   # fraction of eligible parcels rerouted through a UCC; required
```

`probability` is required (no default) and study-area specific. It controls
what share of catchment-zone parcels are rerouted; the remainder continue as
direct flows.

**CLI:**

```bash
urban-dollop consolidate-uccs data/
urban-dollop consolidate-uccs --outdir results/ data/
```

Reads `zones.gpkg`, `parcel_demand.csv`, `uccs.csv`, `ucc_catchment_zones.csv`,
and `skim_distance.mtx` (or `.mtx.gz`) from `data/`. Writes `parcel_demand.csv`
back to `data/` by default.

#### Python API

```python
from urban_dollop import (
    ParcelDemand, SkimDistance, UCC, UCCCatchmentZone, UCCConfig, Zone,
    consolidate_uccs,
)

zones           = Zone.from_file("zones.gpkg")
demands         = ParcelDemand.from_file("parcel_demand.csv")
uccs            = UCC.from_file("uccs.csv")
catchment_zones = UCCCatchmentZone.from_file("ucc_catchment_zones.csv")
skim_distance   = SkimDistance.from_file("skim_distance.mtx", zones)

result = consolidate_uccs(
    demands=demands,
    uccs=uccs,
    catchment_zones=catchment_zones,
    skim_distance=skim_distance,
    config=UCCConfig(probability=0.30),
)
ParcelDemand.to_file(result, "parcel_demand.csv")
```

---

### consolidate-microhubs

Reroutes all parcels destined for zero-emission zones through carrier-specific
microhubs. Each flow is split into two legs: leg A (origin → nearest microhub)
and leg B (microhub → original destination, zero-emission last mile).
Non-ZEZ parcels pass through unchanged.

The nearest microhub is carrier-specific and selected by minimising last-mile
distance: `dist(microhub → destination)`. Every carrier with ZEZ-destined
parcels must have at least one microhub configured.

Reads `parcel_demand.csv` from the input directory. Overwrites it with the
rerouted demand by default.

**Canonical inputs:**

| file | field | type | description |
|---|---|---|---|
| `microhubs.csv` | `microhub_id` | `int` | unique microhub identifier |
| `microhubs.csv` | `zone_id` | `int` | zone the microhub is located in |
| `microhubs.csv` | `carrier` | `str` | carrier this microhub serves |
| `zero_emission_zones.csv` | `zone_id` | `int` | zone where conventional vehicles are prohibited |
| `skim_distance.mtx` | — | `float32` | zone-to-zone travel distance matrix |

This step has no config section — rerouting is 100% for all ZEZ-bound parcels.

**CLI:**

```bash
urban-dollop consolidate-microhubs data/
urban-dollop consolidate-microhubs --outdir results/ data/
```

Reads `zones.gpkg`, `parcel_demand.csv`, `microhubs.csv`,
`zero_emission_zones.csv`, and `skim_distance.mtx` (or `.mtx.gz`) from `data/`.
Writes `parcel_demand.csv` back to `data/` by default.

#### Python API

```python
from urban_dollop import (
    Microhub, ParcelDemand, SkimDistance, Zone, ZeroEmissionZone,
    consolidate_microhubs,
)

zones         = Zone.from_file("zones.gpkg")
demands       = ParcelDemand.from_file("parcel_demand.csv")
microhubs     = Microhub.from_file("microhubs.csv")
zez_zones     = ZeroEmissionZone.from_file("zero_emission_zones.csv")
skim_distance = SkimDistance.from_file("skim_distance.mtx", zones)

result = consolidate_microhubs(
    demands=demands,
    microhubs=microhubs,
    zez_zones=zez_zones,
    skim_distance=skim_distance,
)
ParcelDemand.to_file(result, "parcel_demand.csv")
```

---

### schedule-deliveries

Assigns parcel demand to vehicle tours. Groups demand by `(origin_zone, carrier)`,
clusters delivery stops spatially, and assigns a vehicle type by capacity.
Returns one row per tour leg.

**Canonical output — `delivery_trips.csv`:**

| field | type | description |
|---|---|---|
| `tour_id` | `int` | unique tour identifier |
| `trip_id` | `int` | sequential leg position within the tour |
| `carrier` | `str` | carrier operating the tour |
| `origin_zone_id` | `int` | zone at the start of this leg |
| `destination_zone_id` | `int` | zone at the end of this leg |
| `n_parcels` | `int` | parcels delivered at this stop (0 for the return leg) |
| `vehicle_id` | `int` | vehicle type assigned to this tour |

**Canonical inputs:**

| file | field | type | description |
|---|---|---|---|
| `vehicles.csv` | `vehicle_id` | `int` | unique vehicle type identifier |
| `vehicles.csv` | `name` | `str` | vehicle type label |
| `vehicles.csv` | `max_parcels` | `int` | maximum parcel capacity |

The scheduler assigns the smallest vehicle whose capacity fits the tour load.

**Config — `[parcel_scheduling]` in `urban-dollop.toml`:**

```toml
[parcel_scheduling]
# seed = 42   # optional: fix RNG seed for reproducible tour clustering
```

**CLI:**

```bash
urban-dollop schedule-deliveries data/
urban-dollop schedule-deliveries --outdir results/ data/
```

Reads `zones.gpkg`, `vehicles.csv`, `skim_time.mtx` (or `.mtx.gz`), and
`parcel_demand.csv` from `data/`. Writes `delivery_trips.csv` to the current
directory by default.

#### Python API

```python
from urban_dollop import (
    ParcelDemand, SkimMatrix, Vehicle, Zone,
    schedule_parcel_deliveries, ParcelSchedulingConfig, DeliveryTrip,
)

zones    = Zone.from_file("zones.gpkg")
vehicles = Vehicle.from_file("vehicles.csv")
skim     = SkimMatrix.from_file("skim_time.mtx", zones)
demands  = ParcelDemand.from_file("parcel_demand.csv")

trips = schedule_parcel_deliveries(
    demands=demands,
    vehicles=vehicles,
    skim=skim,
    config=ParcelSchedulingConfig(seed=42),
)
DeliveryTrip.to_file(trips, "delivery_trips.csv")
```
