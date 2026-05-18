# urban-dollop

A Python package for urban freight simulation based on the MASS-GT multi-agent model.

---

## Domain Model

`FileModel` is the base for any domain entity that can be loaded from a file. It provides
`from_file()`, which dispatches to the right reader based on file extension and handles
column remapping. `GeoEntity` is reserved for entities whose geometry is structurally
meaningful (network links, nodes) — Zone and Depot do not inherit from it because their
spatial reference is `zone_id`, not a coordinate.

`Parcel` is the primary output of the pipeline: produced by parcel demand generation and
consumed by every downstream module.

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
        +carrier str
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
        +carrier str
        +vehicle_type int
        +n_parcels int
    }

    class SkimMatrix {
        +data ndarray
        +n_zones int
        +get(from_zone_id, to_zone_id) int
        +from_file(path, zones) SkimMatrix
    }

    SkimMatrix --> Zone : zones
```
