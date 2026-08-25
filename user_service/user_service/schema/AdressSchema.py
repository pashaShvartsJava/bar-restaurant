from pydantic import BaseModel, Field
from datetime import date



class AddressResponseDTO(BaseModel):
    city : str = Field(..., description="city")
    postal_code : int = Field(..., description="postal code")
    street : str = Field(..., description="street")
    house : int = Field(..., description="house number")
    apartment : int = Field(..., description="apartment number; not necessary")