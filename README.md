# Air Quality Health

Home Assistant custom integration to calculate the daily average of PM10 and PM2.5 per calendar day and count limit exceedances.

## Configure via UI

Go to `Settings -> Devices & Services -> Add Integration` and choose **Air Quality Health Norms**.

`pm10_norm` and `pm25_norm` are optional. Default values are `45` and `15` respectively.

## Sensors

- `sensor.air_quality_health_pm10_daily_average`
- `sensor.air_quality_health_pm2_5_daily_average`
- `sensor.air_quality_health_pm10_annual_average`
- `sensor.air_quality_health_pm2_5_annual_average`
- `sensor.air_quality_health_pm10_limit_exceedances`
- `sensor.air_quality_health_pm2_5_limit_exceedances`
