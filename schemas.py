from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import date

class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    email: str
    is_admin: bool = False

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class ProfileUpdate(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6)

class Coordinates(BaseModel):
    lat: float
    lon: float

class WeatherResponse(BaseModel):
    latitude: float
    longitude: float
    temperature_2m: list[float]
    relative_humidity_2m: list[float]
    precipitation: list[float]
    weather_code: list[int]
    evapotranspiration: list[float]
    wind_speed_10m: list[float]
    wind_direction_10m: list[float]
    soil_temperature_6cm: list[float]
    soil_moisture_0_to_1cm: list[float]

class PostCreate(BaseModel):
    title: str
    content: str

class CommentCreate(BaseModel):
    content: str
    post_id: int

class CropResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]

    class Config:
        from_attributes = True

class CropTaskResponse(BaseModel):
    id: int
    month: str
    task: str

    class Config:
        from_attributes = True

class TaskCreate(BaseModel):
    month: str
    task: str

class CropCreate(BaseModel):
    name: str
    description: Optional[str] = None
    tasks: List[TaskCreate]

class AgriculturalEventResponse(BaseModel):
    id: int
    name: str
    description: str
    date: date
    season: str
    category: str
    tasks: str

    class Config:
        from_attributes = True

class CommodityRequest(BaseModel):
    commodity: str
    currency: str

class CommodityPriceResponse(BaseModel):
    commodity: str
    currency: str
    price: float
    unit: str
    source: str