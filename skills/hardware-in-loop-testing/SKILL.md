---
name: hardware-in-loop-testing
description: Interface hardware-in-the-loop (HIL) simulation testbeds with embedded firmware endpoints under noise and faults.
---

# Hardware-in-the-Loop (HIL) Testing

Implement hardware-in-the-loop (HIL) simulation test suites, sensor noise injection protocols, hardware fault injection (voltage brownouts, clock jitter, bus disconnects), signal generators (DAQ, CANoe, LabVIEW, PyVISA, SCPI), and automated PASS/FAIL regression testbeds for embedded firmware validation.

The skill is **hardware-safe and SLA-bounded**: instrument connections, power limits, signal ranges, noise models, fault injection triggers, and emergency power-off safety relays are verified before executing test runs.

---

## 1. Required I/O Context Schemas & Natural Language Auto-Inference

The skill supports **two invocation modes**:

1. **🤖 Orchestrator / Technical Mode (JSON Manifest)**: Pass the JSON context manifest below.
2. **💬 Non-Technical Mode (Plain English Prompts)**: If the user provides a natural language prompt (e.g. *"Run a PyVISA HIL test suite injecting 50mV Gaussian white noise on the ADC input of an STM32 MCU and verify 2s recovery after brownout"*), the agent **must automatically infer and populate** `rig_type`, `noise_model`, `fault_type`, and `pass_fail_criteria` from the user's text and testbed environment.

### JSON Context Manifest Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "HilTestingContextManifest",
  "type": "object",
  "required": ["testbed_spec", "test_scenario"],
  "properties": {
    "testbed_spec": {
      "type": "object",
      "required": ["rig_type", "instrument_address"],
      "properties": {
        "rig_type": { 
          "type": "string", 
          "enum": ["benchtop_daq", "can_bus_simulator", "renode_emulator", "custom_pyvisa"] 
        },
        "instrument_address": { "type": "string" },
        "max_voltage_limit": { "type": "number", "default": 3.3 },
        "safety_relay_enabled": { "type": "boolean", "default": true }
      }
    },
    "test_scenario": {
      "type": "object",
      "required": ["noise_model", "fault_type"],
      "properties": {
        "noise_model": { 
          "type": "string", 
          "enum": ["gaussian_white_noise", "impulse_spike", "thermal_drift", "packet_corruption", "none"] 
        },
        "noise_amplitude_v": { "type": "number", "default": 0.05 },
        "fault_type": { 
          "type": "string", 
          "enum": ["voltage_brownout", "bus_disconnection", "clock_jitter", "watchdog_starvation", "none"] 
        },
        "fault_duration_ms": { "type": "integer", "default": 500 }
      }
    },
    "pass_fail_criteria": {
      "type": "object",
      "required": ["max_recovery_latency_ms"],
      "properties": {
        "max_recovery_latency_ms": { "type": "integer", "default": 2000 },
        "allowed_packet_loss_pct": { "type": "number", "default": 0.1 }
      }
    }
  }
}
```

### Automatic Natural Language Inference & Over-Voltage Protection

If no raw JSON payload is provided, apply these defaults and safety checks:

- **Over-Voltage Emergency Clamping**: If `max_voltage_limit` exceeds physical MCU ratings (e.g. $> 3.6\text{V}$ for 3.3V logic), **ABORT execution immediately** and trigger safety clamp `VOLTAGE_EXCEEDS_MCU_RATING`.
- **`rig_type`**: Auto-detected from testbed configuration files (`pyvisa` address, `renode` script, `vector` CANoe setup).
- **`noise_model`**: Defaults to `gaussian_white_noise` with amplitude $0.05\text{V}$.
- **`max_recovery_latency_ms`**: Defaults to $2000\text{ ms}$ (2 seconds).

---

## 2. Deterministic State Machine Execution Flow

Follow this exact sequential protocol. Do not skip steps or alter execution ordering.

### Step 1: Testbed Connection & VISA Instrument Handshake

1. Establish connection to physical or emulated test instruments via PyVISA / SCPI or socket interface (`TCPIP::192.168.1.100::INSTR`, `GPIB::1::INSTR`).
2. Query instrument identification string (`*IDN?`) and set output voltage limits (`VOLT:PROT 3.3`).

### Step 2: Signal Generator Calibration & Noise Synthesis

1. Generate target sensor signals (DAC analog voltages, PWM, CAN/UART message frames).
2. Synthesize noise signals over base sensor outputs:
   - **Gaussian White Noise**: $V_{\text{out}}(t) = V_{\text{base}}(t) + \mathcal{N}(0, \sigma^2)$.
   - **Impulse Spikes**: Periodically inject $0.5\text{V}$ voltage spikes for $10\text{ ms}$ windows.

### Step 3: Test Scenario Execution & Fault Injection

1. **Scenario 1 (Nominal Tracking)**: Sweep sensor inputs from 0% to 100% full-scale; verify firmware output reading accuracy ($\ge 99.5\%$).
2. **Scenario 2 (Sensor Noise & Drift)**: Inject Gaussian noise and thermal drift; verify firmware digital low-pass filtering (Kalman / Moving Average) smooths sensor signals.
3. **Scenario 3 (Bus Disconnect & Timeout)**: Open physical relay or disable CAN transceiver for $500\text{ ms}$; verify firmware detects bus timeout and enters safe state.
4. **Scenario 4 (Voltage Brownout & Self-Reset)**: Drop MCU supply voltage to $2.0\text{V}$ for $200\text{ ms}$; verify Brown-Out Reset (BOR) triggers and MCU successfully recovers within $2.0\text{s}$.

### Step 4: Telemetry Capture & Latency / Recovery Analysis

1. Measure real-time response latency from fault injection timestamp ($t_0$) to firmware recovery signal ($t_{\text{rec}}$):
   $$\Delta t_{\text{recovery}} = t_{\text{rec}} - t_0 \le 2000 \text{ ms}$$
2. Assert that no unhandled hard faults or permanent watchdog deadlocks occurred.

### Step 5: Physical Safety Shutdown & Rig Teardown

1. Zero all DAC signal generator outputs (`OUTPUT OFF`).
2. Open power supply relays and disarm fault injection channels.
3. Disconnect VISA session cleanly.

---

## 3. Reference Implementation: Python / PyVISA & SCPI HIL Test Harness

```python
import time
import math
import random
import pyvisa

