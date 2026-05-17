# urban-dollop

A Python package for urban freight simulation based on the MASS-GT multi-agent model.

---

## Domain Model

The library is built around five domain entities. `Zone` and `Depot` both extend `GeoEntity` because they have a physical location in the road network. `Carrier` and `Parcel` are non-spatial.

`Parcel` is the primary output of the pipeline: it is produced by parcel demand generation and consumed by every downstream module.

```mermaid
classDiagram
    class Zone {
        +zone_id: int
        +municipality: str
        +households: int
        +employment: int
    }

    class Depot {
        +depot_id: int
    }

    class Carrier {
        +name: str
        +share: float
    }

    class Parcel {
        +parcel_id: int
        +vehicle_type: int
        +locker_zone: int
        +segment: str
        +local_to_local: bool
        +crowdshipping_eligible: bool
        +fulfilment_type: str
    }

    Depot --> Zone : located in
    Depot --> Carrier : operated by
    Parcel --> Zone : origin / destination
    Parcel --> Depot : assigned to
    Parcel --> Carrier : delivered by
```
