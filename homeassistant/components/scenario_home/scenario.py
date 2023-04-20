from py4j.java_gateway import GatewayParameters, JavaGateway

from homeassistant.helpers.entity import Entity


class Scenario:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def get_frontend(self):
        return JavaGateway(
            gateway_parameters=GatewayParameters(self.host, self.port)
        ).entry_point.getFrontend()


class Device(Entity):
    frontend = None

    def __init__(self, scenario, device):
        self._code = device.getCode()
        self._name = device.getName()
        self._attr_unique_id = f"{scenario.host}_{self._code}"
        self.get_frontend = scenario.get_frontend

    @property
    def name(self) -> str:
        """Return the display name of this device."""
        return self._name
