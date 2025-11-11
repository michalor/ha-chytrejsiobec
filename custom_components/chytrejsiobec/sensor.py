"""Support for ChytrejsiObec sensors."""
from __future__ import annotations

from datetime import datetime
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    PERCENTAGE,
    UnitOfPressure,
    UnitOfTemperature,
    UnitOfElectricPotential,
    UnitOfLength,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ... import ChytrejsiObecDataUpdateCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Sensor definitions: (key, name, unit, device_class, state_class, icon)
METEO_SENSORS = [
    ("airTemperature", "Temperature", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, None),
    ("airHumidity", "Humidity", PERCENTAGE, SensorDeviceClass.HUMIDITY, SensorStateClass.MEASUREMENT, None),
    ("airPressure", "Pressure", UnitOfPressure.HPA, SensorDeviceClass.ATMOSPHERIC_PRESSURE, SensorStateClass.MEASUREMENT, None),
    ("dustPM1", "PM1", CONCENTRATION_MICROGRAMS_PER_CUBIC_METER, SensorDeviceClass.PM1, SensorStateClass.MEASUREMENT, None),
    ("dustPM25", "PM2.5", CONCENTRATION_MICROGRAMS_PER_CUBIC_METER, SensorDeviceClass.PM25, SensorStateClass.MEASUREMENT, None),
    ("dustPM10", "PM10", CONCENTRATION_MICROGRAMS_PER_CUBIC_METER, SensorDeviceClass.PM10, SensorStateClass.MEASUREMENT, None),
    ("mainPower", "Battery", UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "mdi:battery"),
    ("lastCommunicationTime", "Last Update", None, SensorDeviceClass.TIMESTAMP, None, "mdi:clock-outline"),
]

RAINFALL_SENSORS = [
    ("rainfall", "Current Rainfall", UnitOfLength.MILLIMETERS, None, SensorStateClass.MEASUREMENT, "mdi:weather-rainy"),
    ("todaysRainfall", "Today's Rainfall", UnitOfLength.MILLIMETERS, None, SensorStateClass.TOTAL_INCREASING, "mdi:weather-pouring"),
    ("rainfall24", "24h Rainfall", UnitOfLength.MILLIMETERS, None, SensorStateClass.MEASUREMENT, "mdi:weather-pouring"),
    ("lastHourRainfall", "Last Hour Rainfall", UnitOfLength.MILLIMETERS, None, SensorStateClass.MEASUREMENT, "mdi:weather-rainy"),
    ("mainPower", "Battery", UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "mdi:battery"),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ChytrejsiObec sensors based on a config entry."""
    coordinator: ChytrejsiObecDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    
    # Create sensors for each device
    for device_idx, device in enumerate(coordinator.data):
        device_class = device.get("class")
        device_name = device.get("deviceName", f"Device {device_idx}")
        device_id = device.get("devID", f"device_{device_idx}")
        
        if device_class == "MeteoStation":
            for sensor_def in METEO_SENSORS:
                key = sensor_def[0]
                # Only create sensor if data exists
                if key in device.get("data", {}):
                    entities.append(
                        ChytrejsiObecSensor(
                            coordinator,
                            device_idx,
                            device_name,
                            device_id,
                            sensor_def,
                        )
                    )
        
        elif device_class == "RainfallMeter":
            for sensor_def in RAINFALL_SENSORS:
                key = sensor_def[0]
                if key in device.get("data", {}):
                    entities.append(
                        ChytrejsiObecSensor(
                            coordinator,
                            device_idx,
                            device_name,
                            device_id,
                            sensor_def,
                        )
                    )

    async_add_entities(entities)


class ChytrejsiObecSensor(CoordinatorEntity, SensorEntity):
    """Representation of a ChytrejsiObec sensor."""

    def __init__(
        self,
        coordinator: ChytrejsiObecDataUpdateCoordinator,
        device_idx: int,
        device_name: str,
        device_id: str,
        sensor_def: tuple,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        
        self._device_idx = device_idx
        self._device_name = device_name
        self._device_id = device_id
        
        self._key = sensor_def[0]
        self._sensor_name = sensor_def[1]
        self._unit = sensor_def[2]
        self._device_class = sensor_def[3]
        self._state_class = sensor_def[4]
        self._icon = sensor_def[5]
        
        # Generate unique_id
        self._attr_unique_id = f"{device_id}_{self._key}"
        self._attr_name = f"{device_name} {self._sensor_name}"
        
        # Set device info for grouping
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device_name,
            "manufacturer": "ChytrejsiObec",
            "model": coordinator.data[device_idx].get("model", "Unknown"),
        }

    @property
    def native_value(self):
        """Return the state of the sensor."""
        try:
            device_data = self.coordinator.data[self._device_idx].get("data", {})
            value = device_data.get(self._key)
            
            # Handle timestamp conversion
            if self._device_class == SensorDeviceClass.TIMESTAMP and value:
                try:
                    return datetime.fromisoformat(value.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    return None
            
            return value
        except (IndexError, KeyError):
            return None

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit

    @property
    def device_class(self):
        """Return the device class."""
        return self._device_class

    @property
    def state_class(self):
        """Return the state class."""
        return self._state_class

    @property
    def icon(self):
        """Return the icon."""
        return self._icon

    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        try:
            device = self.coordinator.data[self._device_idx]
            return {
                "device_class": device.get("class"),
                "model": device.get("model"),
                "vendor": device.get("vendor"),
                "status": device.get("status", {}).get("status"),
                "location": device.get("config", {}).get("map", {}).get("position"),
            }
        except (IndexError, KeyError):
            return {}