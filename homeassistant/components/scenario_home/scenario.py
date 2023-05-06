"""Module for defining classes used by every entity connected to Scenario Automation."""
from typing import Any

from py4j.java_gateway import GatewayParameters, JavaGateway

from homeassistant.helpers.entity import Entity


class Scenario:
    """Represents the connection to the Scenario Connector Add-on."""

    def __init__(self, host, port):
        """Construct the Scenario Connector representation."""
        self.host = host
        self.port = port

    def get_frontend(self) -> Any:
        """Return the frontend API of the Add-On."""
        return JavaGateway(
            gateway_parameters=GatewayParameters(self.host, self.port)
        ).entry_point.getFrontend()


class Device(Entity):
    """Represents a device from Scenario Automation."""

    frontend: Any = None

    def __init__(self, scenario, device):
        """Construct the device based on the remote representation."""
        self._code = device.getCode()
        self._name = device.getName()
        self._attr_unique_id = f"{scenario.host}_{self._code}"
        self.get_frontend = scenario.get_frontend

    @property
    def name(self) -> str:
        """Return the display name of this device."""
        return self._name
