"""SkodaObdBleEntity base class."""

from homeassistant.const import CONF_ADDRESS
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN, NAME, VERSION


class SkodaObdBleEntity(CoordinatorEntity):
    """Base entity for skoda_obd_ble."""

    def __init__(self, coordinator, config_entry) -> None:
        """Initialise."""
        super().__init__(coordinator)
        self.config_entry = config_entry

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        return f"{self.config_entry.data[CONF_ADDRESS]}-{self.name}"

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self.config_entry.data[CONF_ADDRESS])},
            "name": NAME,
            "manufacturer": "ELM327-compatible",
            "model": "BLE OBD-II adapter",
            "sw_version": VERSION,
        }

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return {
            "attribution": ATTRIBUTION,
            "integration": DOMAIN,
        }

    @property
    def extra_state_attributes(self):
        """Expose freshness alongside retained readings."""
        return {
            "last_successful_read": self.coordinator.value_last_success.get(
                getattr(self, "_sensor", None)
            ),
            "connection_status": self.coordinator.connection_status,
        }
