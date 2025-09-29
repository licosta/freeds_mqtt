import json
from homeassistant.components import mqtt
from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    topic_prefix = entry.data.get("topic_prefix", "freeds")

    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=f"FreeDS ({topic_prefix})",
        manufacturer="FreeDS",
        model="MQTT Controller"
    )
    
    entities = [
        FreedsPWMAutoButton(entry, topic_prefix, device_info),
        FreedsPWMManualButton(entry, topic_prefix, device_info),
    ]
    async_add_entities(entities)

class FreedsPWMAutoButton(ButtonEntity):
    """Botón para activar el modo Automático del PWM."""
    def __init__(self, entry, prefix, device_info):
        self._attr_device_info = device_info
        self._attr_name = "Set PWM Auto"
        self._attr_unique_id = f"{entry.entry_id}_pwm_auto_button"
        self._attr_icon = "mdi:auto-mode"
        self._topic_cmd = f"{prefix}/cmnd"

    async def async_press(self) -> None:
        """Poner en modo Automático."""
        payload = json.dumps({"command": "pwmman", "payload": "0"})
        await mqtt.async_publish(self.hass, self._topic_cmd, payload)

class FreedsPWMManualButton(ButtonEntity):
    """Botón para activar el modo Manual del PWM."""
    def __init__(self, entry, prefix, device_info):
        self._attr_device_info = device_info
        self._attr_name = "Set PWM Manual"
        self._attr_unique_id = f"{entry.entry_id}_pwm_manual_button"
        self._attr_icon = "mdi:hand-back-right"
        self._topic_cmd = f"{prefix}/cmnd"

    async def async_press(self) -> None:
        """Poner en modo Manual."""
        payload = json.dumps({"command": "pwmman", "payload": "1"})
        await mqtt.async_publish(self.hass, self._topic_cmd, payload)