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
    class FileModel {
        +from_file(path, columns) list
    }

    class GeoEntity {
        +geometry
    }

    class Zone {
        +zone_id int
        +municipality str
        +households int
        +employment int
    }

    class Carrier {
        +carrier str
        +share float
    }

    class Depot {
        +depot_id int
        +zone_id int
        +carrier str
    }

    class Parcel {
        +parcel_id int
        +origin_zone int
        +destination_zone int
        +depot_id int
        +carrier str
        +vehicle_type int
        +locker_zone int
        +segment str
        +local_to_local bool
        +crowdshipping_eligible bool
        +fulfilment_type str
    }

    class SkimMatrix {
        +data ndarray
        +n_zones int
        +get(from_zone_id, to_zone_id) int
        +from_file(path, zones) SkimMatrix
    }

    FileModel <|-- Zone
    FileModel <|-- Depot
    FileModel <|-- Carrier
    FileModel <|-- Parcel

    SkimMatrix --> Zone : zones
```
