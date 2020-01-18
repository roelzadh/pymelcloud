"""Heat pump (DeviceType=0) device definition."""
from typing import Any, Dict, List, Optional

from pymelcloud.device import Device, EFFECTIVE_FLAGS

PROPERTY_POWER = "power"
PROPERTY_TARGET_TEMPERATURE = "target_temperature"
PROPERTY_OPERATION_MODE = "operation_mode"
PROPERTY_FAN_SPEED = "fan_speed"
PROPERTY_VANE_HORIZONTAL = "vane_horizontal"
PROPERTY_VANE_VERTICAL = "vane_vertical"

FAN_SPEED_AUTO = "auto"
FAN_SPEED_SLUG = "speed-"

OPERATION_MODE_HEAT = "heat"
OPERATION_MODE_DRY = "dry"
OPERATION_MODE_COOL = "cool"
OPERATION_MODE_FAN_ONLY = "fan-only"
OPERATION_MODE_HEAT_COOL = "heat-cool"
OPERATION_MODE_UNDEFINED = "undefined"

_OPERATION_MODE_LOOKUP = {
    1: OPERATION_MODE_HEAT,
    2: OPERATION_MODE_DRY,
    3: OPERATION_MODE_COOL,
    7: OPERATION_MODE_FAN_ONLY,
    8: OPERATION_MODE_HEAT_COOL,
}

_OPERATION_MODE_MIN_TEMP_LOOKUP = {
    OPERATION_MODE_HEAT: "MinTempHeat",
    OPERATION_MODE_DRY: "MinTempCoolDry",
    OPERATION_MODE_COOL: "MinTempCoolDry",
    OPERATION_MODE_FAN_ONLY: "MinTempHeat",  # Fake it just in case.
    OPERATION_MODE_HEAT_COOL: "MinTempAutomatic",
    OPERATION_MODE_UNDEFINED: "MinTempHeat",
}

_OPERATION_MODE_MAX_TEMP_LOOKUP = {
    OPERATION_MODE_HEAT: "MaxTempHeat",
    OPERATION_MODE_DRY: "MaxTempCoolDry",
    OPERATION_MODE_COOL: "MaxTempCoolDry",
    OPERATION_MODE_FAN_ONLY: "MaxTempHeat",  # Fake it just in case.
    OPERATION_MODE_HEAT_COOL: "MaxTempAutomatic",
    OPERATION_MODE_UNDEFINED: "MaxTempHeat",
}

V_VANE_POSITION_AUTO = "auto"
V_VANE_POSITION_1 = "1-up"
V_VANE_POSITION_2 = "2"
V_VANE_POSITION_3 = "3"
V_VANE_POSITION_4 = "4"
V_VANE_POSITION_5 = "5-down"
V_VANE_POSITION_SWING = "swing"
V_VANE_POSITION_UNDEFINED = "undefined"


H_VANE_POSITION_AUTO = "auto"
H_VANE_POSITION_1 = "1-left"
H_VANE_POSITION_2 = "2"
H_VANE_POSITION_3 = "3"
H_VANE_POSITION_4 = "4"
H_VANE_POSITION_5 = "5-right"
H_VANE_POSITION_SPLIT = "split"
H_VANE_POSITION_SWING = "swing"
H_VANE_POSITION_UNDEFINED = "undefined"


def _fan_speed_from(speed: int) -> str:
    if speed == 0:
        return FAN_SPEED_AUTO

    return f"{FAN_SPEED_SLUG}{speed}"


def _fan_speed_to(speed: str) -> int:
    assert speed >= 0
    if speed == FAN_SPEED_AUTO:
        return 0

    return int(speed[len(FAN_SPEED_SLUG) :])


def _operation_mode_from(mode: int) -> str:
    return _OPERATION_MODE_LOOKUP.get(mode, OPERATION_MODE_UNDEFINED)


def _operation_mode_to(mode: str) -> int:
    for k, value in _OPERATION_MODE_LOOKUP.items():
        if value == mode:
            return k
    raise ValueError(f"Invalid operation_mode [{mode}]")


