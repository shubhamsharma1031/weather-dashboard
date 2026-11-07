-- ============================================================
-- Weather Dashboard: database setup (MySQL 8.0+)
-- ============================================================
CREATE DATABASE IF NOT EXISTS weather_db;
USE weather_db;

CREATE TABLE IF NOT EXISTS weather_daily (
    city              VARCHAR(40)  NOT NULL,
    date              DATE         NOT NULL,
    temp_max_c        DECIMAL(5,2),
    temp_min_c        DECIMAL(5,2),
    temp_mean_c       DECIMAL(5,2),
    precipitation_mm  DECIMAL(6,2),
    rain_mm           DECIMAL(6,2),
    wind_max_kmh      DECIMAL(6,2),
    humidity_pct      DECIMAL(5,2),
    sunshine_hours    DECIMAL(4,1),
    temp_range_c      DECIMAL(5,2),
    is_rainy_day      TINYINT,
    heat_category     VARCHAR(15),
    month             TINYINT,
    month_name        CHAR(3),
    year              SMALLINT,
    week              TINYINT,
    season            VARCHAR(15),
    latitude          DECIMAL(8,4),
    longitude         DECIMAL(8,4),
    PRIMARY KEY (city, date)          -- one row per city per day; enables upsert
);

CREATE TABLE IF NOT EXISTS weather_forecast (
    city              VARCHAR(40)  NOT NULL,
    date              DATE         NOT NULL,
    temp_max_c        DECIMAL(5,2),
    temp_min_c        DECIMAL(5,2),
    temp_mean_c       DECIMAL(5,2),
    precipitation_mm  DECIMAL(6,2),
    rain_mm           DECIMAL(6,2),
    wind_max_kmh      DECIMAL(6,2),
    sunshine_hours    DECIMAL(4,1),
    temp_range_c      DECIMAL(5,2),
    is_rainy_day      TINYINT,
    heat_category     VARCHAR(15),
    season            VARCHAR(15),
    loaded_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (city, date)
);

CREATE INDEX idx_daily_date   ON weather_daily (date);
CREATE INDEX idx_daily_season ON weather_daily (season);
