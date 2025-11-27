from vernier_drop_counter import DripCounter
from cnc_machine import CNC_Machine
from runze_valve import RunzeValve
import time


class FractionCollector:
    counter = None
    cnc_machine = None
    valve_controller = None
    mux_id = None

    def __init__(self, sensor_id=1, runze_valve_port='COM9', runze_valve_address=0, runze_valve_num_port=10, collection_num=3, waste_num=6):
        self.counter = DripCounter(sensor_id=sensor_id)
        self.cnc_machine = CNC_Machine()
        self.valve = RunzeValve(com_port=runze_valve_port, address=runze_valve_address, num_port=runze_valve_num_port)
        self.collection_num = collection_num
        self.waste_num = waste_num
        self.move_to_waste()

    def collect_fraction(self, threshold, location, location_index, rinse_drop = 20, timeout=120, poll_interval=20):
        self.move_to_waste()
        # Rinse collection tubing
        print(f"Rinsing collection tubing for {rinse_drop} drops...\n")
        self.set_valve_state(self.collection_num)  # Set to collection port
        self.counter.wait_for_drops(rinse_drop, timeout=timeout, poll_interval=poll_interval)
        self.set_valve_state(self.waste_num)  # Set to waste port
        print("Rinsing complete.\n")
        # Move to the vial
        self.cnc_machine.move_to_location(location, location_index, safe=True)
        print(f"Collecting fraction at {location} (index {location_index}) until {threshold} drops are counted...\n")
        # Collect fraction
        self.set_valve_state(self.collection_num)  # Set to collection port
        print(f"Starting fraction collection at {location} (index {location_index})...\n")
        if not self.counter.wait_for_drops(threshold, timeout=timeout, poll_interval=poll_interval):
            print(f"Failed to collect enough drops at {location} (index {location_index})...\n")
            # If the threshold is not met, move to waste
            self.move_to_waste() 
            return False
        print(f"Fraction collection of {location} (index {location_index}) complete.\n")

        # Move to the CNC waste location
        self.move_to_waste()

        return True
    def set_valve_state(self, port):
        """Set the valve to a specific port."""
        self.valve.set_current_port(port)

    def move_to_waste(self, location = "cnc_waste_location", location_index=0, safe=True):
        """Close valve and move to the CNC waste location."""
        self.set_valve_state(self.waste_num)
        self.cnc_machine.move_to_location(location, location_index, safe=safe)
        # self.cnc_machine.move_to_point(z=-35)
