from pydantic import BaseModel
from typing import Optional

class RestaurantForUserProfileDTO(BaseModel):
    slug: str
    restaurant_name: str
    city: Optional[str] = None
    short_description: Optional[str] = None
    photo_url: Optional[str] = None