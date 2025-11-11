# ChytrejsiObec Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

This custom integration allows you to integrate ChytrejsiObec (Chytřejší Obec) IoT sensors into Home Assistant. The platform is used by many Czech towns to monitor weather conditions, air quality, and rainfall.

## Features

- 🌡️ **Weather Monitoring**: Temperature, humidity, and atmospheric pressure
- 🌫️ **Air Quality**: PM1, PM2.5, and PM10 particulate matter sensors
- 🌧️ **Rainfall Tracking**: Current, hourly, daily, and 24-hour rainfall data
- 🔋 **Battery Monitoring**: Track device battery levels
- 🗺️ **Multi-location Support**: Monitor multiple stations in your town
- 🔄 **Automatic Updates**: Polls data every 5 minutes
- 📱 **Device Grouping**: Sensors are automatically grouped by device

## Supported Device Types

- **MeteoStation**: Weather stations with temperature, humidity, pressure, and air quality sensors
- **RainfallMeter**: Rainfall measurement devices

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/michalor/ha-chytrejsiobec`
6. Select category: "Integration"
7. Click "Add"
8. Find "ChytrejsiObec" in HACS and install it
9. Restart Home Assistant

### Manual Installation

1. Download the `custom_components/chytrejsiobec` folder
2. Copy it to your Home Assistant's `custom_components` directory
3. Restart Home Assistant

## Configuration

### Through the UI (Recommended)

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "ChytrejsiObec"
4. Enter your configuration:
   - **API Token**: Your town's subdomain (e.g., `townname.chytrejsiobec.cz`)
   - **Name** (optional): Friendly name for your integration
   - **Device Classes** (optional): Comma-separated list (default: `RainfallMeter,MeteoStation`)

### Finding Your API Token

Your API token is typically your town's subdomain in the format: `townname.chytrejsiobec.cz`

Examples:
- Řeka: `reka.chytrejsiobec.cz`
- Other towns: Check your local ChytrejsiObec portal

To verify your token works, you can test it with:
```bash
curl -H "Authorization: reka.chytrejsiobec.cz" \
  "https://api.chytrejsiobec.cz/api/device/list?status=OK&deviceClass=MeteoStation"
```

## Entities Created

For each **MeteoStation**, the following sensors are created:
- Temperature (°C)
- Humidity (%)
- Atmospheric Pressure (hPa)
- PM1, PM2.5, PM10 (µg/m³)
- Battery Voltage (V)
- Last Update (timestamp)

For each **RainfallMeter**, the following sensors are created:
- Current Rainfall (mm)
- Today's Rainfall (mm)
- 24-Hour Rainfall (mm)
- Last Hour Rainfall (mm)
- Battery Voltage (V)

## Example Lovelace Card

```yaml
type: entities
title: Weather Station
entities:
  - entity: sensor.reka_temperature
  - entity: sensor.reka_humidity
  - entity: sensor.reka_pressure
  - entity: sensor.reka_pm2_5
  - entity: sensor.reka_rainfall_today
```

## Example Automations

### High Air Pollution Alert

```yaml
automation:
  - alias: "Air Quality Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.reka_pm2_5
        above: 35
    action:
      - service: notify.mobile_app
        data:
          message: "Air quality is unhealthy! PM2.5: {{ states('sensor.reka_pm2_5') }} µg/m³"
```

### Heavy Rainfall Notification

```yaml
automation:
  - alias: "Heavy Rain Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.reka_last_hour_rainfall
        above: 10
    action:
      - service: notify.mobile_app
        data:
          message: "Heavy rainfall detected: {{ states('sensor.reka_last_hour_rainfall') }} mm in the last hour"
```

## Troubleshooting

### No Data Showing

1. Verify your API token is correct
2. Check that your town has active sensors
3. Look at Home Assistant logs: **Settings** → **System** → **Logs**
4. Test the API manually using curl (see above)

### Sensors Not Updating

- The integration polls every 5 minutes by default
- Check if the device shows as "unavailable" - this may indicate the sensor is offline
- Verify the sensor is still active on the ChytrejsiObec portal

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

If you find this integration useful, consider:
- ⭐ Starring the repository
- 🐛 Reporting issues
- 🔧 Contributing improvements

## License

MIT License - See LICENSE file for details

## Credits

- Data provided by [ChytrejsiObec](https://chytrejsiobec.cz/)
- Integration developed for the Home Assistant community

## Disclaimer

This is an unofficial integration. It is not affiliated with or endorsed by ChytrejsiObec or any municipality.