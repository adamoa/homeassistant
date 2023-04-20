"""Platform for light integration."""
import logging
from typing import Any

from homeassistant.components.light import ATTR_BRIGHTNESS, ColorMode, LightEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .scenario import Device, Scenario

_LOGGER = logging.getLogger(__name__)


# noinspection PyUnusedLocal
def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    # Assign configuration variables.
    # The configuration check takes care they are present.
    scenario = discovery_info["scenario"]

    # Setup connection with devices/cloud
    frontend = scenario.get_frontend()

    add_entities(ScenarioLight(scenario, light) for light in frontend.getLights())


class ScenarioLight(Device, LightEntity):
    def __init__(self, scenario: Scenario, light) -> None:
        super().__init__(scenario, light)
        self._dimmable = light.isDimmable()
        self._state = None
        self._brightness = None

    @property
    def supported_color_modes(self) -> set[ColorMode] | set[str] | None:
        """Instructs hass whether a light can have its brightness changed."""
        return {ColorMode.BRIGHTNESS} if self._dimmable else {ColorMode.ONOFF}

    @property
    def brightness(self):
        """Return the brightness of the light."""
        return self._brightness

    @property
    def is_on(self) -> bool | None:
        """Return true if light is on."""
        return self._state

    def get_light(self):
        return self.get_frontend().getLight(self._code)

    def turn_on(self, **kwargs: Any) -> None:
        """Instruct the light to turn on."""
        light = self.get_light()
        if self._dimmable:
            brightness = int(kwargs.get(ATTR_BRIGHTNESS, 255) * 100 / 255)
            light.setIntensity(brightness)

        light.turnOn(True)

    def turn_off(self, **kwargs: Any) -> None:
        """Instruct the light to turn off."""
        self.get_light().turnOn(False)

    def update(self) -> None:
        """Fetch new state data for this light."""
        light = self.get_light()
        self._state = light.isOn()
        self._brightness = (
            int(light.getIntensity() * 255 / 100) if self._dimmable else None
        )
