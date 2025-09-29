import json
from homeassistant.components import mqtt
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

RELAY_TOPICS = {1: "relay1", 2: "relay2", 3: "relay3", 4: "relay4"}

async def async_setup_entry(hass, entry, async_add_entities):
    topic_prefix = entry.data.get("topic_prefix", "freeds")

    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=f"FreeDS ({topic_prefix})",
        manufacturer="FreeDS",
        model="MQTT Controller"
    )

    # Se elimina el switch FreedsPWM de esta lista
    entities = [FreedsRelay(entry, topic_prefix, i, device_info) for i in RELAY_TOPICS]
    async_add_entities(entities)

class FreedsRelay(SwitchEntity):
    def __init__(self, entry, prefix, relay_num, device_info):
        self._attr_device_info = device_info
        self._relay_num = relay_num
        self._attr_name = f"FreeDS Relay {relay_num}"
        self._attr_unique_id = f"{entry.entry_id}_relay_{relay_num}"
        self._state = False
        self._topic_cmd = f"{prefix}/relay/{relay_num}/CMND"
        self._topic_stat = f"{prefix}/relay/{relay_num}/STATUS"

    async def async_added_to_hass(self):
        await mqtt.async_subscribe(self.hass, self._topic_stat, self.message_received)

    def message_received(self, msg):
        self._state = msg.payload.lower() == 'on'
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs):
        payload = json.dumps({"command": f"relay{self._relay_num}", "payload": "1"})
        await mqtt.async_publish(self.hass, self._topic_cmd, payload)

    async def async_turn_off(self, **kwargs):
        payload = json.dumps({"command": f"relay{self._relay_num}", "payload": "0"})
        await mqtt.async_publish(self.hass, self._topic_cmd, payload)

    @property
    def is_on(self):
        return self._state