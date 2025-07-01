"""Field type enumeration for magnetic measurement data."""

from enum import Enum


class FieldType(Enum):
    """Simple field type enumeration."""

    TIME = "time"
    MAGNETIC_FIELD = "magnetic_field"
    CURRENT = "current"
    VOLTAGE = "voltage"
    TEMPERATURE = "temperature"
    PRESSURE = "pressure"
    FLOW_RATE = "flow_rate"
    POWER = "power"
    ROTATION_SPEED = "rotation_speed"
    PERCENTAGE = "percentage"
    RESISTANCE = "resistance"
    COORDINATE = "coordinate"
    LENGTH = "length"
    AREA = "area"
    VOLUME = "volume"
    INDEX = "index"