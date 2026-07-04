#!/usr/bin/env python3
"""
Generates a KiCad 8 schematic (.kicad_sch) for the RoboCar project.

Maps all hardware connections to the Raspberry Pi 4:
  - 3x HC-SR04 ultrasonic sensors (GPIO)
  - PCA9685 16-ch servo driver (I2C) -> 2 motors + 1 steering servo
  - INA3221 battery monitor (I2C, 0x40)
  - INA226 current sensor (I2C, 0x44)
  - MPU6050 IMU (I2C, 0x68)
  - USB camera (/dev/video0, 640x480)
  - Emergency stop switch (GPIO6)

Usage:
    python3 hardware/generate_schematic.py

Output:
    hardware/robocar_schematic.kicad_sch
"""

import os
import uuid as _uuid

# ─── Constants ───────────────────────────────────────────────────────────────

PIN_LEN = 2.54
PIN_STEP = 2.54
FONT = 1.27
WIRE_STUB = 10.16


def uid():
    return str(_uuid.uuid4())


# ─── Component Definitions ──────────────────────────────────────────────────


def _pins(*args):
    """Build pin list from (name, number, electrical_type, side) tuples."""
    return [dict(name=a[0], num=str(a[1]), type=a[2], side=a[3]) for a in args]


COMPONENTS = {
    "RPi": {
        "ref": "U",
        "value": "Raspberry Pi 4",
        "width": 30.48,
        "pins": _pins(
            ("3V3", 1, "power_out", "left"),
            ("5V", 2, "power_out", "left"),
            ("SDA1 (GPIO2)", 3, "bidirectional", "left"),
            ("SCL1 (GPIO3)", 5, "output", "left"),
            ("GND", 6, "passive", "left"),
            ("USB", "U", "bidirectional", "left"),
            ("GPIO6 (E-Stop)", 31, "input", "right"),
            ("GPIO12 (TRIG_C)", 32, "output", "right"),
            ("GPIO13 (ECHO_C)", 33, "input", "right"),
            ("GPIO16 (ECHO_L)", 36, "input", "right"),
            ("GPIO19 (TRIG_L)", 35, "output", "right"),
            ("GPIO20 (ECHO_R)", 38, "input", "right"),
            ("GPIO26 (TRIG_R)", 37, "output", "right"),
        ),
    },
    "HC_SR04": {
        "ref": "U",
        "value": "HC-SR04",
        "width": 15.24,
        "pins": _pins(
            ("VCC", 1, "power_in", "left"),
            ("TRIG", 2, "input", "left"),
            ("ECHO", 3, "output", "left"),
            ("GND", 4, "passive", "left"),
        ),
    },
    "PCA9685": {
        "ref": "U",
        "value": "PCA9685 / ServoKit",
        "width": 20.32,
        "pins": _pins(
            ("VCC", 1, "power_in", "left"),
            ("SDA", 2, "bidirectional", "left"),
            ("SCL", 3, "input", "left"),
            ("GND", 4, "passive", "left"),
            ("V+", 5, "power_in", "left"),
            ("CH0 (Motor1)", 6, "output", "right"),
            ("CH1 (Motor2)", 7, "output", "right"),
            ("CH2 (Steer)", 8, "output", "right"),
        ),
    },
    "INA3221": {
        "ref": "U",
        "value": "INA3221 (0x40)",
        "width": 20.32,
        "pins": _pins(
            ("VS", 1, "power_in", "left"),
            ("SDA", 2, "bidirectional", "left"),
            ("SCL", 3, "input", "left"),
            ("GND", 4, "passive", "left"),
            ("CH1+", 5, "input", "right"),
            ("CH1-", 6, "input", "right"),
            ("CH2+", 7, "input", "right"),
            ("CH2-", 8, "input", "right"),
            ("CH3+", 9, "input", "right"),
            ("CH3-", 10, "input", "right"),
        ),
    },
    "INA226": {
        "ref": "U",
        "value": "INA226 (0x44)",
        "width": 15.24,
        "pins": _pins(
            ("VS", 1, "power_in", "left"),
            ("SDA", 2, "bidirectional", "left"),
            ("SCL", 3, "input", "left"),
            ("GND", 4, "passive", "left"),
            ("IN+", 5, "input", "right"),
            ("IN-", 6, "input", "right"),
        ),
    },
    "MPU6050": {
        "ref": "U",
        "value": "MPU6050 (0x68)",
        "width": 15.24,
        "pins": _pins(
            ("VCC", 1, "power_in", "left"),
            ("SDA", 2, "bidirectional", "left"),
            ("SCL", 3, "input", "left"),
            ("GND", 4, "passive", "left"),
        ),
    },
    "Camera": {
        "ref": "J",
        "value": "USB Camera 640x480",
        "width": 17.78,
        "pins": _pins(
            ("USB", 1, "bidirectional", "left"),
            ("GND", 2, "passive", "left"),
        ),
    },
    "Motor": {
        "ref": "M",
        "value": "DC Motor (ESC)",
        "width": 12.7,
        "pins": _pins(
            ("Signal", 1, "input", "left"),
            ("V+", 2, "power_in", "left"),
            ("GND", 3, "passive", "left"),
        ),
    },
    "Servo": {
        "ref": "M",
        "value": "Steering Servo",
        "width": 12.7,
        "pins": _pins(
            ("Signal", 1, "input", "left"),
            ("V+", 2, "power_in", "left"),
            ("GND", 3, "passive", "left"),
        ),
    },
    "Switch": {
        "ref": "SW",
        "value": "Emergency Stop",
        "width": 12.7,
        "pins": _pins(
            ("IN", 1, "input", "left"),
            ("GND", 2, "passive", "left"),
        ),
    },
}


