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

## Usage

### Parcel demand generation

Estimate daily parcel delivery demand from zonal population and employment data.

```python
from urban_dollop import Zone, Depot, Carrier, SkimMatrix, generate_parcel_demand

zones = Zone.from_file("zones.gpkg")
depots = Depot.from_file("depots.gpkg")
carriers = Carrier.from_file("carrier_shares.csv")
skim = SkimMatrix.from_file("skim_time.mtx", zones)

demands = generate_parcel_demand(zones, depots, carriers, skim)
```

`demands` is a `list[ParcelDemand]` — one record per `(destination_zone, depot)` pair:

| field | type | description |
|---|---|---|
| `destination_zone_id` | `int` | zone receiving the parcels |
| `depot_id` | `int` | depot handling this flow |
| `n_parcels` | `int` | number of parcels |

**Save to CSV:**

```python
ParcelDemand.to_file(demands, "parcel_demand.csv")
```

**Calibration via `urban-dollop.toml`:**

```toml
[parcel_demand]
parcels_per_household = 0.2054
parcels_per_employee  = 0.0
delivery_success_b2c  = 0.75
delivery_success_b2b  = 0.95
# calibration_target = 50000  # optional: scale total to a known daily count
```

The rate parameters (`parcels_per_household`, `parcels_per_employee`) control
the spatial distribution of demand across zones. `calibration_target`, when
set, applies a proportional scaling factor so the study-area total matches a
known aggregate — for example, a national parcel volume statistic divided by
the number of cities. The spatial distribution is preserved.

**Programmatic override:**

```python
from urban_dollop import ParcelDemandConfig

demands = generate_parcel_demand(
    zones, depots, carriers, skim,
    config=ParcelDemandConfig(
        parcels_per_household=0.178,
        parcels_per_employee=0.029,
        delivery_success_b2c=0.80,
        delivery_success_b2b=0.95,
        calibration_target=50000,  # optional
    ),
)
```

**Column mapping** — when your files use different column names:

```python
zones = Zone.from_file("zones.gpkg", columns={
    "zone_id": "id",
    "households": "hh_count",
    "employment": "jobs",
})
```

Canonical field names:

| model | field | description |
|---|---|---|
| `Zone` | `zone_id` | unique integer zone identifier |
| `Zone` | `households` | household count |
| `Zone` | `employment` | employee count |
| `Depot` | `depot_id` | unique integer depot identifier |
| `Depot` | `zone_id` | zone the depot is located in |
| `Depot` | `carrier` | carrier name (must match `Carrier.name`) |
| `Carrier` | `name` | carrier name |
| `Carrier` | `share` | market share fraction (all carriers must sum to 1) |

**CLI:**

```bash
urban-dollop generate-demand data/
urban-dollop generate-demand --outdir results/ data/
```

Reads `zones.gpkg`, `depots.gpkg`, `carrier_shares.csv`, and `skim_time.mtx` (or `.gz`)
from `data/`. Writes `parcel_demand.csv` to the current directory by default.

---

### Parcel demand generation — ordered logit formulation

For contexts where zone-level population and an urbanization classification are
available, the HARMONY v3 ordered logit formulation can be used instead.

```python
from urban_dollop import Zone, Depot, Carrier, SkimMatrix, generate_logit_demand, LogitDemandConfig

zones = Zone.from_file("zones.gpkg")   # must include population and urbanization_level columns
depots = Depot.from_file("depots.gpkg")
carriers = Carrier.from_file("carrier_shares.csv")
skim = SkimMatrix.from_file("skim_time.mtx", zones)

demands = generate_logit_demand(zones, depots, carriers, skim,
    config=LogitDemandConfig(
        beta_urbanization={1: -0.5, 2: -0.3, 3: 0.0, 4: 0.2, 5: 0.4},
        mu_thresholds=[-1.5, 0.5, 1.5, 2.2, 2.8, 3.3, 4.2, 5.0],
    ),
)
```

The logit model computes expected monthly B2C parcels per person using an ordered
logit over urbanization level, then converts to daily demand and multiplies by
zone population. It returns the same `list[ParcelDemand]` as the linear formulation.

**Zone fields required by the logit formulation:**

| field | type | description |
|---|---|---|
| `population` | `float` | total resident population |
| `urbanization_level` | `int` | urbanization class (arbitrary integer scale; must match keys in `beta_urbanization`) |

**`LogitDemandConfig` parameters:**

| parameter | type | description |
|---|---|---|
| `beta_urbanization` | `dict[int, float]` | linear predictor coefficient per urbanization level |
| `mu_thresholds` | `list[float]` | ordered logit threshold vector; length must equal `len(parcel_levels) - 1` |
| `parcel_levels` | `list[int]` | parcel count categories (default: `[0, 1, 2, 3, 4, 5, 10, 15, 20]`) |
| `monthly_to_daily_divisor` | `float` | divides monthly expected demand to obtain daily (default: `60.0`) |
| `calibration_target` | `float \| None` | optional aggregate scaling, same semantics as the linear formulation |

Parameters are estimated from survey data. Dutch estimates from HARMONY v3
(de Bok et al. 2025) may be used as a prior when local data are not available.

**Via `urban-dollop.toml`:**

```toml
[parcel_demand_logit]
monthly_to_daily_divisor = 60.0
mu_thresholds = [-1.5, 0.5, 1.5, 2.2, 2.8, 3.3, 4.2, 5.0]
# calibration_target = 50000

[parcel_demand_logit.beta_urbanization]
# TOML keys are strings; they are coerced to integers automatically
"1" = -0.5
"2" = -0.3
"3" = 0.0
"4" = 0.2
"5" = 0.4
```

---

### Parcel delivery scheduling

Schedule demand into vehicle tours.

```python
from urban_dollop import Depot, ParcelDemand, SkimMatrix, Vehicle, schedule_parcel_deliveries

depots = Depot.from_file("depots.gpkg")
vehicles = Vehicle.from_file("vehicles.csv")
skim = SkimMatrix.from_file("skim_time.mtx", zones)
demands = ParcelDemand.from_file("parcel_demand.csv")

trips = schedule_parcel_deliveries(demands, depots, vehicles, skim)
```

`trips` is a `list[DeliveryTrip]` — one record per leg within a tour:

| field | type | description |
|---|---|---|
| `tour_id` | `int` | unique tour identifier |
| `trip_id` | `int` | sequential leg position within the tour |
| `depot_id` | `int` | depot the tour departs from and returns to |
| `carrier` | `str` | carrier operating the tour |
| `origin_zone_id` | `int` | zone at the start of this leg |
| `destination_zone_id` | `int` | zone at the end of this leg |
| `n_parcels` | `int` | parcels delivered at this stop (0 for the return leg) |
| `vehicle_id` | `int` | vehicle type assigned to this tour |

**Save to CSV:**

```python
DeliveryTrip.to_file(trips, "delivery_trips.csv")
```

**Vehicle types — `vehicles.csv`:**

| field | type | description |
|---|---|---|
| `vehicle_id` | `int` | unique vehicle type identifier |
| `name` | `str` | vehicle type label |
| `max_parcels` | `int` | maximum parcel capacity |

The scheduler assigns the smallest vehicle whose capacity fits the tour load.

**CLI:**

```bash
urban-dollop schedule-deliveries data/
urban-dollop schedule-deliveries --outdir results/ data/
```

Reads `zones.gpkg`, `depots.gpkg`, `carrier_shares.csv`, `vehicles.csv`,
`skim_time.mtx` (or `.gz`), and `parcel_demand.csv` from `data/`.
Writes `delivery_trips.csv` to the current directory by default.
