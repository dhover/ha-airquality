# Air Quality Health

Home Assistant custom integration to calculate the daily average of PM10 and PM2.5 per calendar day and count limit exceedances.

## Configure via UI (recommended)

Go to `Settings -> Devices & Services -> Add Integration` and choose **Air Quality Health Norms**.

## Configuration

Add this to `configuration.yaml`:

```yaml
airquality_health:
  pm10_entity: sensor.pm10
  pm25_entity: sensor.pm25
  pm10_norm: 45
  pm25_norm: 15
```

`pm10_norm` and `pm25_norm` are optional. Default values are `45` and `15` respectively.

## Sensors

- `sensor.pm10_daggemiddelde` (PM10 daily average)
- `sensor.pm2_5_daggemiddelde` (PM2.5 daily average)
- `sensor.pm10_norm_overschrijdingen` (PM10 limit exceedances)
- `sensor.pm2_5_norm_overschrijdingen` (PM2.5 limit exceedances)