_H_VANE_POSITION_LOOKUP = {
    0: H_VANE_POSITION_AUTO,
    1: H_VANE_POSITION_1,
    2: H_VANE_POSITION_2,
    3: H_VANE_POSITION_3,
    4: H_VANE_POSITION_4,
    5: H_VANE_POSITION_5,
    8: H_VANE_POSITION_SPLIT,
    12: H_VANE_POSITION_SWING,
}


def _horizontal_vane_from(position: int) -> str:
    return _H_VANE_POSITION_LOOKUP.get(position, H_VANE_POSITION_UNDEFINED)


def _horizontal_vane_to(position: str) -> int:
    for k, value in _H_VANE_POSITION_LOOKUP.items():
        if value == position:
            return k
    raise ValueError(f"Invalid horizontal vane position [{position}]")


_V_VANE_POSITION_LOOKUP = {
    0: V_VANE_POSITION_AUTO,
    1: V_VANE_POSITION_1,
    2: V_VANE_POSITION_2,
    3: V_VANE_POSITION_3,
    4: V_VANE_POSITION_4,
    5: V_VANE_POSITION_5,
    7: V_VANE_POSITION_SWING,
}


def _vertical_vane_from(position: int) -> str:
    return _V_VANE_POSITION_LOOKUP.get(position, V_VANE_POSITION_UNDEFINED)


def _vertical_vane_to(position: str) -> int:
    for k, value in _V_VANE_POSITION_LOOKUP.items():
        if value == position:
            return k
    raise ValueError(f"Invalid vertical vane position [{position}]")