# ─── KiCad Schematic Writer ─────────────────────────────────────────────────


class Schematic:
    def __init__(self):
        self.file_uuid = uid()
        self.defs = {}
        self.instances = []
        self.wires = []
        self.labels = []
        self.glabels = []
        self.texts = []

    def register(self, key, defn):
        self.defs[key] = defn

    def place(self, key, ref, value, x, y):
        inst = dict(key=key, ref=ref, value=value, x=x, y=y, uuid=uid())
        self.instances.append(inst)
        return inst

    # ── pin helpers ──────────────────────────────────────────────────────

    def _sides(self, key):
        d = self.defs[key]
        left = [p for p in d["pins"] if p["side"] == "left"]
        right = [p for p in d["pins"] if p["side"] == "right"]
        return left, right

    def _body(self, key):
        d = self.defs[key]
        left, right = self._sides(key)
        hw = d["width"] / 2
        n = max(len(left), len(right), 1)
        hh = (n * PIN_STEP + PIN_STEP) / 2
        return hw, hh

    def _pin_local(self, key, pin_name):
        left, right = self._sides(key)
        hw = self.defs[key]["width"] / 2
        for group, is_right in [(left, False), (right, True)]:
            n = len(group)
            for i, p in enumerate(group):
                if p["name"] == pin_name:
                    ly = (n - 1) / 2 * PIN_STEP - i * PIN_STEP
                    lx = (hw + PIN_LEN) if is_right else -(hw + PIN_LEN)
                    return lx, ly, is_right
        raise KeyError(f"Pin '{pin_name}' not found in component '{key}'")

    def pin_xy(self, inst, pin_name):
        lx, ly, _ = self._pin_local(inst["key"], pin_name)
        return inst["x"] + lx, inst["y"] - ly

    def connect(self, inst, pin_name, net, glob=False, shape="bidirectional"):
        """Add wire stub + label from a pin to a named net."""
        px, py = self.pin_xy(inst, pin_name)
        _, _, is_right = self._pin_local(inst["key"], pin_name)
        if is_right:
            wx, angle = px + WIRE_STUB, 0
        else:
            wx, angle = px - WIRE_STUB, 180
        self.wires.append((px, py, wx, py))
        entry = dict(text=net, x=wx, y=py, angle=angle)
        if glob:
            entry["shape"] = shape
            self.glabels.append(entry)
        else:
            self.labels.append(entry)

    def note(self, text, x, y, sz=3.0):
        self.texts.append(dict(text=text, x=x, y=y, sz=sz))

    # ── rendering ────────────────────────────────────────────────────────

    def _render_lib(self, key):
        d = self.defs[key]
        left, right = self._sides(key)
        hw, hh = self._body(key)
        lid = f"robocar:{key}"
        o = []

        o.append(f'    (symbol "{lid}"')
        o.append(
            f"      (pin_names (offset 1.016)) (in_bom yes) (on_board yes)"
        )
        o.append(
            f'      (property "Reference" "{d["ref"]}"'
            f" (at 0 {hh + 2.54:.2f} 0)"
            f" (effects (font (size {FONT} {FONT}))))"
        )
        o.append(
            f'      (property "Value" "{d["value"]}"'
            f" (at 0 {-(hh + 2.54):.2f} 0)"
            f" (effects (font (size {FONT} {FONT}))))"
        )
        o.append(
            f'      (property "Footprint" "" (at 0 0 0)'
            f" (effects (font (size {FONT} {FONT})) hide))"
        )
        o.append(
            f'      (property "Datasheet" "" (at 0 0 0)'
            f" (effects (font (size {FONT} {FONT})) hide))"
        )

        # Body rectangle
        o.append(f'      (symbol "{key}_0_1"')
        o.append(
            f"        (rectangle"
            f" (start {-hw:.2f} {hh:.2f}) (end {hw:.2f} {-hh:.2f})"
        )
        o.append(
            f"          (stroke (width 0.254) (type default))"
            f" (fill (type background)))"
        )
        o.append(f"      )")

        # Pins
        o.append(f'      (symbol "{key}_1_1"')
        for group, is_right in [(left, False), (right, True)]:
            n = len(group)
            for i, p in enumerate(group):
                py = (n - 1) / 2 * PIN_STEP - i * PIN_STEP
                if is_right:
                    px, ang = hw + PIN_LEN, 180
                else:
                    px, ang = -(hw + PIN_LEN), 0
                o.append(
                    f"        (pin {p['type']} line"
                    f" (at {px:.2f} {py:.2f} {ang})"
                    f" (length {PIN_LEN})"
                )
                o.append(
                    f"          (name \"{p['name']}\""
                    f" (effects (font (size {FONT} {FONT}))))"
                )
                o.append(
                    f"          (number \"{p['num']}\""
                    f" (effects (font (size {FONT} {FONT})))))"
                )
        o.append(f"      )")
        o.append(f"    )")
        return "\n".join(o)

    def _render_inst(self, inst):
        d = self.defs[inst["key"]]
        _, hh = self._body(inst["key"])
        lid = f'robocar:{inst["key"]}'
        ix, iy = inst["x"], inst["y"]
        o = []

        o.append(
            f'  (symbol (lib_id "{lid}")'
            f" (at {ix:.2f} {iy:.2f} 0) (unit 1)"
        )
        o.append(f"    (in_bom yes) (on_board yes) (dnp no)")
        o.append(f'    (uuid "{inst["uuid"]}")')
        o.append(
            f'    (property "Reference" "{inst["ref"]}"'
            f" (at {ix:.2f} {iy - hh - 3.81:.2f} 0)"
            f" (effects (font (size {FONT} {FONT}))))"
        )
        o.append(
            f'    (property "Value" "{inst["value"]}"'
            f" (at {ix:.2f} {iy + hh + 3.81:.2f} 0)"
            f" (effects (font (size {FONT} {FONT}))))"
        )
        o.append(
            f'    (property "Footprint" ""'
            f" (at {ix:.2f} {iy:.2f} 0)"
            f" (effects (font (size {FONT} {FONT})) hide))"
        )
        o.append(
            f'    (property "Datasheet" ""'
            f" (at {ix:.2f} {iy:.2f} 0)"
            f" (effects (font (size {FONT} {FONT})) hide))"
        )

        for p in d["pins"]:
            o.append(f'    (pin "{p["num"]}" (uuid "{uid()}"))')

        o.append(f"  )")
        return "\n".join(o)

    def generate(self, filepath):
        """Write the complete .kicad_sch file."""
        o = []

        # Header
        o.append("(kicad_sch")
        o.append("  (version 20231120)")
        o.append('  (generator "robocar_generator")')
        o.append('  (generator_version "1.0")')
        o.append(f'  (uuid "{self.file_uuid}")')
        o.append('  (paper "A3")')
        o.append("")

        # Title block
        o.append("  (title_block")
        o.append('    (title "RoboCar - Hardware Connections")')
        o.append('    (date "2026-05-12")')
        o.append('    (rev "1.0")')
        o.append(
            '    (comment 1 "Raspberry Pi 4 - GPIO, I2C (Bus 1), USB")'
        )
        o.append(
            '    (comment 2 "Auto-generated — hardware/generate_schematic.py")'
        )
        o.append("  )")
        o.append("")

        # Library symbols
        used = set(inst["key"] for inst in self.instances)
        o.append("  (lib_symbols")
        for key in used:
            o.append(self._render_lib(key))
        o.append("  )")
        o.append("")

        # Text annotations
        for t in self.texts:
            o.append(f'  (text "{t["text"]}"')
            o.append(f'    (at {t["x"]:.2f} {t["y"]:.2f} 0)')
            o.append(
                f'    (effects (font (size {t["sz"]} {t["sz"]})))'
            )
            o.append(f"  )")

        # Global labels
        for gl in self.glabels:
            o.append(f'  (global_label "{gl["text"]}"')
            o.append(f'    (shape {gl["shape"]})')
            o.append(
                f'    (at {gl["x"]:.2f} {gl["y"]:.2f} {gl["angle"]})'
            )
            o.append(f"    (effects (font (size {FONT} {FONT})))")
            o.append(f'    (uuid "{uid()}")')
            o.append(
                f'    (property "Intersheetref" "${{INTERSHEET_REFS}}"'
                f" (at 0 0 0)"
                f" (effects (font (size {FONT} {FONT})) hide))"
            )
            o.append(f"  )")

        # Net labels
        for lb in self.labels:
            o.append(f'  (label "{lb["text"]}"')
            o.append(
                f'    (at {lb["x"]:.2f} {lb["y"]:.2f} {lb["angle"]})'
            )
            o.append(f"    (effects (font (size {FONT} {FONT})))")
            o.append(f'    (uuid "{uid()}")')
            o.append(f"  )")

        # Wires
        for x1, y1, x2, y2 in self.wires:
            o.append(
                f"  (wire (pts"
                f" (xy {x1:.2f} {y1:.2f}) (xy {x2:.2f} {y2:.2f}))"
            )
            o.append(f"    (stroke (width 0) (type default))")
            o.append(f'    (uuid "{uid()}")')
            o.append(f"  )")

        # Symbol instances
        for inst in self.instances:
            o.append(self._render_inst(inst))

        # Sheet instances (required by KiCad 8)
        o.append("")
        o.append("  (sheet_instances")
        o.append('    (path "/"')
        o.append('      (page "1"))')
        o.append("  )")

        # Symbol instance paths (required by KiCad 8)
        o.append("  (symbol_instances")
        for inst in self.instances:
            o.append(f'    (path "/{inst["uuid"]}"')
            o.append(f'      (reference "{inst["ref"]}") (unit 1))')
        o.append("  )")

        o.append(")")

        with open(filepath, "w") as f:
            f.write("\n".join(o) + "\n")
        print(f"Generated: {filepath}")


