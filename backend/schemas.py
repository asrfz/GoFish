from pydantic import BaseModel
from typing import Optional
from enum import Enum


class Species(str, Enum):
    WALLEYE = "walleye"
    TROUT = "trout"
    BASS = "bass"


class HydrometricData(BaseModel):
    station_id: str
    station_name: str
    latitude: float
    longitude: float
    discharge: Optional[float] = None  # m³/s
    water_level: Optional[float] = None  # meters


class WeatherData(BaseModel):
    temperature: float  # °C
    pressure: float  # hPa
    wind_speed: float  # km/h
    is_pressure_falling: bool


class BiteScore(BaseModel):
    species: Species
    score: int  # 0-100
    status: str  # "Great", "Good", "Fair", "Poor"
    reasoning: str


class StationForecast(BaseModel):
    station_id: str
    station_name: str
    latitude: float
    longitude: float
    discharge: Optional[float]
    water_level: Optional[float]
    weather: WeatherData
    bite_scores: list[BiteScore]


class ForecastResponse(BaseModel):
    timestamp: str
    stations: list[StationForecast]


class FishingAccessPoint(BaseModel):
    id: str
    name: str
    latitude: float
    longitude: float
    access_type: str  # "boat_launch", "shoreline", "dock"
