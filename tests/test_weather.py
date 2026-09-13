from gridops.ingestion.weather import (
    WeatherLocation,
    parse_hourly_weather_response,
)


def test_parse_hourly_weather_response() -> None:
    location = WeatherLocation(
        location_id="test_city",
        name="Test City",
        latitude=40.0,
        longitude=-75.0,
    )

    payload = {
        "hourly": {
            "time": [
                "2023-01-01T00:00",
                "2023-01-01T01:00",
            ],
            "temperature_2m": [5.0, 4.5],
            "relative_humidity_2m": [70, 72],
            "dew_point_2m": [0.0, 0.1],
            "apparent_temperature": [3.0, 2.5],
            "precipitation": [0.0, 0.1],
            "wind_speed_10m": [10.0, 12.0],
        }
    }

    result = parse_hourly_weather_response(
        payload,
        location=location,
    )

    assert len(result) == 2
    assert result["location_id"].iloc[0] == "test_city"
    assert result["temperature_2m"].iloc[0] == 5.0
    assert result["observed_at"].notna().all()