# ─── Main: Layout & Connections ──────────────────────────────────────────────


def main():
    sch = Schematic()

    for key, defn in COMPONENTS.items():
        sch.register(key, defn)

    # ── Place Components ─────────────────────────────────────────────────

    # Raspberry Pi (center)
    rpi = sch.place("RPi", "U1", "Raspberry Pi 4", 200, 148)

    # I2C devices (left column)
    mpu = sch.place("MPU6050", "U2", "MPU6050 (0x68)", 65, 68)
    ina3221 = sch.place("INA3221", "U3", "INA3221 (0x40)", 65, 138)
    ina226 = sch.place("INA226", "U4", "INA226 (0x44)", 65, 208)
    pca = sch.place("PCA9685", "U5", "PCA9685 / ServoKit", 160, 250)

    # HC-SR04 sensors (right column)
    hc_l = sch.place("HC_SR04", "U6", "HC-SR04 Left (Green)", 340, 78)
    hc_r = sch.place("HC_SR04", "U7", "HC-SR04 Right (Yellow)", 340, 128)
    hc_c = sch.place("HC_SR04", "U8", "HC-SR04 Center (Red)", 340, 178)

    # Emergency stop (right bottom)
    sw = sch.place("Switch", "SW1", "Emergency Stop", 340, 230)

    # Camera (top center)
    cam = sch.place("Camera", "J1", "USB Camera 640x480", 200, 40)

    # Actuators (bottom row)
    m1 = sch.place("Motor", "M1", "Motor 1 (CH0)", 280, 280)
    m2 = sch.place("Motor", "M2", "Motor 2 (CH1)", 280, 310)
    srv = sch.place("Servo", "M3", "Steering Servo (CH2)", 280, 340)

    # ── I2C Bus ──────────────────────────────────────────────────────────

    sch.connect(rpi, "SDA1 (GPIO2)", "SDA", glob=True)
    sch.connect(rpi, "SCL1 (GPIO3)", "SCL", glob=True)

    for dev in (mpu, ina3221, ina226, pca):
        sch.connect(dev, "SDA", "SDA", glob=True)
        sch.connect(dev, "SCL", "SCL", glob=True)

    # ── Power Rails ──────────────────────────────────────────────────────

    sch.connect(rpi, "3V3", "3V3", glob=True, shape="passive")
    sch.connect(rpi, "5V", "5V", glob=True, shape="passive")
    sch.connect(rpi, "GND", "GND", glob=True, shape="passive")

    # I2C device power
    sch.connect(mpu, "VCC", "3V3", glob=True, shape="passive")
    sch.connect(mpu, "GND", "GND", glob=True, shape="passive")

    for dev in (ina3221, ina226):
        sch.connect(dev, "VS", "5V", glob=True, shape="passive")
        sch.connect(dev, "GND", "GND", glob=True, shape="passive")

    sch.connect(pca, "VCC", "3V3", glob=True, shape="passive")
    sch.connect(pca, "GND", "GND", glob=True, shape="passive")
    sch.connect(pca, "V+", "V_SERVO", glob=True, shape="passive")

    # ── GPIO: HC-SR04 ────────────────────────────────────────────────────

    # Left sensor (GPIO19=TRIG, GPIO16=ECHO)
    sch.connect(hc_l, "TRIG", "GPIO19_TRIG_L")
    sch.connect(hc_l, "ECHO", "GPIO16_ECHO_L")
    sch.connect(hc_l, "VCC", "5V", glob=True, shape="passive")
    sch.connect(hc_l, "GND", "GND", glob=True, shape="passive")

    # Right sensor (GPIO26=TRIG, GPIO20=ECHO)
    sch.connect(hc_r, "TRIG", "GPIO26_TRIG_R")
    sch.connect(hc_r, "ECHO", "GPIO20_ECHO_R")
    sch.connect(hc_r, "VCC", "5V", glob=True, shape="passive")
    sch.connect(hc_r, "GND", "GND", glob=True, shape="passive")

    # Center sensor (GPIO12=TRIG, GPIO13=ECHO)
    sch.connect(hc_c, "TRIG", "GPIO12_TRIG_C")
    sch.connect(hc_c, "ECHO", "GPIO13_ECHO_C")
    sch.connect(hc_c, "VCC", "5V", glob=True, shape="passive")
    sch.connect(hc_c, "GND", "GND", glob=True, shape="passive")

    # RPi side of GPIO connections
    sch.connect(rpi, "GPIO19 (TRIG_L)", "GPIO19_TRIG_L")
    sch.connect(rpi, "GPIO16 (ECHO_L)", "GPIO16_ECHO_L")
    sch.connect(rpi, "GPIO26 (TRIG_R)", "GPIO26_TRIG_R")
    sch.connect(rpi, "GPIO20 (ECHO_R)", "GPIO20_ECHO_R")
    sch.connect(rpi, "GPIO12 (TRIG_C)", "GPIO12_TRIG_C")
    sch.connect(rpi, "GPIO13 (ECHO_C)", "GPIO13_ECHO_C")

    # ── GPIO: Emergency Stop ─────────────────────────────────────────────

    sch.connect(rpi, "GPIO6 (E-Stop)", "GPIO6_ESTOP")
    sch.connect(sw, "IN", "GPIO6_ESTOP")
    sch.connect(sw, "GND", "GND", glob=True, shape="passive")

    # ── USB Camera ───────────────────────────────────────────────────────

    sch.connect(rpi, "USB", "USB_CAM")
    sch.connect(cam, "USB", "USB_CAM")
    sch.connect(cam, "GND", "GND", glob=True, shape="passive")

    # ── PCA9685 -> Actuators ─────────────────────────────────────────────

    sch.connect(pca, "CH0 (Motor1)", "PCA_CH0")
    sch.connect(pca, "CH1 (Motor2)", "PCA_CH1")
    sch.connect(pca, "CH2 (Steer)", "PCA_CH2")

    sch.connect(m1, "Signal", "PCA_CH0")
    sch.connect(m1, "V+", "V_SERVO", glob=True, shape="passive")
    sch.connect(m1, "GND", "GND", glob=True, shape="passive")

    sch.connect(m2, "Signal", "PCA_CH1")
    sch.connect(m2, "V+", "V_SERVO", glob=True, shape="passive")
    sch.connect(m2, "GND", "GND", glob=True, shape="passive")

    sch.connect(srv, "Signal", "PCA_CH2")
    sch.connect(srv, "V+", "V_SERVO", glob=True, shape="passive")
    sch.connect(srv, "GND", "GND", glob=True, shape="passive")

    # ── INA3221 sense inputs (batteries) ─────────────────────────────────

    sch.connect(ina3221, "CH1+", "BAT1+")
    sch.connect(ina3221, "CH1-", "BAT1-")
    sch.connect(ina3221, "CH2+", "BAT2+")
    sch.connect(ina3221, "CH2-", "BAT2-")
    sch.connect(ina3221, "CH3+", "BAT3+")
    sch.connect(ina3221, "CH3-", "BAT3-")

    # ── INA226 sense inputs (load current) ───────────────────────────────

    sch.connect(ina226, "IN+", "LOAD+")
    sch.connect(ina226, "IN-", "LOAD-")

    # ── Annotations ──────────────────────────────────────────────────────

    sch.note("I2C Bus 1", 65, 38, sz=4.0)
    sch.note("GPIO Connections", 340, 55, sz=4.0)
    sch.note("Actuators (PCA9685 PWM)", 280, 263, sz=3.0)
    sch.note(
        "Note: INA3221 default addr = 0x40,"
        " same as PCA9685. Verify HW config.",
        30,
        290,
        sz=2.0,
    )

    # ── Generate ─────────────────────────────────────────────────────────

    out = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "robocar_schematic.kicad_sch",
    )
    sch.generate(out)


if __name__ == "__main__":
    main()
