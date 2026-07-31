# DAX Measures — Power BI Weather Analytics Dashboard

Complete library of production-ready DAX measures for the Power BI Weather ETL Dashboard.
All measures assume a Star Schema with relationships:
- `dim_date[date_key]` → `fact_weather_metrics[date_key]` (Many-to-One)
- `dim_city[city_id]`  → `fact_weather_metrics[city_id]`  (Many-to-One)

---

## Base Measures

```dax
-- Total hourly observation records
Total Records =
COUNTROWS(fact_weather_metrics)

-- Current average temperature (respects all slicers)
Avg Temperature =
AVERAGE(fact_weather_metrics[temperature_c])

-- Current average humidity
Avg Humidity =
AVERAGE(fact_weather_metrics[relative_humidity])

-- Total precipitation
Total Precipitation =
SUM(fact_weather_metrics[precipitation_mm])

-- Average wind speed
Avg Wind Speed =
AVERAGE(fact_weather_metrics[wind_speed_kmh])
```

---

## Time Intelligence Measures

```dax
-- Year-to-date average temperature
Avg Temp YTD =
TOTALYTD(
    AVERAGE(fact_weather_metrics[temperature_c]),
    dim_date[full_date]
)

-- Month-to-date average temperature
Avg Temp MTD =
TOTALMTD(
    AVERAGE(fact_weather_metrics[temperature_c]),
    dim_date[full_date]
)

-- 7-day rolling average temperature
7D Moving Avg Temp =
CALCULATE(
    AVERAGE(fact_weather_metrics[temperature_c]),
    DATESINPERIOD(
        dim_date[full_date],
        MAX(dim_date[full_date]),
        -7,
        DAY
    )
)

-- 30-day rolling average temperature
30D Moving Avg Temp =
CALCULATE(
    AVERAGE(fact_weather_metrics[temperature_c]),
    DATESINPERIOD(
        dim_date[full_date],
        MAX(dim_date[full_date]),
        -30,
        DAY
    )
)

-- Month-over-Month % change in average temperature
MoM Temp Change % =
VAR PrevMonth =
    CALCULATE(
        AVERAGE(fact_weather_metrics[temperature_c]),
        DATEADD(dim_date[full_date], -1, MONTH)
    )
VAR CurrMonth =
    AVERAGE(fact_weather_metrics[temperature_c])
RETURN
    DIVIDE(CurrMonth - PrevMonth, ABS(PrevMonth), 0)

-- Month-over-Month % change in average humidity
MoM Humidity Change % =
VAR PrevMonth =
    CALCULATE(
        AVERAGE(fact_weather_metrics[relative_humidity]),
        DATEADD(dim_date[full_date], -1, MONTH)
    )
VAR CurrMonth =
    AVERAGE(fact_weather_metrics[relative_humidity])
RETURN
    DIVIDE(CurrMonth - PrevMonth, ABS(PrevMonth), 0)
```

---

## Anomaly Detection Measures

```dax
-- Correctly scoped temperature anomaly flag
-- Uses CALCULATE with ALL(dim_date) to compute global std dev across ALL dates,
-- avoiding incorrect filter-context collapse in a time-sliced report page.
Temp Anomaly Flag =
VAR OverallStdDev =
    CALCULATE(
        STDEV.P(fact_weather_metrics[temperature_c]),
        ALL(dim_date)
    )
VAR OverallAvg =
    CALCULATE(
        AVERAGE(fact_weather_metrics[temperature_c]),
        ALL(dim_date)
    )
VAR CurrentTemp =
    AVERAGE(fact_weather_metrics[temperature_c])
RETURN
    IF(
        CurrentTemp > OverallAvg + (2 * OverallStdDev),
        "🔴 High Spike",
        IF(
            CurrentTemp < OverallAvg - (2 * OverallStdDev),
            "🔵 Low Drop",
            "✅ Normal"
        )
    )

-- Humidity anomaly flag (same scoping pattern)
Humidity Anomaly Flag =
VAR OverallStdDev =
    CALCULATE(STDEV.P(fact_weather_metrics[relative_humidity]), ALL(dim_date))
VAR OverallAvg =
    CALCULATE(AVERAGE(fact_weather_metrics[relative_humidity]), ALL(dim_date))
VAR CurrentVal =
    AVERAGE(fact_weather_metrics[relative_humidity])
RETURN
    IF(CurrentVal > OverallAvg + (2 * OverallStdDev), "🔴 High", "✅ Normal")
```

---

## City Ranking Measures

```dax
-- Rank cities by average temperature (hottest = Rank 1)
City Temp Rank =
RANKX(
    ALL(dim_city[city_name]),
    CALCULATE(AVERAGE(fact_weather_metrics[temperature_c])),
    ,
    DESC,
    DENSE
)

-- Rank cities by total precipitation
City Rain Rank =
RANKX(
    ALL(dim_city[city_name]),
    CALCULATE(SUM(fact_weather_metrics[precipitation_mm])),
    ,
    DESC,
    DENSE
)
```

---

## Formatting Helpers

```dax
-- Temp with degree symbol for card visuals
Avg Temp Display =
FORMAT([Avg Temperature], "0.0") & "°C"

-- MoM change as styled % string
MoM Temp Display =
VAR Pct = [MoM Temp Change %]
RETURN
    IF(Pct >= 0, "▲ " & FORMAT(Pct, "0.0%"), "▼ " & FORMAT(ABS(Pct), "0.0%"))
```

---

## Implementation Notes

- **Always test `Temp Anomaly Flag`** manually in Power BI after connecting the database.
  Apply a city slicer and a date range slicer simultaneously, then verify the flag value
  shifts appropriately — confirming `ALL(dim_date)` correctly escapes the date filter context.
- Replace placeholder RESULT numbers in the STAR interview guide with real measured values
  after running the pipeline for at least 24 hours.
- For **Incremental Refresh** (future scale): When fact table exceeds ~1M rows, enable
  Power BI incremental refresh policy on `fact_weather_metrics` partitioned by `timestamp_utc`.
