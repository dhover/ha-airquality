# Air Quality Health

Home Assistant custom integratie om per kalenderdag het gemiddelde van PM10 en PM2.5 te berekenen en normoverschrijdingen te tellen.

## Configureren via UI (aanbevolen)

Ga naar `Instellingen -> Apparaten & Diensten -> Integratie toevoegen` en kies **Air Quality Health**.

## Configuratie

Voeg dit toe aan `configuration.yaml`:

```yaml
airquality_health:
  pm10_entity: sensor.pm10
  pm25_entity: sensor.pm25
  pm10_norm: 45
  pm25_norm: 15
```

`pm10_norm` en `pm25_norm` zijn optioneel. Standaardwaarden zijn respectievelijk `45` en `15`.

## Sensoren

- `sensor.pm10_daggemiddelde`
- `sensor.pm2_5_daggemiddelde`
- `sensor.pm10_norm_overschrijdingen`
- `sensor.pm2_5_norm_overschrijdingen`
