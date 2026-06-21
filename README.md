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

Estimates daily parcel delivery demand by zone and assigns each flow to a depot.
Two formulations are available; both accept the same depot, carrier, and skim
inputs and return the same `list[ParcelDemand]`.

**Shared inputs:**

```python
from urban_dollop import Zone, Depot, Carrier, SkimMatrix

depots = Depot.from_file("depots.gpkg")
carriers = Carrier.from_file("carrier_shares.csv")
skim = SkimMatrix.from_file("skim_time.mtx", zones)
```

**Output** — `list[ParcelDemand]`, one record per `(destination_zone, depot)` pair:

| field | type | description |
|---|---|---|
| `destination_zone_id` | `int` | zone receiving the parcels |
| `depot_id` | `int` | depot handling this flow |
| `n_parcels` | `int` | number of parcels |

```python
ParcelDemand.to_file(demands, "parcel_demand.csv")
```

Both formulations accept an optional `calibration_target` (total daily parcels
in the study area). When set, all zone demands are scaled proportionally so the
study-area total matches the target; the spatial distribution is preserved.

#### Linear formulation

Use `generate_parcel_demand` when your zone data has household and employment
counts. Demand is a linear rate applied per household and per employee:

```python
from urban_dollop import generate_parcel_demand, ParcelDemandConfig

zones = Zone.from_file("zones.gpkg")

demands = generate_parcel_demand(zones, depots, carriers, skim)
```

Configure via `urban-dollop.toml`:

```toml
[parcel_demand]
parcels_per_household = 0.2054
parcels_per_employee  = 0.0
delivery_success_b2c  = 0.75
delivery_success_b2b  = 0.95
# calibration_target = 50000
```

Or programmatically:

```python
demands = generate_parcel_demand(
    zones, depots, carriers, skim,
    config=ParcelDemandConfig(
        parcels_per_household=0.178,
        parcels_per_employee=0.029,
        delivery_success_b2c=0.80,
        delivery_success_b2b=0.95,
        calibration_target=50000, # optional
    ),
)
```

#### Ordered logit formulation

Use `generate_logit_demand` when your zone data has population and an
urbanization classification. Demand is derived from an ordered logit model over
urbanization level:

```python
from urban_dollop import generate_logit_demand, LogitDemandConfig

zones = Zone.from_file("zones.gpkg", columns={
    "zone_id": "id",
    "population": "inwoners",
    "urbanization_level": "STED",
})

demands = generate_logit_demand(
    zones, depots, carriers, skim,
    config=LogitDemandConfig(
        beta_urbanization={1: ..., 2: ..., 3: ..., 4: ..., 5: ...},
        mu_thresholds=[..., ..., ..., ..., ..., ..., ..., ...], # 8 values
        calibration_target=50000, # optional
    ),
)
```

`beta_urbanization` and `mu_thresholds` are estimated from a household travel
survey. Dutch estimates from HARMONY v3 (de Bok et al. 2025) can be used as a
prior when local survey data are not available.

**Canonical field names** — use the `columns` argument to `from_file` to map
your file's column names to these:

| model | field | description |
|---|---|---|
| `Zone` | `zone_id` | unique integer zone identifier |
| `Zone` | `households` | household count (linear) |
| `Zone` | `employment` | employee count (linear) |
| `Zone` | `population` | total resident population (logit) |
| `Zone` | `urbanization_level` | integer urbanization class (logit) |
| `Depot` | `depot_id` | unique integer depot identifier |
| `Depot` | `zone_id` | zone the depot is located in |
| `Depot` | `carrier` | carrier name (must match `Carrier.name`) |
| `Carrier` | `name` | carrier name |
| `Carrier` | `share` | market share fraction (all carriers must sum to 1) |

**CLI:**

```bash
urban-dollop generate-demand data/ # linear formulation
urban-dollop generate-demand --logit data/ # ordered logit formulation
urban-dollop generate-demand --outdir results/ data/
```

Reads `zones.gpkg`, `depots.gpkg`, `carrier_shares.csv`, and `skim_time.mtx` (or `.gz`)
from `data/`. Writes `parcel_demand.csv` to the current directory by default.
`--logit` reads config from the `[parcel_demand_logit]` section of `urban-dollop.toml`
instead of `[parcel_demand]`.

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
