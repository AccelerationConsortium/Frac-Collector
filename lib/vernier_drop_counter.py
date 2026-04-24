import time
from gdx import GDX

class DripCounter:
    def __init__(self, sensor_id=1):
        self.available = False
        self.device = GDX()
        try:
            self.sensor_type = "GDX-DC 05501561"
            self.device.open(connection='usb', device_to_open=self.sensor_type)
            self.device.select_sensors(sensor_id)
            info = self.device.enabled_sensor_info()
            if info and info[0]:
                self.available = True
                print(f"Drop counter ready: {info[0]}")
            else:
                print("Drop counter: no sensor info returned. Falling back to time-based mode.")
        except Exception as ex:
            print(f"Drop counter not available ({ex}). Falling back to time-based mode.")

    def wait_for_drops(self, threshold, timeout=None, poll_interval=20):
        if not self.available:
            return False
        self.device.start(poll_interval)
        info = self.device.enabled_sensor_info()
        if not info or not info[0]:
            print("Drop counter: sensor info lost during collection. Falling back to time-based mode.")
            self.available = False
            self.device.stop()
            return False
        print(info[0], "Started")
        drops = 0
        start_time = time.time()
        while drops < threshold:
            measurements = self.device.read()
            if measurements is None:
                print("Warning: Drop interval > 5s")
                continue
            drops += 1
            print(drops)
            time.sleep(0.01)
            if timeout is not None and (time.time() - start_time) > timeout:
                print("Timeout reached.")
                self.device.stop()
                return False
        self.device.stop()
        return True