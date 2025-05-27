"""Integration with Scenario Home automation system."""

import voluptuous as vol

from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.discovery import load_platform

from .scenario import Scenario

CONF_SCENARIO = "scenario"
CONF_API_URL = "api_url"
DOMAIN = "scenario_home"
CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_HOST, default="local-scenario-connector"): cv.string,
                vol.Required(CONF_PORT, default=25333): cv.positive_int,
                vol.Required(
                    CONF_API_URL, default="http://supervisor/core/api/"
                ): cv.string,
            }
        )
    },
    extra=vol.REMOVE_EXTRA,
)


def setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the scenario components from configuration.yaml."""
    data = config[DOMAIN]

    load_platform(
        hass,
        "light",
        DOMAIN,
        {
            CONF_SCENARIO: Scenario(data[CONF_HOST], data[CONF_PORT]),
            "api_url": data[CONF_API_URL],
        },
        config,
    )
    load_platform(
        hass,
        "cover",
        DOMAIN,
        {
            CONF_SCENARIO: Scenario(data[CONF_HOST], data[CONF_PORT]),
            "api_url": data[CONF_API_URL],
        },
        config,
    )
    load_platform(
        hass,
        "climate",
        DOMAIN,
        {CONF_SCENARIO: Scenario(data[CONF_HOST], data[CONF_PORT])},
        config,
    )

    return True
