# Power BI dashboard: build guide

Data source: `data/processed/weather_daily.csv` and `data/processed/weather_forecast.csv`
(created by `python src/run_pipeline.py`). You can also connect Power BI straight to MySQL:
**Get data → MySQL database → localhost / weather_db**.

## 1. Import and model

1. **Get data → Text/CSV** → import both CSV files.
2. In Power Query set `date` to **Date**, temperature/rain/wind columns to **Decimal number**, `is_rainy_day`, `month`, `year`, `week` to **Whole number**.
3. Select `month_name` → **Sort by column → month**.
4. In **Model view**, set `latitude` and `longitude` data category to **Latitude / Longitude**, and `city` to **City**.

## 2. Measures

```DAX
Avg Temp (°C) = AVERAGE ( weather_daily[temp_mean_c] )

Max Temp (°C) = MAX ( weather_daily[temp_max_c] )

Min Temp (°C) = MIN ( weather_daily[temp_min_c] )

Total Rain (mm) = SUM ( weather_daily[precipitation_mm] )

Rainy Days = SUM ( weather_daily[is_rainy_day] )

Avg Humidity (%) = AVERAGE ( weather_daily[humidity_pct] )

Extreme Heat Days =
CALCULATE ( COUNTROWS ( weather_daily ), weather_daily[temp_max_c] >= 40 )

Avg Sunshine (h) = AVERAGE ( weather_daily[sunshine_hours] )

Temp 7-Day Avg =
AVERAGEX (
    DATESINPERIOD ( weather_daily[date], MAX ( weather_daily[date] ), -7, DAY ),
    CALCULATE ( AVERAGE ( weather_daily[temp_mean_c] ) )
)

Hottest City =
FIRSTNONBLANK (
    TOPN ( 1, VALUES ( weather_daily[city] ), [Avg Temp (°C)], DESC ),
    1
)

Last Updated = "Data up to " & FORMAT ( MAX ( weather_daily[date] ), "dd mmm yyyy" )
```

## 3. Page 1: India Weather Overview

| Area | Visual | Fields |
|---|---|---|
| Top | 5 **Cards** | Avg Temp, Max Temp, Total Rain, Rainy Days, Extreme Heat Days |
| Left | **Map** | Latitude/Longitude, Bubble size: Total Rain, Tooltip: Avg Temp |
| Right | **Line chart** | X: date, Y: Temp 7-Day Avg, Legend: city |
| Bottom left | **Clustered column** | X: month_name, Y: Total Rain, Legend: season |
| Bottom right | **Matrix heatmap** | Rows: city, Columns: month_name, Values: Avg Temp (conditional formatting: blue → red) |
| Slicers | city, season, date range | |

## 4. Page 2: City Deep Dive

- **Slicer** for one city (single select).
- **Area chart**: temp_max_c and temp_min_c over date (shows daily range).
- **Donut chart**: share of days by heat_category.
- **Table**: Next 7 days from `weather_forecast` with conditional icons for rain.
- **Card**: Last Updated.

## 5. Refresh

Run `python src/run_pipeline.py` again, then press **Refresh** in Power BI. With MySQL as the source and `--mysql`, the dashboard updates with the newest data every time you refresh.

## 6. Screenshots

Save the file as `powerbi/Weather_Dashboard.pbix`, then add screenshots to `powerbi/screenshots/` and link them in the README.
