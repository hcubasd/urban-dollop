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
    }

    class Parcel {
        +parcel_id int
        +vehicle_type int
        +segment str
        +local_to_local bool
        +crowdshipping_eligible bool
        +fulfilment_type str
    }

    FileModel <|-- Zone
    FileModel <|-- Depot
    FileModel <|-- Carrier

    Depot *-- Zone : zone
    Depot *-- Carrier : carrier

    Parcel *-- Zone : origin_zone
    Parcel *-- Zone : destination_zone
    Parcel o-- Zone : locker_zone
    Parcel *-- Depot : depot
    Parcel *-- Carrier : carrier
```