class HilTestbedHarness:
    def __init__(self, resource_address: str, max_voltage: float = 3.3):
        self.rm = pyvisa.ResourceManager()
        self.inst = self.rm.open_resource(resource_address)
        self.max_voltage = max_voltage
        self.inst.timeout = 5000 // ms
        
    def setup_safety_limits(self):
        """Configure SCPI voltage limits on programmable power supply / DAQ."""
        self.inst.write(f"VOLT:LIMIT {self.max_voltage}")
        self.inst.write("OUTP ON")
        
    def generate_sensor_signal_with_noise(self, duration_sec: float, noise_sigma: float = 0.05):
        """Inject sine wave sensor signal + Gaussian noise onto DAC output."""
        start_time = time.time()
        print(f"[HIL] Injecting sensor signal with Gaussian noise (sigma={noise_sigma}V)...")
        
        while time.time() - start_time < duration_sec:
            elapsed = time.time() - start_time
            # Base 1.65V centered sine wave (0.5 Hz)
            base_voltage = 1.65 + 1.0 * math.sin(2 * math.pi * 0.5 * elapsed)
            # Add Gaussian noise
            noise = random.gauss(0.0, noise_sigma)
            target_voltage = max(0.0, min(self.max_voltage, base_voltage + noise))
            
            # Apply to DAQ DAC Channel 1 via SCPI
            self.inst.write(f"SOUR:VOLT {target_voltage:.3f}")
            time.sleep(0.01) // 100 Hz sampling rate

    def inject_voltage_brownout(self, drop_voltage: float = 1.8, duration_ms: float = 300) -> float:
        """Inject brownout fault and measure firmware recovery time."""
        print(f"[HIL Fault] Injecting brownout ({drop_voltage}V for {duration_ms}ms)...")
        t_fault = time.time()
        
        # Drop voltage
        self.inst.write(f"SOUR:VOLT {drop_voltage}")
        time.sleep(duration_ms / 1000.0)
        
        # Restore normal voltage
        self.inst.write("SOUR:VOLT 3.3")
        
        # Poll for firmware heartbeat GPIO signal on DAQ Digital Input
        t_recovery = None
        while time.time() - t_fault < 5.0:
            status = self.inst.query("SENS:DIG:DATA?").strip()
            if status == "1": // Firmware GPIO Heartbeat active
                t_recovery = time.time() - t_fault
                break
            time.sleep(0.01)
            
        if t_recovery is None:
            raise RuntimeError("[HIL FAIL] Firmware failed to recover within 5s SLA after brownout.")
            
        print(f"[HIL SUCCESS] Firmware recovered in {t_recovery * 1000.0:.1f} ms.")
        return t_recovery

    def emergency_shutdown(self):
        """Safety Teardown: Zero all outputs and open relays."""
        print("[HIL Safety] Executing emergency shutdown...")
        try:
            self.inst.write("SOUR:VOLT 0.0")
            self.inst.write("OUTP OFF")
            self.inst.close()
        except Exception as e:
            print(f"[HIL Warning] Teardown error: {e}")

