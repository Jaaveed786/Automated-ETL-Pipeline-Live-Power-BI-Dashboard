import pandera as pa
from pandera.typing import Series

class WeatherFactSchema(pa.DataFrameModel):
    """Pandera Data Schema model enforcing quality checks on weather metrics."""
    metric_id: Series[str] = pa.Field(unique=True, nullable=False)
    city_id: Series[str] = pa.Field(nullable=False)
    date_key: Series[int] = pa.Field(ge=20200101, le=20351231)
    timestamp_utc: Series[str] = pa.Field(nullable=False)
    timestamp_local: Series[str] = pa.Field(nullable=False)
    temperature_c: Series[float] = pa.Field(ge=-60.0, le=60.0, nullable=True)
    relative_humidity: Series[float] = pa.Field(ge=0.0, le=100.0, nullable=True)
    precipitation_mm: Series[float] = pa.Field(ge=0.0, le=500.0, nullable=True)
    wind_speed_kmh: Series[float] = pa.Field(ge=0.0, le=300.0, nullable=True)
    surface_pressure_hpa: Series[float] = pa.Field(ge=800.0, le=1200.0, nullable=True)

    class Config:
        strict = False
        coerce = True
