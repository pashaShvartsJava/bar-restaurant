from pydantic import BaseModel, Field
from datetime import date



class AddressResponseDTO(BaseModel):
    city : str = Field(..., description="city")
    postal_code : int = Field(..., description="postal code")
    street : str = Field(..., description="street")
    house : int = Field(..., description="house number")
    apartment : int | None= Field(..., description="apartment number; not necessary")

class AddressEditSchema(BaseModel):
    city: str | None = Field(..., description="city")
    postal_code: int | None= Field(..., description="postal code")
    street: str | None = Field(..., description="street")
    house: int | None = Field(..., description="house number")
    apartment: int | None = Field(..., description="apartment number; not necessary")