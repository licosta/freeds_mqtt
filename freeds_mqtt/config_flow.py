import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN, DEFAULT_HOST, DEFAULT_TOPIC_PREFIX

class FreedsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            return self.async_create_entry(
                title="FreeDS MQTT",
                data=user_input
            )

        schema = vol.Schema({
            vol.Optional("host", default=DEFAULT_HOST): str,
            vol.Optional("topic_prefix", default=DEFAULT_TOPIC_PREFIX): str,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors
        )
