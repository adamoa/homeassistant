"""Platform for integration of shades."""
import logging
from typing import Any

from homeassistant.components.cover import (
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
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

    add_entities(ScenarioShade(scenario, shade) for shade in frontend.getShades())


class ScenarioShade(Device, CoverEntity):
    def __init__(self, scenario: Scenario, shade) -> None:
        super().__init__(scenario, shade)
        self._opening = False
        self._closing = False

    @property
    def device_class(self) -> CoverDeviceClass | None:
        return CoverDeviceClass.SHADE

    @property
    def supported_features(self) -> CoverEntityFeature:
        return (
            CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP
        )

    @property
    def is_opening(self) -> bool | None:
        return self._opening

    @property
    def is_closing(self) -> bool | None:
        return self._closing

    @property
    def is_closed(self) -> bool | None:
        return None

    def get_shade(self):
        return self.get_frontend().getShade(self._code)

    def open_cover(self, **kwargs: Any) -> None:
        self.get_shade().command(True)

    def close_cover(self, **kwargs: Any) -> None:
        self.get_shade().command(False)

    def stop_cover(self, **kwargs: Any) -> None:
        self.get_shade().stop()
