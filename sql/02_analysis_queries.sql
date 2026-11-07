-- ============================================================
-- Weather Dashboard: analysis queries (MySQL 8.0+)
-- ============================================================
USE weather_db;

-- Q1. Data coverage check: rows and date range per city
SELECT city, COUNT(*) AS days, MIN(date) AS first_day, MAX(date) AS last_day
FROM weather_daily
GROUP BY city
ORDER BY city;

-- Q2. City summary: average, hottest and coldest temperatures, total rain
SELECT
    city,
    ROUND(AVG(temp_mean_c), 1)      AS avg_temp_c,
    MAX(temp_max_c)                 AS hottest_c,
    MIN(temp_min_c)                 AS coldest_c,
    ROUND(SUM(precipitation_mm), 1) AS total_rain_mm,
    SUM(is_rainy_day)               AS rainy_days
FROM weather_daily
GROUP BY city
ORDER BY avg_temp_c DESC;

-- Q3. Monthly average temperature per city (feeds the trend chart)
SELECT
    city,
    year,
    month,
    month_name,
    ROUND(AVG(temp_mean_c), 1)      AS avg_temp_c,
    ROUND(SUM(precipitation_mm), 1) AS rain_mm
FROM weather_daily
GROUP BY city, year, month, month_name
ORDER BY city, year, month;

-- Q4. Season comparison across cities
SELECT
    season,
    city,
    ROUND(AVG(temp_max_c), 1)        AS avg_max_c,
    ROUND(AVG(humidity_pct), 1)      AS avg_humidity_pct,
    ROUND(SUM(precipitation_mm), 1)  AS rain_mm
FROM weather_daily
GROUP BY season, city
ORDER BY FIELD(season, 'Winter', 'Summer', 'Monsoon', 'Post-Monsoon'), avg_max_c DESC;

-- Q5. Extreme heat days (40 °C or more) per city
SELECT city, COUNT(*) AS extreme_heat_days, MAX(temp_max_c) AS peak_temp_c
FROM weather_daily
WHERE temp_max_c >= 40
GROUP BY city
ORDER BY extreme_heat_days DESC;

-- Q6. Top 5 hottest days for each city (window function)
SELECT city, date, temp_max_c
FROM (
    SELECT city, date, temp_max_c,
           ROW_NUMBER() OVER (PARTITION BY city ORDER BY temp_max_c DESC) AS rn
    FROM weather_daily
) ranked
WHERE rn <= 5
ORDER BY city, rn;

-- Q7. 7-day moving average temperature (smooths daily noise)
SELECT
    city,
    date,
    temp_mean_c,
    ROUND(AVG(temp_mean_c) OVER (PARTITION BY city ORDER BY date
          ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 2) AS temp_7day_avg
FROM weather_daily
ORDER BY city, date;

-- Q8. Day-to-day temperature change and the biggest sudden drops
SELECT city, date, temp_mean_c, change_c
FROM (
    SELECT city, date, temp_mean_c,
           ROUND(temp_mean_c - LAG(temp_mean_c) OVER (PARTITION BY city ORDER BY date), 2) AS change_c
    FROM weather_daily
) d
WHERE change_c IS NOT NULL
ORDER BY change_c
LIMIT 10;

-- Q9. Longest run of consecutive rainy days per city (gaps-and-islands)
WITH rainy AS (
    SELECT city, date,
           DATE_SUB(date, INTERVAL ROW_NUMBER() OVER (PARTITION BY city ORDER BY date) DAY) AS grp
    FROM weather_daily
    WHERE is_rainy_day = 1
),
streaks AS (
    SELECT city, grp, COUNT(*) AS streak_days, MIN(date) AS start_date, MAX(date) AS end_date
    FROM rainy
    GROUP BY city, grp
)
SELECT city, streak_days, start_date, end_date
FROM (
    SELECT streaks.*, ROW_NUMBER() OVER (PARTITION BY city ORDER BY streak_days DESC) AS rn
    FROM streaks
) s
WHERE rn = 1
ORDER BY streak_days DESC;

-- Q10. Rank cities by rainfall during the monsoon
SELECT
    city,
    ROUND(SUM(precipitation_mm), 1) AS monsoon_rain_mm,
    RANK() OVER (ORDER BY SUM(precipitation_mm) DESC) AS rain_rank
FROM weather_daily
WHERE season = 'Monsoon'
GROUP BY city;

-- Q11. Heat category distribution: share of days in each category per city
SELECT
    city,
    heat_category,
    COUNT(*) AS days,
    ROUND(COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY city) * 100, 1) AS pct_of_days
FROM weather_daily
GROUP BY city, heat_category
ORDER BY city, days DESC;

-- Q12. Next 7 days: forecast compared with the same month's historical average
SELECT
    f.city,
    f.date,
    f.temp_max_c                         AS forecast_max_c,
    h.avg_max_c                          AS usual_max_c,
    ROUND(f.temp_max_c - h.avg_max_c, 1) AS difference_c
FROM weather_forecast f
JOIN (
    SELECT city, month, ROUND(AVG(temp_max_c), 1) AS avg_max_c
    FROM weather_daily
    GROUP BY city, month
) h ON h.city = f.city AND h.month = MONTH(f.date)
ORDER BY f.city, f.date;