if __name__ == "__main__":
    # Example execution against virtual/physical VISA DAQ
    harness = HilTestbedHarness("TCPIP0::127.0.0.1::1883::SOCKET")
    try:
        harness.setup_safety_limits()
        harness.generate_sensor_signal_with_noise(duration_sec=3.0)
        harness.inject_voltage_brownout(drop_voltage=1.8, duration_ms=250)
    finally:
        harness.emergency_shutdown()
```

---

## 4. Real-Time Signal & Recovery Invariants

$$\text{Firmware Fault Recovery Latency: } \Delta t_{\text{recovery}} = t_{\text{recovery}} - t_{\text{fault}} \le 2000 \text{ ms}$$

$$\text{Filtered Signal Accuracy: } |V_{\text{measured\_fw}} - V_{\text{base\_signal}}| \le 0.02 \times V_{\text{max}} \quad (\text{under } \sigma_{\text{noise}} \le 0.05\text{V})$$

$$\text{Safety Relay Trip Time: } t_{\text{trip}} \le 50 \text{ ms} \quad (\text{on over-voltage breach})$$

---

## 5. Guardrails

### Operational Restrictions

- **Mandatory Safety Limits**: Never send voltage commands without setting `VOLT:LIMIT` on power supplies.
- **Automated Teardown**: Always wrap instrument commands in `try...finally` blocks to guarantee `OUTP OFF` execution on failure.
- **Isolated Power Supplies**: Never share HIL signal generator grounds with high-voltage mains without optoisolation.

### Physical Safety Invariants

- **No Over-Voltage Surges**: Over-voltage protection must clamp inputs before exceeding $3.6\text{V}$ for 3.3V logic microcontrollers.
- **Relay Trip Verification**: Emergency relays must be tested before executing fault injection scenarios.

---

## 6. Atomic Failure Recovery & Rollback Handler

If an HIL test case fails or instrument communication drops:

```bash
# Execute emergency instrument shutdown via CLI script
python3 -c "import pyvisa; rm = pyvisa.ResourceManager(); inst = rm.open_resource('TCPIP0::127.0.0.1::1883::SOCKET'); inst.write('OUTP OFF'); inst.write('SOUR:VOLT 0')" 2>/dev/null

# Revert modified test config files
if [ -n "${MODIFIED_FILES:-}" ]; then
  git checkout -- ${MODIFIED_FILES} 2>/dev/null
fi
```

---

## 7. Verification Plan & Toolchain Commands

Execute HIL test suite:

```bash
# 1. Execute pytest HIL regression testbed
pytest tests/hil/test_sensor_faults.py -v

# 2. Run standalone PyVISA harness
python3 scripts/run_hil_harness.py --config config/hil_benchtop.json
```

---

## 8. Completion Report

Report testbed rig type, VISA instrument addresses, noise models injected, fault scenarios tested (brownouts, bus disconnects), firmware recovery latencies, telemetry signal accuracy, and final PASS/FAIL verdict.
