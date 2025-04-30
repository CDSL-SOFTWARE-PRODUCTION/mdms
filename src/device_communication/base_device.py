from typing import Dict, Any, Type
from enum import Enum, auto

class DeviceStatus(Enum):
    DISCONNECTED = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    ERROR = auto()
    IDLE = auto()

class ConnectionType(Enum):
    SERIAL = auto()
    USB = auto()
    ETHERNET = auto()
    BLUETOOTH = auto()
    WIFI = auto()
    TCP = auto()

class DeviceFactory:
    def __init__(self):
        self._device_types = {}
    
    def register(self, device_type: str, device_class: Type):
        self._device_types[device_type] = device_class
        
    def create_device(self, device_type: str, *args, **kwargs):
        if device_type not in self._device_types:
            raise ValueError(f"Unknown device type: {device_type}")
        return self._device_types[device_type](*args, **kwargs)

class BaseDevice:
    def __init__(self, device_id: str, connection_type: ConnectionType):
        self.device_id = device_id
        self.connection_type = connection_type
        self.status = DeviceStatus.DISCONNECTED

    async def initialize(self) -> bool:
        """Initialize device and prepare for connection"""
        self.status = DeviceStatus.IDLE
        return True

    async def connect(self) -> bool:
        """Connect to the device"""
        raise NotImplementedError

    async def disconnect(self) -> bool:
        """Disconnect from the device"""
        raise NotImplementedError

    async def get_status(self) -> DeviceStatus:
        """Get current device status"""
        raise NotImplementedError

    async def get_parameters(self) -> Dict[str, Any]:
        """Get current device parameters"""
        raise NotImplementedError

    async def set_parameter(self, parameter: str, value: Any) -> bool:
        """Set a specific device parameter"""
        raise NotImplementedError

    async def run_diagnostic(self) -> Dict[str, Any]:
        """Run device diagnostics"""
        raise NotImplementedError

# Create global device factory instance
device_factory = DeviceFactory()