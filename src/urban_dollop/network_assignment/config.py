from pydantic import BaseModel


class NetworkAssignmentConfig(BaseModel):
    seed: int | None = None
