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
Returns a `list[ParcelDemand]` — one record per `(destination_zone, depot)` pair:

| field | type | description |
|---|---|---|
| `destination_zone_id` | `int` | zone receiving the parcels |
| `depot_id` | `int` | depot handling this flow |
| `n_parcels` | `int` | number of parcels |

Two formulations are available. They differ in what zone attributes they require;
everything else (depots, carrier shares, skim matrix, output format) is identical.

#### Linear formulation

Use `generate_parcel_demand` when your zone data has household and employment
counts. Demand is a linear rate applied per household and per employee.

```python
from urban_dollop import Zone, Depot, Carrier, SkimMatrix
from urban_dollop import generate_parcel_demand, ParcelDemandConfig, ParcelDemand

zones = Zone.from_file("zones.gpkg")
depots = Depot.from_file("depots.gpkg")
carriers = Carrier.from_file("carrier_shares.csv")
skim = SkimMatrix.from_file("skim_time.mtx", zones)

demands = generate_parcel_demand(zones, depots, carriers, skim)
ParcelDemand.to_file(demands, "parcel_demand.csv")
```

**Input file fields:**

| file | field | type | description |
|---|---|---|---|
| `zones.gpkg` | `zone_id` | `int` | unique zone identifier |
| `zones.gpkg` | `households` | `float` | household count |
| `zones.gpkg` | `employment` | `float` | employee count |
| `depots.gpkg` | `depot_id` | `int` | unique depot identifier |
| `depots.gpkg` | `zone_id` | `int` | zone the depot is located in |
| `depots.gpkg` | `carrier` | `str` | carrier name (must match `Carrier.name`) |
| `carrier_shares.csv` | `name` | `str` | carrier name |
| `carrier_shares.csv` | `share` | `float` | market share fraction (all must sum to 1.0) |

If your files use different column names, pass a mapping:

```python
zones = Zone.from_file("zones.gpkg", columns={"zone_id": "id", "households": "hh"})
```

Configure via `urban-dollop.toml`:

```toml
[parcel_demand]
parcels_per_household = 0.2054
parcels_per_employee = 0.0
delivery_success_b2c = 0.75
delivery_success_b2b = 0.95
# calibration_target = 50000
```

Or pass a config object directly:

```python
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
```

`calibration_target` is the total daily parcels expected in the study area. When
set, all zone demands are scaled proportionally so the total matches; the spatial
distribution is preserved.

**CLI:**

```bash
urban-dollop generate-demand data/
urban-dollop generate-demand --outdir results/ data/
```

Reads `zones.gpkg`, `depots.gpkg`, `carrier_shares.csv`, and `skim_time.mtx`
(or `.mtx.gz`) from `data/`. Writes `parcel_demand.csv` to the current directory
by default. Config is read from the `[parcel_demand]` section of
`urban-dollop.toml`.

#### Ordered logit formulation

Use `generate_logit_demand` when your zone data has population and an integer
urbanization classification. Demand is derived from an ordered logit over
urbanization level following the HARMONY v3 formulation.

The model computes an expected number of B2C parcels per person per month:

$$P(X \leq p_k \mid z) = \frac{1}{1 + e^{\,\eta_z - \mu_k}}, \qquad \eta_z = \beta_{\text{urb}(z)}$$

`mu_thresholds` are the ordered cut-points $\mu_k$, one per boundary between adjacent
parcel levels. `parcel_levels` defines those discrete counts $p_k$ — the default
`[0, 1, 2, 3, 4, 5, 10, 15, 20]` matches the HARMONY v3 survey response categories,
but you can supply a different list if your survey used different options.
`len(mu_thresholds)` must equal `len(parcel_levels) - 1`. Expected monthly parcels per
person are multiplied by zone population and divided by `monthly_to_daily_divisor`
(default 60) to get daily demand.

The logit formulation only requires `zone_id`, `population`, and `urbanization_level`
from the zone file — `households` and `employment` are not needed and do not have to
be present. Use `columns=` to map your file's column names:

| file | field | type | description |
|---|---|---|---|
| `zones.gpkg` | `zone_id` | `int` | unique zone identifier |
| `zones.gpkg` | `population` | `float` | total resident population |
| `zones.gpkg` | `urbanization_level` | `int` | integer urbanization class |

```python
from urban_dollop import Zone, Depot, Carrier, SkimMatrix
from urban_dollop import generate_logit_demand, LogitDemandConfig, ParcelDemand

zones = Zone.from_file("zones.gpkg", columns={
    "population": "inwoners",
    "urbanization_level": "STED",
})
depots = Depot.from_file("depots.gpkg")
carriers = Carrier.from_file("carrier_shares.csv")
skim = SkimMatrix.from_file("skim_time.mtx", zones)

demands = generate_logit_demand(
    zones, depots, carriers, skim,
    config=LogitDemandConfig(
        beta_urbanization={1: 2.0, 2: 1.2, 3: 0.4, 4: -0.3, 5: -1.0},
        mu_thresholds=[-0.5, 1.0, 2.0, 2.8, 3.5, 4.0, 5.5, 7.0],
        calibration_target=50000,
        # parcel_levels defaults to [0, 1, 2, 3, 4, 5, 10, 15, 20] — override if
        # your survey used different response categories
    ),
)
ParcelDemand.to_file(demands, "parcel_demand.csv")
```

`beta_urbanization` and `mu_thresholds` are estimated from a household travel
survey. The Dutch estimates from HARMONY v3 (de Bok et al. 2025) can be used as
a prior when local survey data are not available. The urbanization coding only
needs to be a consistent set of integers — Dutch STED (1–5), EU DEGURBA (1–3),
or any national classification all work; you calibrate the betas to match.

Configure via `urban-dollop.toml` instead of passing a config object:

```toml
[parcel_demand_logit]
beta_urbanization = {1 = 2.0, 2 = 1.2, 3 = 0.4, 4 = -0.3, 5 = -1.0}
mu_thresholds = [-0.5, 1.0, 2.0, 2.8, 3.5, 4.0, 5.5, 7.0]
# parcel_levels = [0, 1, 2, 3, 4, 5, 10, 15, 20]
# calibration_target = 50000
```

**CLI:**

```bash
urban-dollop generate-demand --logit data/
urban-dollop generate-demand --logit --outdir results/ data/
```

Reads the same input files as the linear CLI. Config is read from the
`[parcel_demand_logit]` section of `urban-dollop.toml`.

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
