import time
from gdx import gdx

class DripCounter:
    def __init__(self, sensor_id=1):
        self.device = gdx.gdx()
        self.sensor_type = "GDX-DC 05501561"
        self.device.open(connection='usb', device_to_open=self.sensor_type)
        self.device.select_sensors(sensor_id)

    def wait_for_drops(self, threshold, timeout = None, poll_interval=20):
        self.device.start(poll_interval)
        column_headers = self.device.enabled_sensor_info()[0]
        print(column_headers, "Started")
        drops = 0
        start_time = time.time()
        while drops < threshold:
            measurements = self.device.read()
            if measurements == None:
                drops += 0
                print("Warning: Drop interval > 5s")
                continue
            drops += 1
            print(drops)
            time.sleep(0.01)
            if timeout is not None and (time.time() - start_time) > timeout:
                print("Timeout reached.")
                return False
        self.device.stop()
        return True