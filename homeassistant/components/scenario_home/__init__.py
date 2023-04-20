"""Integration with Scenario Home automation system."""

import voluptuous as vol

from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .scenario import Scenario

DOMAIN = "scenario_home"
CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_HOST, default="local-scenario-connector"): cv.string,
                vol.Required(CONF_PORT, default=25333): cv.positive_int,
            }
        )
    },
    extra=vol.REMOVE_EXTRA,
)


def setup(hass: HomeAssistant, config: ConfigType) -> bool:
    data = config[DOMAIN]

    hass.helpers.discovery.load_platform(
        "light",
        DOMAIN,
        {"scenario": Scenario(data[CONF_HOST], data[CONF_PORT])},
        config,
    )
    hass.helpers.discovery.load_platform(
        "cover",
        DOMAIN,
        {"scenario": Scenario(data[CONF_HOST], data[CONF_PORT])},
        config,
    )
    hass.helpers.discovery.load_platform(
        "climate",
        DOMAIN,
        {"scenario": Scenario(data[CONF_HOST], data[CONF_PORT])},
        config,
    )

    return True
