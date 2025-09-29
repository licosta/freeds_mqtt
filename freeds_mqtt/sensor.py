import json
from datetime import timedelta
from homeassistant.components import mqtt
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import (
    UnitOfPower,
    UnitOfTemperature,
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
)
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.util import dt as dt_util
from .const import DOMAIN

SENSORS = {
    "pv1w": {"name": "PV1 Potencia", "unit": UnitOfPower.WATT},
    "pv1v": {"name": "PV1 Voltaje", "unit": UnitOfElectricPotential.VOLT},
    "pv1c": {"name": "PV1 Corriente", "unit": UnitOfElectricCurrent.AMPERE},
    "pv2w": {"name": "PV2 Potencia", "unit": UnitOfPower.WATT},
    "pv2v": {"name": "PV2 Voltaje", "unit": UnitOfElectricPotential.VOLT},
    "pv2c": {"name": "PV2 Corriente", "unit": UnitOfElectricCurrent.AMPERE},
    "solarW": {"name": "Producción Solar", "unit": UnitOfPower.WATT},
    "gridW": {"name": "Red", "unit": UnitOfPower.WATT},
    "gridV": {"name": "Voltaje Red", "unit": UnitOfElectricPotential.VOLT},
    "gridC": {"name": "Corriente Red", "unit": UnitOfElectricCurrent.AMPERE},
    "loadWatts": {"name": "Consumo Vivienda", "unit": UnitOfPower.WATT},
    "invTemp": {"name": "Temp Inversor", "unit": UnitOfTemperature.CELSIUS},
    "todayW": {"name": "Energía generada hoy", "unit": UnitOfEnergy.KILO_WATT_HOUR},
    "batteryV": {"name": "Voltaje Batería", "unit": UnitOfElectricPotential.VOLT},
    "batteryC": {"name": "Corriente Batería", "unit": UnitOfElectricCurrent.AMPERE},
    "batteryW": {"name": "Potencia Batería", "unit": UnitOfPower.WATT},
    "batterySoC": {"name": "Batería SOC", "unit": PERCENTAGE},
    "calcWatts": {"name": "Potencia Derivada Estimada", "unit": UnitOfPower.WATT},
    "houseConsumption": {"name": "Consumo Casa", "unit": UnitOfPower.WATT},
    "tempTermo": {"name": "Temperatura Termo", "unit": UnitOfTemperature.CELSIUS},
    "tempTriac": {"name": "Temperatura Triac", "unit": UnitOfTemperature.CELSIUS},
    "tempCustom": {"name": "Temperatura Personalizada", "unit": UnitOfTemperature.CELSIUS},
    "pwm": {"name": "PWM", "unit": PERCENTAGE},
    "stat/pwm": {"name": "PWM Mode", "icon": "mdi:cog-transfer"},
}

async def async_setup_entry(hass, entry, async_add_entities):
    topic_prefix = entry.data.get("topic_prefix", "freeds")
    
    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=f"FreeDS ({topic_prefix})",
        manufacturer="FreeDS",
        model="MQTT Controller"
    )
    
    entities = [FreedsSensor(entry, topic_prefix, topic, cfg, device_info) for topic, cfg in SENSORS.items()]
    # Añadimos el nuevo sensor de energía diaria
    entities.append(FreedsDailyEnergySensor(entry, topic_prefix, device_info))
    async_add_entities(entities)

class FreedsSensor(SensorEntity):
    def __init__(self, entry, prefix, topic, cfg, device_info):
        self._attr_device_info = device_info
        self._attr_name = cfg["name"]
        self._attr_unique_id = f"{entry.entry_id}_{topic.replace('/', '_')}"
        self._attr_native_unit_of_measurement = cfg.get("unit")
        self._attr_icon = cfg.get("icon")
        self._state = None
        self._topic = f"{prefix}/{topic}"

    async def async_added_to_hass(self):
        await mqtt.async_subscribe(self.hass, self._topic, self.message_received)

    def message_received(self, msg):
        self._state = msg.payload
        self.async_write_ha_state()

    @property
    def native_value(self):
        return self._state

class FreedsDailyEnergySensor(SensorEntity):
    """Calcula la energía diaria a partir de la potencia derivada."""
    _attr_should_poll = False

    def __init__(self, entry, prefix, device_info):
        self._attr_device_info = device_info
        self._attr_name = "Energía Excedentes Diaria"
        self._attr_unique_id = f"{entry.entry_id}_daily_derived_energy"
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._topic = f"{prefix}/calcWatts"
        
        self._energy_total = 0.0
        self._last_power_w = 0.0
        self._last_update = None

    async def async_added_to_hass(self):
        """Se suscribe al tópico de potencia al ser añadido a Home Assistant."""
        self._last_update = dt_util.now()
        await mqtt.async_subscribe(self.hass, self._topic, self.message_received)

    def message_received(self, msg):
        """Gestiona un nuevo valor de potencia y actualiza la energía acumulada."""
        try:
            new_power_w = float(msg.payload)
        except (ValueError, TypeError):
            return

        now = dt_util.now()
        
        if self._last_update is None:
            self._last_update = now
            return

        # Reinicia el contador si es un nuevo día
        if now.date() != self._last_update.date():
            self._energy_total = 0.0

        time_delta = now - self._last_update
        if time_delta.total_seconds() > 0:
            # Cálculo de energía por el método del trapecio
            time_delta_hours = time_delta.total_seconds() / 3600.0
            avg_power_kw = (self._last_power_w + new_power_w) / 2 / 1000.0
            energy_added = avg_power_kw * time_delta_hours
            self._energy_total += energy_added

        self._last_power_w = new_power_w
        self._last_update = now
        self._attr_native_value = round(self._energy_total, 2)
        self.async_write_ha_state()