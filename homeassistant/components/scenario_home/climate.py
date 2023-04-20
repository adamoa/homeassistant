"""Platform for integration of air conditioners."""
import logging

from homeassistant.components.climate import (
    FAN_DIFFUSE,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import TEMP_CELSIUS
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

    add_entities(
        ScenarioAirConditioner(scenario, air_conditioner)
        for air_conditioner in frontend.getIRDevices()
        if air_conditioner.getType() == "ac_lg"
    )


class ScenarioAirConditioner(Device, ClimateEntity):
    def __init__(self, scenario: Scenario, air_conditioner) -> None:
        super().__init__(scenario, air_conditioner)
        self._max_temp = air_conditioner.getMaxTemp()
        self._min_temp = air_conditioner.getMinTemp()
        self._mode = None
        self._fan_speed = None
        self._temp = None

    @property
    def temperature_unit(self) -> str:
        return TEMP_CELSIUS

    @property
    def target_temperature(self) -> float | None:
        return self._temp

    @property
    def target_temperature_step(self) -> float | None:
        return 1

    @property
    def max_temp(self) -> float:
        return self._max_temp

    @property
    def min_temp(self) -> float:
        return self._min_temp

    @property
    def hvac_mode(self) -> HVACMode | str | None:
        return self._mode

    @property
    def hvac_modes(self) -> list[HVACMode] | list[str]:
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
        return self._fan_speed

    @property
    def fan_modes(self) -> list[str] | None:
        return [FAN_LOW, FAN_MEDIUM, FAN_HIGH, FAN_DIFFUSE]

    @property
    def supported_features(self) -> ClimateEntityFeature:
        return ClimateEntityFeature.FAN_MODE | ClimateEntityFeature.TARGET_TEMPERATURE

    def get_air_conditioner(self):
        return self.get_frontend().getIRDevice(self._code)

    def set_temperature(self, **kwargs) -> None:
        ac = self.get_air_conditioner()
        ac.setTemp(int(kwargs["temperature"]))
        ac.sendCommand()

    def set_humidity(self, humidity: int) -> None:
        raise NotImplementedError()

    def set_fan_mode(self, fan_mode: str) -> None:
        ac = self.get_air_conditioner()
        ac.setFanSpeed(fan_mode if fan_mode != FAN_DIFFUSE else "wind")
        ac.sendCommand()

    def set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        ac = self.get_air_conditioner()

        if hvac_mode == HVACMode.OFF:
            ac.turnOff()
        else:
            ac.turnOn()
            ac.setMode(hvac_mode.replace("_", "-"))

        ac.sendCommand()

    def set_swing_mode(self, swing_mode: str) -> None:
        raise NotImplementedError()

    def set_preset_mode(self, preset_mode: str) -> None:
        raise NotImplementedError()

    def turn_aux_heat_on(self) -> None:
        raise NotImplementedError()

    def turn_aux_heat_off(self) -> None:
        raise NotImplementedError()

    def update(self):
        ac = self.get_air_conditioner()
        self._mode = ac.getMode().replace("-", "_") if ac.isOn() else HVACMode.OFF
        fan_speed = ac.getFanSpeed()
        self._fan_speed = fan_speed if fan_speed != "wind" else FAN_DIFFUSE
        self._temp = ac.getTempSet()
