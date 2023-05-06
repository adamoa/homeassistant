"""Platform for integration of shades."""
from collections.abc import Callable
from datetime import timedelta
import logging
from typing import Any

from homeassistant.components.cover import (
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import RequiredParameterMissing
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import CONF_API_URL, CONF_SCENARIO
from .scenario import Device, Scenario

_LOGGER = logging.getLogger(__name__)


# noinspection PyUnusedLocal
def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up cover entities."""
    # Assign configuration variables.
    # The configuration check takes care they are present.
    if discovery_info is None:
        raise RequiredParameterMissing(["Unable to set up without discovery_info."])

    scenario = discovery_info[CONF_SCENARIO]

    # Setup connection with devices/cloud
    frontend = scenario.get_frontend()

    add_entities(
        ScenarioShade(scenario, shade, discovery_info[CONF_API_URL])
        for shade in frontend.getShades()
    )


class ScenarioShade(Device, CoverEntity):
    """Representation of a Cover device."""

    _attr_should_poll = False

    def __init__(self, scenario: Scenario, shade, api_url) -> None:
        """Construct the cover entity based on remote representation."""
        super().__init__(scenario, shade)
        self._opening = False
        self._closing = False
        self.api_url = api_url
        self.stop_updater: Callable[[], None] | None = None

    async def _subscribe(self, *args):
        frontend = self.get_frontend()
        connector = frontend.getHomeAssistantConnector(self.api_url)
        connector.registerEntity(self._code, self.entity_id)

    async def async_added_to_hass(self) -> None:
        """Run when this Entity has been added to HA."""
        self.stop_updater = async_track_time_interval(
            self.hass, self._subscribe, timedelta(seconds=30)
        )
        await self._subscribe()

    async def async_will_remove_from_hass(self) -> None:
        """Entity being removed from hass."""
        # The opposite of async_added_to_hass. Remove any registered call backs here.
        if self.stop_updater is not None:
            self.stop_updater()
            frontend = self.get_frontend()
            connector = frontend.getHomeAssistantConnector(self.api_url)
            connector.unregisterEntity(self._code)

    @property
    def device_class(self) -> CoverDeviceClass | None:
        """Return the class of this entity."""
        return CoverDeviceClass.SHADE

    @property
    def supported_features(self) -> CoverEntityFeature:
        """Flag supported features."""
        return (
            CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP
        )

    @property
    def is_opening(self) -> bool | None:
        """Return if the cover is opening or not."""
        return self.get_frontend().getShade(self._code).isMovingUp()

    @property
    def is_closing(self) -> bool | None:
        """Return if the cover is closing or not."""
        return self.get_frontend().getShade(self._code).isMovingDown()

    @property
    def is_closed(self) -> bool | None:
        """Return if the cover is closed or not."""
        return None

    def _get_shade(self):
        return self.get_frontend().getShade(self._code)

    def open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        self._get_shade().command(True)

    def close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        self._get_shade().command(False)

    def stop_cover(self, **kwargs: Any) -> None:
        """Stop the cover."""
        self._get_shade().stop()
