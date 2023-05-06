"""Platform for integration of air conditioners."""
import logging
from typing import Any

from homeassistant.components.climate import (
    FAN_DIFFUSE,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import RequiredParameterMissing
from homeassistant.helpers.entity_platform import (
    AddEntitiesCallback,
    async_get_current_platform,
)
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import CONF_SCENARIO
from .scenario import Device, Scenario

_LOGGER = logging.getLogger(__name__)


# noinspection PyUnusedLocal
async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the climate entities."""
    # Assign configuration variables.
    # The configuration check takes care they are present.
    if discovery_info is None:
        raise RequiredParameterMissing(["Unable to set up without discovery_info."])

    scenario = discovery_info[CONF_SCENARIO]

    # Setup connection with devices/cloud
    frontend = scenario.get_frontend()

    add_entities(
        ScenarioAirConditioner(scenario, air_conditioner)
        for air_conditioner in frontend.getIRDevices()
        if air_conditioner.getType() == "ac_lg"
    )

    platform = async_get_current_platform()

    platform.async_register_entity_service("toggle_led", {}, "toggle_led")


class ScenarioAirConditioner(Device, ClimateEntity):
    """Representation of a Climate device."""

    def __init__(self, scenario: Scenario, air_conditioner) -> None:
        """Construct the climate entity based on remote representation."""
        super().__init__(scenario, air_conditioner)
        self._max_temp = air_conditioner.getMaxTemp()
        self._min_temp = air_conditioner.getMinTemp()
        self._mode = None
        self._fan_speed = None
        self._temp = None

    @property
    def temperature_unit(self) -> str:
        """Return the unit of measurement used by the platform."""
        return UnitOfTemperature.CELSIUS

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        return self._temp

    @property
    def target_temperature_step(self) -> float | None:
        """Return the supported step of target temperature."""
        return 1

    @property
    def max_temp(self) -> float:
        """Return the maximum temperature."""
        return self._max_temp

    @property
    def min_temp(self) -> float:
        """Return the minimum temperature."""
        return self._min_temp

    @property
    def hvac_mode(self) -> HVACMode | str | None:
        """Return hvac operation ie. heat, cool mode."""
        return self._mode

    @property
    def hvac_modes(self) -> list[HVACMode] | list[str]:
        """Return the list of available hvac operation modes."""
        return [
            HVACMode.AUTO,
            HVACMode.COOL,
            HVACMode.HEAT,
            HVACMode.DRY,
            HVACMode.FAN_ONLY,
            HVACMode.OFF,
        ]

    @property
    def fan_mode(self) -> str | None:
        """Return the fan setting."""
        return self._fan_speed

    @property
    def fan_modes(self) -> list[str] | None:
        """Return the list of available fan modes."""
        return [FAN_LOW, FAN_MEDIUM, FAN_HIGH, FAN_DIFFUSE]

    @property
    def supported_features(self) -> ClimateEntityFeature:
        """Return the list of supported features."""
        return ClimateEntityFeature.FAN_MODE | ClimateEntityFeature.TARGET_TEMPERATURE

    def _get_air_conditioner(self):
        return self.get_frontend().getIRDevice(self._code)

    def set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        remote_ac = self._get_air_conditioner()
        remote_ac.setTemp(int(kwargs["temperature"]))
        remote_ac.sendCommand()

    def set_humidity(self, humidity: int) -> None:
        """Set new target humidity."""
        raise NotImplementedError()

    def set_fan_mode(self, fan_mode: str) -> None:
        """Set new target fan mode."""
        remote_ac = self._get_air_conditioner()
        remote_ac.setFanSpeed(fan_mode if fan_mode != FAN_DIFFUSE else "wind")
        remote_ac.sendCommand()

    def set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        remote_ac = self._get_air_conditioner()

        if hvac_mode == HVACMode.OFF:
            remote_ac.turnOff()
        else:
            remote_ac.turnOn()
            remote_ac.setMode(hvac_mode.replace("_", "-"))

        remote_ac.sendCommand()

    def set_swing_mode(self, swing_mode: str) -> None:
        """Set new target swing operation."""
        raise NotImplementedError()

    def set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        raise NotImplementedError()

    def turn_aux_heat_on(self) -> None:
        """Turn auxiliary heater on."""
        raise NotImplementedError()

    def turn_aux_heat_off(self) -> None:
        """Turn auxiliary heater off."""
        raise NotImplementedError()

    def update(self):
        """Update function for polling status."""
        remote_ac = self._get_air_conditioner()
        self._mode = (
            remote_ac.getMode().replace("-", "_") if remote_ac.isOn() else HVACMode.OFF
        )
        fan_speed = remote_ac.getFanSpeed()
        self._fan_speed = fan_speed if fan_speed != "wind" else FAN_DIFFUSE
        self._temp = remote_ac.getTempSet()

    def toggle_led(self):
        """Service for toggling the status LED of the equipment."""
        remote_ac = self._get_air_conditioner()
        remote_ac.toggleLed()
