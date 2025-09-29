from homeassistant.components import mqtt
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    """Configura el sensor binario de FreeDS."""
    topic_prefix = entry.data.get("topic_prefix", "freeds")

    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=f"FreeDS ({topic_prefix})",
        manufacturer="FreeDS",
        model="MQTT Controller"
    )

    async_add_entities([FreedsPWMBinarySensor(entry, topic_prefix, device_info)])

class FreedsPWMBinarySensor(BinarySensorEntity):
    """Representa el estado de solo lectura del PWM de FreeDS."""

    def __init__(self, entry, prefix, device_info):
        """Inicializa el sensor binario."""
        self._attr_device_info = device_info
        self._attr_name = "FreeDS PWM Status"
        self._attr_unique_id = f"{entry.entry_id}_pwm_status"
        self._state = False
        self._topic_stat = f"{prefix}/stat/pwm"

    async def async_added_to_hass(self):
        """Se suscribe a los eventos MQTT."""
        await mqtt.async_subscribe(self.hass, self._topic_stat, self.message_received)

    def message_received(self, msg):
        """Gestiona los nuevos mensajes MQTT."""
        payload_str = msg.payload.upper()
        self._state = payload_str in ('AUTO', 'MAN')
        self.async_write_ha_state()

    @property
    def is_on(self):
        """Devuelve True si el PWM está encendido."""
        return self._state