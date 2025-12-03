import os

try:  # pragma: no cover - hardware specific optional dependency
    import Adafruit_BBIO.ADC as ADC  # type: ignore
except ImportError:  # pragma: no cover
    ADC = None  # type: ignore


class MuscleSensor:
    """
    Minimal MyoWare analog reader: use Adafruit_BBIO.ADC directly, convert the
    normalized reading (0-1.0) into volts, and report absolute + relative activation.
    """

    DEFAULT_ADC_PIN = "P2_35"
    DEFAULT_MAX_VOLTAGE = 3.3  # V on 3.3V-capable analog pin
    DEFAULT_ADC_REF_VOLTAGE = 3.3
    _adc_initialized = False

    def __init__(self, mock: bool = False):
        if mock:
            raise RuntimeError("MuscleSensor mock mode has been removed.")

        if ADC is None:
            raise RuntimeError("Adafruit_BBIO.ADC not available on this device.")

        if not MuscleSensor._adc_initialized:
            ADC.setup()
            MuscleSensor._adc_initialized = True

        requested_pin = os.getenv("MYOWARE_ADC_PIN", self.DEFAULT_ADC_PIN).strip().upper()
        self.adc_pin = self._normalize_pin(requested_pin)
        self.adc_ref_voltage = float(
            os.getenv("MYOWARE_ADC_REF_VOLTAGE", str(self.DEFAULT_ADC_REF_VOLTAGE))
        )
    def _normalize_pin(self, requested: str) -> str:
        """Convert PocketBeagle-style pin names into Adafruit_BBIO ADC channel names."""
        alias_map = {
            "P1_19": "AIN0",
            "P1_21": "AIN1",
            "P1_23": "AIN2",
            "P1_25": "AIN3",
            "P1_27": "AIN4",
            "P2_35": "AIN5",
            "P1_5": "AIN5",
            "P1_3": "AIN6",
        }
        if requested.startswith("AIN"):
            return requested
        return alias_map.get(requested, requested)

        self.reference_voltage = None
        self.rest_voltage = None
        self.max_voltage = None

    def _read_voltage(self) -> float:
        value = float(ADC.read(self.adc_pin))
        return max(0.0, min(1.0, value)) * self.adc_ref_voltage

    def _voltage_to_percent(self, voltage: float) -> float:
        if self.rest_voltage is None or self.max_voltage is None:
            return 0.0
        span = max(self.max_voltage - self.rest_voltage, 1e-3)
        return max(0.0, min(100.0, ((voltage - self.rest_voltage) / span) * 100.0))

    def read(self):
        voltage = self._read_voltage()
        return {
            "voltage": voltage,
            "relative": self._voltage_to_percent(voltage),
            "rest_voltage": self.rest_voltage,
            "peak_voltage": self.max_voltage,
        }

    def calibrate_range(self, mode: str):
        voltage = self._read_voltage()
        if mode == "rest":
            self.rest_voltage = voltage
        elif mode == "max":
            self.max_voltage = max(voltage, (self.rest_voltage or 0) + 1e-3)
        else:
            raise ValueError("mode must be 'rest' or 'max'")
        return {
            "rest_voltage": self.rest_voltage,
            "peak_voltage": self.max_voltage,
        }

    def clear_reference(self):
        self.rest_voltage = None
        self.max_voltage = None
