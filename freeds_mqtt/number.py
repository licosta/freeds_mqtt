import json
from homeassistant.components import mqtt
from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import PERCENTAGE
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    """Configura la plataforma de número para FreeDS."""
    topic_prefix = entry.data.get("topic_prefix", "freeds")

    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=f"FreeDS ({topic_prefix})",
        manufacturer="FreeDS",
        model="MQTT Controller"
    )
    
    async_add_entities([FreedsPWMValueNumber(entry, topic_prefix, device_info)])

class FreedsPWMValueNumber(NumberEntity):
    """Representa el valor del PWM en modo Manual para FreeDS."""

    def __init__(self, entry, prefix, device_info):
        """Inicializa la entidad de número."""
        self._attr_device_info = device_info
        self._attr_name = "PWM Manual Value"
        self._attr_unique_id = f"{entry.entry_id}_pwm_manual_value"
        
        # Propiedades de la entidad
        self._attr_native_min_value = 0
        self._attr_native_max_value = 100
        self._attr_native_step = 1
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_mode = NumberMode.SLIDER
        self._attr_icon = "mdi:speedometer"

        # Tópicos MQTT
        self._topic_cmd = f"{prefix}/cmnd"
        self._topic_stat = f"{prefix}/pwmmanvalue"
        
        # CORREGIDO: Se inicializa sin valor para esperar el estado real desde MQTT
        self._attr_native_value = None

    async def async_added_to_hass(self) -> None:
        """Se suscribe al tópico de estado MQTT."""
        await mqtt.async_subscribe(self.hass, self._topic_stat, self.message_received)

    def message_received(self, msg):
        """Gestiona los nuevos mensajes MQTT del estado."""
        try:
            self._attr_native_value = float(msg.payload)
            self.async_write_ha_state()
        except (ValueError, TypeError):
            # Ignora valores que no sean numéricos
            pass

    async def async_set_native_value(self, value: float) -> None:
        """Actualiza el valor enviando un comando MQTT."""
        payload = json.dumps({"command": "pwmmanvalue", "payload": str(int(value))})
        await mqtt.async_publish(self.hass, self._topic_cmd, payload)