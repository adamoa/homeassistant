"""Platform for light integration."""
from collections.abc import Callable
from datetime import timedelta
import logging
from typing import Any

from homeassistant.components.light import ATTR_BRIGHTNESS, ColorMode, LightEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import RequiredParameterMissing
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import CONF_API_URL, CONF_SCENARIO
from .scenario import Device, Scenario

_LOGGER = logging.getLogger(__name__)
PARALLEL_UPDATES = 16


# noinspection PyUnusedLocal
def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up light entities."""
    # Assign configuration variables.
    # The configuration check takes care they are present.
    if discovery_info is None:
        raise RequiredParameterMissing(["Unable to set up without discovery_info."])

    scenario = discovery_info[CONF_SCENARIO]

    # Setup connection with devices/cloud
    frontend = scenario.get_frontend()

    add_entities(
        ScenarioLight(scenario, light, discovery_info[CONF_API_URL])
        for light in frontend.getLights()
    )


class ScenarioLight(Device, LightEntity):
    """Representation of a Light device."""

    _attr_should_poll = False

    def __init__(self, scenario: Scenario, light, api_url) -> None:
        """Construct the light entity based on remote representation."""
        super().__init__(scenario, light)
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
    def supported_color_modes(self) -> set[ColorMode] | set[str] | None:
        """Instructs hass whether a light can have its brightness changed."""
        return (
            {ColorMode.BRIGHTNESS}
            if self._get_light().isDimmable()
            else {ColorMode.ONOFF}
        )

    @property
    def brightness(self):
        """Return the brightness of the light."""
        return self._get_light().getIntensity()

    @property
    def is_on(self) -> bool | None:
        """Return true if light is on."""
        return self._get_light().isOn()

    def _get_light(self):
        return self.get_frontend().getLight(self._code)

    def turn_on(self, **kwargs: Any) -> None:
        """Instruct the light to turn on."""
        light = self._get_light()
        brightness = int(kwargs.get(ATTR_BRIGHTNESS, 255) * 100 / 255)
        light.setIntensity(brightness)

    def turn_off(self, **kwargs: Any) -> None:
        """Instruct the light to turn off."""
        self._get_light().turnOn(False)
