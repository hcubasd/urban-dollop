# urban-dollop

urban-dollop is a Python library that extracts and packages the mathematical models
from [MASS-GT](https://github.com/orgs/mass-gt/repositories) — a multi-agent urban
freight simulation system originally developed at TU Delft for the Dutch Randstad region.
The models are reimplemented as a transparent, installable Python pipeline intended for
academic research and reproducible urban logistics studies.

The primary case study is Joinville, Santa Catarina, Brazil (43 traffic analysis zones).
The primary novel contribution is the introduction of road grade as a dimension in
emission accounting, enabling topographically accurate estimates in hilly cities.

---

## Usage

### Parcel demand generation

Estimate the daily parcel delivery demand for a study area from zonal population and
employment data.

```python
from urban_dollop import Zone, Depot, Carrier, SkimMatrix, generate_parcel_demand

zones    = Zone.from_file("zones.gpkg")
depots   = Depot.from_file("depots.gpkg")
carriers = Carrier.from_file("carrier_shares.csv")
skim     = SkimMatrix.from_file("skim_time.mtx", zones)

demands  = generate_parcel_demand(zones, depots, carriers, skim)
```

`demands` is a `list[ParcelDemand]` — one record per unique
(destination zone, depot, vehicle type) combination:

| field | type | description |
|---|---|---|
| `destination_zone_id` | `int` | zone ID of the delivery address |
| `depot_id` | `int` | depot that handles this flow |
| `vehicle_type` | `int` | vehicle type code (default `7` = van) |
| `n_parcels` | `int` | number of parcels in this flow |

The origin zone of each flow is implicit — it is always the zone of the depot.

**Save to CSV** (join to your zones layer in QGIS or ArcGIS on `destination_zone_id`
to map parcels delivered per zone):

```python
ParcelDemand.to_file(demands, "parcel_demand.csv")
```

**Calibration — via `urban-dollop.toml`:**

Place an `urban-dollop.toml` in your working directory to set calibration parameters
without touching code:

```toml
[parcel_demand]
parcels_per_household = 0.2054  # B2C daily deliveries per household
parcels_per_employee  = 0.0     # B2B daily deliveries per employee
delivery_success_b2c  = 0.75    # first-attempt success rate, residential
delivery_success_b2b  = 0.95    # first-attempt success rate, commercial
default_vehicle_type  = 7       # 7 = van
random_seed           = 42
```

**Calibration — programmatic override:**

Pass a `ParcelDemandConfig` to override TOML values in code:

```python
from urban_dollop import ParcelDemandConfig

demands = generate_parcel_demand(
    zones, depots, carriers, skim,
    config=ParcelDemandConfig(
        parcels_per_household = 0.178,
        parcels_per_employee  = 0.029,
        delivery_success_b2c  = 0.80,
        delivery_success_b2b  = 0.95,
        default_vehicle_type  = 7,
    ),
)
```

Programmatic values take precedence over TOML. Missing fields fall back to TOML.
Pydantic raises if a required field is absent from both sources.

**Column mapping** — when your files use different column names:

```python
zones = Zone.from_file("zones.gpkg", columns={
    "zone_id":    "id",
    "households": "hh_count",
    "employment": "jobs",
})

carriers = Carrier.from_file("shares.csv", columns={
    "name":  "courier",
    "share": "market_share",
})
```

Canonical column names:

| model | field | description |
|---|---|---|
| `Zone` | `zone_id` | unique integer zone identifier |
| `Zone` | `municipality` | municipality name |
| `Zone` | `households` | household count |
| `Zone` | `employment` | employee count |
| `Depot` | `depot_id` | unique integer depot identifier |
| `Depot` | `zone_id` | zone the depot is located in |
| `Depot` | `carrier` | carrier name (must match `Carrier.name`) |
| `Carrier` | `name` | carrier name |
| `Carrier` | `share` | market share fraction (all carriers must sum to 1) |

---

## Mathematical models

The following models are extracted from MASS-GT's `parcel_dmnd` module and implemented
in `generate_parcel_demand()`.

### Parcel demand generation

#### Zonal demand

The number of parcel flows destined for zone $z$ on an average weekday:

$$D_z = \left\lfloor \frac{H_z \cdot r_{HH}}{s_{B2C}} + \frac{E_z \cdot r_E}{s_{B2B}} \right\rceil$$

| symbol | `ParcelDemandConfig` field | description |
|---|---|---|
| $H_z$ | — | households in zone $z$ |
| $E_z$ | — | employees in zone $z$ |
| $r_{HH}$ | `parcels_per_household` | B2C parcels per household per day |
| $r_E$ | `parcels_per_employee` | B2B parcels per employee per day |
| $s_{B2C}$ | `delivery_success_b2c` | first-attempt delivery success rate, residential |
| $s_{B2B}$ | `delivery_success_b2b` | first-attempt delivery success rate, commercial |

The success rates correct for failed first-attempt deliveries: the generated volume
reflects shipments sent, not deliveries completed.

#### Carrier split

Total zonal demand is distributed across carriers by market share:

$$D_{z,k} = \left\lfloor \sigma_k \cdot D_z \right\rceil$$

where $\sigma_k$ is the market share of carrier $k$ (`Carrier.share`), and
$\sum_k \sigma_k = 1$.

#### Depot assignment

Each (zone, carrier) flow is assigned to the nearest depot of that carrier by
travel time from the depot zone to the destination zone:

$$\delta(z, k) = \underset{n \in \mathcal{N}_k}{\arg\min}\ t(n_{\text{zone}}, z)$$

where $\mathcal{N}_k$ is the set of depots operated by carrier $k$ and
$t(n_{\text{zone}}, z)$ is the travel time in seconds from the depot's zone to
zone $z$, read from the pre-computed skim matrix.

#### Aggregation

Flows that share the same destination zone and depot (possible when rounding produces
identical assignments across carriers at the same depot) are summed:

$$F_{z,n} = \sum_{k\,:\,\delta(z,k) = n} D_{z,k}$$

Each resulting $(z, n)$ pair with $F_{z,n} > 0$ becomes one `ParcelDemand` record.

---

## Domain model

```mermaid
classDiagram
    class Zone {
        +zone_id int
        +municipality str
        +households int
        +employment int
        +from_file(path, columns) list
    }

    class Carrier {
        +name str
        +share float
        +from_file(path, columns) list
    }

    class Depot {
        +depot_id int
        +zone_id int
        +carrier str
        +from_file(path, columns) list
    }

    class ParcelDemand {
        +destination_zone_id int
        +depot_id int
        +vehicle_type int
        +n_parcels int
    }

    class SkimMatrix {
        +data ndarray
        +n_zones int
        +get(from_zone_id, to_zone_id) int
        +from_file(path, zones) SkimMatrix
    }

    Depot --> Zone : zone_id
    Depot --> Carrier : carrier
    ParcelDemand --> Zone : destination_zone_id
    ParcelDemand --> Depot : depot_id
    SkimMatrix --> Zone : zones
```
