WITH src AS (
  SELECT
    CAST(DeviceID AS NVARCHAR(MAX))          AS deviceId,
    CAST(temperature AS float)               AS temperature,
    CAST(humidity AS float)                  AS humidity,
    CAST(pressure AS float)                  AS pressure,
    CAST(device_ts AS bigint)                AS device_ts,
    CAST(rasptimestamp AS bigint)            AS rasptimestamp
  FROM "IoThub-aardbei"
)
SELECT
  deviceId,
  temperature,
  humidity,
  pressure,
  device_ts,
  rasptimestamp,
  System.Timestamp AS stored_ts
INTO "IoT-database-bme280"
FROM src;
-- This query processes data from the source stream "IoThub-aardbei" and stores it into the target table "IoT-database-bme280".