class HeatPump(Device):
    """Heat pump device."""

    def apply_write(self, state: Dict[str, Any], key: str, value: Any):
        """Apply writes to state object.

    Used for property validation, do not modify device state.    
    """
        flags = state.get(EFFECTIVE_FLAGS, 0)

        if key == PROPERTY_POWER:
            state["Power"] = value
            flags = flags | 0x01
        elif key == PROPERTY_TARGET_TEMPERATURE:
            state["SetTemperature"] = value
            flags = flags | 0x04
        elif key == PROPERTY_OPERATION_MODE:
            state["OperationMode"] = _operation_mode_to(value)
            flags = flags | 0x02
        elif key == PROPERTY_FAN_SPEED:
            state["SetFanSpeed"] = _fan_speed_to(value)
            flags = flags | 0x08
        elif key == PROPERTY_VANE_HORIZONTAL:
            state["VaneHorizontal"] = _horizontal_vane_to(value)
            flags = flags | 0x100
        elif key == PROPERTY_VANE_VERTICAL:
            state["VaneVertical"] = _vertical_vane_to(value)
            flags = flags | 0x10
        else:
            raise ValueError(f"Cannot set {key}, invalid property")

        state[EFFECTIVE_FLAGS] = flags

    @property
    def power(self) -> Optional[bool]:
        """Return power on / standby state of the device."""
        if self._state is None:
            return None
        return self._state.get("Power")

    @property
    def total_energy_consumed(self) -> Optional[float]:
        """Return total consumed energy as kWh."""
        if self._device_conf is None:
            return None
        device = self._device_conf.get("Device", {})
        reading = device.get("CurrentEnergyConsumed", None)
        if reading is None:
            return None
        return reading / 1000.0

    @property
    def temperature(self) -> Optional[float]:
        """Return room temperature reported by the device."""
        if self._state is None:
            return None
        return self._state.get("RoomTemperature")

    @property
    def target_temperature(self) -> Optional[float]:
        """Return target temperature set for the device."""
        if self._state is None:
            return None
        return self._state.get("SetTemperature")

    @property
    def target_temperature_step(self) -> Optional[float]:
        """Return target temperature set precision."""
        if self._state is None:
            return None
        return self._device_conf.get("Device", {}).get("TemperatureIncrement", 0.5)

    @property
    def target_temperature_min(self) -> Optional[float]:
        """
		Return maximum target temperature for the currently active operation mode.
		"""
        if self._state is None:
            return None
        return self._device_conf.get("Device", {}).get(
            _OPERATION_MODE_MIN_TEMP_LOOKUP.get(self.operation_mode), 10
        )

    @property
    def target_temperature_max(self) -> Optional[float]:
        """
		Return maximum target temperature for the currently active operation mode.
		"""
        if self._state is None:
            return None
        return self._device_conf.get("Device", {}).get(
            _OPERATION_MODE_MAX_TEMP_LOOKUP.get(self.operation_mode), 31
        )

    @property
    def operation_mode(self) -> str:
        """Return currently active operation mode."""
        if self._state is None:
            return OPERATION_MODE_UNDEFINED
        return _operation_mode_from(self._state.get("OperationMode", -1))

    def operation_modes(self) -> List[str]:
        """Return available operation modes."""
        modes: List[str] = []

        conf_dev = self._device_conf.get("Device", {})
        if conf_dev.get("CanHeat", False):
            modes.append(OPERATION_MODE_HEAT)

        if conf_dev.get("CanDry", False):
            modes.append(OPERATION_MODE_DRY)

        if conf_dev.get("CanCool", False):
            modes.append(OPERATION_MODE_COOL)

        modes.append(OPERATION_MODE_FAN_ONLY)

        if conf_dev.get("ModelSupportsAuto", False):
            modes.append(OPERATION_MODE_HEAT_COOL)

        return modes

    @property
    def fan_speed(self) -> Optional[str]:
        """Return currently active fan speed."""
        if self._state is None:
            return None
        return _fan_speed_from(self._state.get("SetFanSpeed"))

    def fan_speeds(self) -> Optional[List[str]]:
        """Return available fan speeds."""
        if self._state is None:
            return None
        speeds = []
        if self._device_conf.get("Device", {}).get("HasAutomaticFanSpeed", False):
            speeds.append(FAN_SPEED_AUTO)

        num_fan_speeds = self._state.get("NumberOfFanSpeeds", 0)
        for num in range(1, num_fan_speeds + 1):
            speeds.append(_fan_speed_from(num))

        return speeds

    @property
    def vane_horizontal(self) -> Optional[str]:
        """Return horizontal vane position."""
        if self._state is None:
            return None
        return _horizontal_vane_from(self._state.get("VaneHorizontal"))

    def vane_horizontal_positions(self) -> Optional[List[str]]:
        """Return available horizontal vane positions."""
        if self._device_conf.get("HideVaneControls", False):
            return []
        device = self._device_conf.get("Device", {})
        if not device.get("ModelSupportsVaneHorizontal", False):
            return []

        positions = [
            H_VANE_POSITION_AUTO,  # ModelSupportsAuto could affect this.
            H_VANE_POSITION_1,
            H_VANE_POSITION_2,
            H_VANE_POSITION_3,
            H_VANE_POSITION_4,
            H_VANE_POSITION_5,
            H_VANE_POSITION_SPLIT,
        ]
        if device.get("SwingFunction", False):
            positions.append(H_VANE_POSITION_SWING)

        return positions

    @property
    def vane_vertical(self) -> Optional[str]:
        """Return vertical vane position."""
        if self._state is None:
            return None
        return _vertical_vane_from(self._state.get("VaneVertical"))

    def vane_vertical_positions(self) -> Optional[List[str]]:
        """Return available vertical vane positions."""
        if self._device_conf.get("HideVaneControls", False):
            return []
        device = self._device_conf.get("Device", {})
        if not device.get("ModelSupportsVaneVertical", False):
            return []

        positions = [
            V_VANE_POSITION_AUTO,  # ModelSupportsAuto could affect this.
            V_VANE_POSITION_1,
            V_VANE_POSITION_2,
            V_VANE_POSITION_3,
            V_VANE_POSITION_4,
            V_VANE_POSITION_5,
        ]
        if device.get("SwingFunction", False):
            positions.append(V_VANE_POSITION_SWING)

        return positions
