# Power BI Setup Guide — Dashboard Configuration & DAX

Complete instructions for connecting Power BI Desktop to the ETL database,
building the Star Schema data model, and configuring the live dashboard.

---

## Part 1: Connect Power BI to the Database

### Option A — SQLite (Local Development)

1. Open **Power BI Desktop**
2. Click **Get Data** → **More** → search **ODBC**
3. If you don't have SQLite ODBC driver:
   - Download **SQLite ODBC Driver** from [sqliteodbc.com](http://www.ch-werner.de/sqliteodbc/)
   - Install and restart Power BI Desktop
4. In ODBC dialog → **DSN**: create a new DSN pointing to `data/warehouse.db`
5. Click **OK** → select tables: `dim_date`, `dim_city`, `fact_weather_metrics`
6. Click **Load**

> **Tip**: Alternatively use **Python script** as data source and load with `pandas.read_sql()` — this avoids the ODBC driver requirement.

### Option B — PostgreSQL (Neon / Supabase — Recommended for Auto-Refresh)

1. Open **Power BI Desktop**
2. Click **Get Data** → **Database** → **PostgreSQL database**
3. Enter:
   - **Server**: `ep-cool-name-123456.us-east-2.aws.neon.tech`
   - **Database**: `neondb`
4. Click **OK** → enter credentials (username + password from Neon dashboard)
5. Select tables: `dim_date`, `dim_city`, `fact_weather_metrics`
6. Also select views: `vw_daily_city_summary`, `vw_latest_city_snapshot`
7. Click **Load**

---

## Part 2: Build the Star Schema Data Model

### Step 1 — Open Model View
Click the **Model** icon (3rd icon in left sidebar) in Power BI Desktop.

### Step 2 — Create Relationships
Drag and drop to create these relationships:

| From (Many side) | To (One side) | Cardinality | Cross-filter |
|---|---|---|---|
| `fact_weather_metrics[date_key]` | `dim_date[date_key]` | Many-to-One | Single (dim → fact) |
| `fact_weather_metrics[city_id]` | `dim_city[city_id]` | Many-to-One | Single (dim → fact) |

> ⚠️ **Critical**: Set cross-filter direction to **Single** on both relationships.
> Do NOT enable Bidirectional — it causes filter ambiguity in multi-slicer reports.

### Step 3 — Verify Model Layout
Your model should look like a star:
```
   dim_date ──────────────────────────────┐
                                          │
                              fact_weather_metrics
                                          │
   dim_city ──────────────────────────────┘
```

---

## Part 3: Create DAX Measures

Right-click `fact_weather_metrics` → **New measure** → paste each measure below.

See [dax_measures.md](../dax/dax_measures.md) for the complete library. Key measures to add first:

```dax
Avg Temperature = AVERAGE(fact_weather_metrics[temperature_c])

Total Records = COUNTROWS(fact_weather_metrics)

7D Moving Avg Temp =
CALCULATE(
    AVERAGE(fact_weather_metrics[temperature_c]),
    DATESINPERIOD(dim_date[full_date], MAX(dim_date[full_date]), -7, DAY)
)

Avg Temp YTD =
TOTALYTD(AVERAGE(fact_weather_metrics[temperature_c]), dim_date[full_date])

MoM Temp Change % =
VAR PrevMonth = CALCULATE(AVERAGE(fact_weather_metrics[temperature_c]), DATEADD(dim_date[full_date], -1, MONTH))
VAR CurrMonth = AVERAGE(fact_weather_metrics[temperature_c])
RETURN DIVIDE(CurrMonth - PrevMonth, ABS(PrevMonth), 0)

Temp Anomaly Flag =
VAR OverallStdDev = CALCULATE(STDEV.P(fact_weather_metrics[temperature_c]), ALL(dim_date))
VAR OverallAvg = CALCULATE(AVERAGE(fact_weather_metrics[temperature_c]), ALL(dim_date))
VAR CurrentTemp = AVERAGE(fact_weather_metrics[temperature_c])
RETURN IF(CurrentTemp > OverallAvg + (2 * OverallStdDev), "🔴 High Spike",
       IF(CurrentTemp < OverallAvg - (2 * OverallStdDev), "🔵 Low Drop", "✅ Normal"))
```

---

## Part 4: Build the Dashboard

### Recommended Report Pages

#### Page 1 — Executive Overview
| Visual | Fields |
|---|---|
| Card | `Avg Temperature` |
| Card | `Total Records` |
| Card | `Avg Humidity` |
| Map / Filled Map | Location: `dim_city[city_name]`, Values: `Avg Temperature` |
| Slicer | `dim_city[city_name]` (multi-select) |
| Slicer | `dim_date[full_date]` (date range) |

#### Page 2 — Temperature Trend Analysis
| Visual | Fields |
|---|---|
| Line Chart | X-axis: `dim_date[full_date]`, Values: `Avg Temperature`, `7D Moving Avg Temp` |
| Line Chart | X-axis: `dim_date[full_date]`, Values: `Avg Temp YTD` |
| Column Chart | X-axis: `dim_date[month_name]`, Values: `MoM Temp Change %` |
| Table | City, Date, Temperature, Anomaly Flag |

#### Page 3 — City Comparison
| Visual | Fields |
|---|---|
| Clustered Bar | Category: `dim_city[city_name]`, Values: `Avg Temperature` |
| Clustered Bar | Category: `dim_city[city_name]`, Values: `Total Precipitation` |
| Matrix | Rows: `dim_city[city_name]`, Columns: `dim_date[month_name]`, Values: `Avg Temperature` |
| KPI Card | `Temp Anomaly Flag` with conditional formatting |

#### Page 4 — Data Freshness Monitor
| Visual | Fields |
|---|---|
| Card | Latest `timestamp_utc` (use `MAX(fact_weather_metrics[timestamp_utc])`) |
| Card | `Total Records` |
| Table | Last 10 records with all metric columns |

---

## Part 5: Configure Scheduled Refresh (Power BI Service)

### Step 1 — Publish to Power BI Service
1. In Power BI Desktop → **Home** → **Publish**
2. Select your workspace → Click **Publish**
3. Open **Power BI Service** (app.powerbi.com)

### Step 2 — Configure Data Source Credentials
1. Go to your dataset → **Settings** (⚙️ icon)
2. Under **Data source credentials** → click **Edit credentials**
3. Enter your PostgreSQL credentials (Neon/Supabase)

### Step 3 — Set Refresh Schedule
1. Under **Scheduled refresh** → toggle **On**
2. Set frequency: **Hourly** (or **Daily** depending on your plan)
3. Set timezone to match your local timezone
4. Click **Apply**

> **Note**: Power BI Free allows 8 refreshes/day. Power BI Pro allows 48 refreshes/day (every 30 min).

---

## Part 6: Verify Anomaly Flag DAX Measure

After building the dashboard, manually test the `Temp Anomaly Flag` measure:

1. Create a **Table visual** with columns: `city_name`, `timestamp_utc`, `temperature_c`, `Temp Anomaly Flag`
2. Apply a **city slicer** (e.g., select only Dubai)
3. Check the flag values — Dubai should show "🔴 High Spike" on its hottest summer hours
4. Apply a **date slicer** (e.g., restrict to 1 month)
5. Verify the flag values **do NOT change** — since `ALL(dim_date)` removes the date filter from the std dev calculation, the threshold remains globally stable

If the flag values change when you move the date slicer, the `CALCULATE(..., ALL(dim_date))` is not working correctly — re-check the measure definition.
