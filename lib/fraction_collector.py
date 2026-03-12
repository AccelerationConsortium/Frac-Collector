from vernier_drop_counter import DripCounter
from cnc_machine import CNC_Machine
from runze_valve import RunzeValve
import time
import math

DROP_VOLUME_ML = 0.008  # 1 drop = 8 µL = 0.008 mL


class FractionCollector:
    counter = None
    cnc_machine = None
    valve_controller = None
    mux_id = None

    def __init__(self, sensor_id=1, runze_valve_port='COM7', runze_valve_address=0, runze_valve_num_port=10, collection_num=3, waste_num=6):
        try:
            self.counter = DripCounter(sensor_id=sensor_id)
        except Exception as ex:
            print(f"Drop counter initialisation failed ({ex}). Falling back to time-based mode.")
            self.counter = None
        self.cnc_machine = CNC_Machine()
        self.valve = RunzeValve(com_port=runze_valve_port, address=runze_valve_address, num_port=runze_valve_num_port)
        self.collection_num = collection_num
        self.waste_num = waste_num
        self.move_to_waste()

    def collect_fraction(self, threshold_ml, location, location_index, rinse_ml=0.16, timeout=120, poll_interval=20):
        use_drops = self.counter is not None and getattr(self.counter, 'available', False)
        threshold = math.floor(threshold_ml / DROP_VOLUME_ML)
        rinse_drops = math.floor(rinse_ml / DROP_VOLUME_ML)

        self.move_to_waste()
        # Rinse collection tubing
        print(f"Rinsing collection tubing for {rinse_ml:.3f} mL...\n")
        self.set_valve_state(self.collection_num)
        if use_drops:
            self.counter.wait_for_drops(rinse_drops, timeout=timeout, poll_interval=poll_interval)
        else:
            time.sleep(rinse_ml / DROP_VOLUME_ML * 0.5)  # rough timed rinse when no sensor
        self.set_valve_state(self.waste_num)
        print("Rinsing complete.\n")
        # Move to the vial
        self.cnc_machine.move_to_location(location, location_index, safe=True)
        print(f"Collecting fraction at {location} (index {location_index}) until {threshold_ml} mL...\n")
        # Collect fraction
        self.set_valve_state(self.collection_num)
        print(f"Starting fraction collection at {location} (index {location_index})...\n")
        if use_drops:
            success = self.counter.wait_for_drops(threshold, timeout=timeout, poll_interval=poll_interval)
        else:
            time.sleep(timeout)
            success = True  # assume filled after timeout when no sensor
        if not success:
            print(f"Failed to collect enough drops at {location} (index {location_index})...\n")
            self.move_to_waste()
            return False
        print(f"Fraction collection of {location} (index {location_index}) complete.\n")

        # Move to the CNC waste location
        self.move_to_waste()

        return True

    def collect_reaction(self, reaction_name, threshold_ml, location, start_index,
                         collection_duration_s, flow_rate_ml_min=0.0, rinse_ml=0.16,
                         per_vial_timeout=300, poll_interval=20):
        """
        Collect an entire reaction across consecutive vials.

        Each vial switches when the drop threshold OR the flow-rate-derived time
        limit is reached — whichever comes first.  The hard per_vial_timeout acts
        as a safety net in case both primary triggers fail.

        Args:
            reaction_name:         identifier used for logging and the returned record.
            threshold_ml:          volume per vial in mL.
            location:              CNC location name for the vial rack.
            start_index:           index of the first vial to fill.
            collection_duration_s: total seconds of the collection window.
            flow_rate_ml_min:      total system flow rate (mL/min) used to compute the
                                   expected fill time per vial.  Set to 0 to disable
                                   time-based switching (drops-only fallback).
            rinse_ml:              volume to rinse the transfer tubing before opening
                                   the collection window (default 0.16 mL = 20 drops).
            per_vial_timeout:      hard maximum seconds per vial; only fires if both
                                   drop and time triggers fail (default 300 s).
            poll_interval:         drop-counter polling interval in ms.

        Returns:
            dict: {
                "reaction_name": str,
                "vials_used":    list[int],   # vial indices that received liquid
                "num_vials":     int,
                "start_time":    float,        # epoch seconds
                "end_time":      float,
            }
        """
        use_drops = self.counter is not None and getattr(self.counter, 'available', False)
        threshold_drops = math.floor(threshold_ml / DROP_VOLUME_ML)
        rinse_drops = math.floor(rinse_ml / DROP_VOLUME_ML)

        # Time-based vial fill limit derived from flow rate
        if flow_rate_ml_min > 0:
            vial_fill_time_s = (threshold_ml / flow_rate_ml_min) * 60
            if use_drops:
                print(
                    f"[{reaction_name}] Dual-trigger per vial: "
                    f"{threshold_drops} drops OR {vial_fill_time_s:.1f} s "
                    f"({threshold_ml:.2f} mL at {flow_rate_ml_min:.2f} mL/min). "
                    f"Hard timeout: {per_vial_timeout} s.\n"
                )
            else:
                print(
                    f"[{reaction_name}] Time-only mode (no drop sensor): "
                    f"{vial_fill_time_s:.1f} s per vial "
                    f"({threshold_ml:.2f} mL at {flow_rate_ml_min:.2f} mL/min). "
                    f"Hard timeout: {per_vial_timeout} s.\n"
                )
        else:
            vial_fill_time_s = None
            if use_drops:
                print(f"[{reaction_name}] Drop-only trigger per vial: {threshold_drops} drops. Hard timeout: {per_vial_timeout} s.\n")
            else:
                print(f"[{reaction_name}] WARNING: no drop sensor and no flow rate — time-based vial switching unavailable.\n")

        # Rinse before opening the collection window
        self.move_to_waste()
        print(f"[{reaction_name}] Rinsing collection tubing for {rinse_ml:.3f} mL...\n")
        self.set_valve_state(self.collection_num)
        if use_drops:
            self.counter.wait_for_drops(rinse_drops, timeout=per_vial_timeout, poll_interval=poll_interval)
        else:
            rinse_time_s = (rinse_ml / flow_rate_ml_min * 60) if flow_rate_ml_min > 0 else 10.0
            time.sleep(rinse_time_s)
        self.set_valve_state(self.waste_num)
        print(f"[{reaction_name}] Rinsing complete.\n")

        # Start collection window timer
        collection_start = time.time()
        print(
            f"[{reaction_name}] Starting reaction collection. "
            f"Collection window: {collection_duration_s:.1f} s.\n"
        )

        vials_used = []
        loc_index = start_index

        while True:
            remaining = collection_duration_s - (time.time() - collection_start)
            if remaining <= 0:
                break

            self.cnc_machine.move_to_location(location, loc_index, safe=True)

            remaining = collection_duration_s - (time.time() - collection_start)
            if remaining <= 0:
                break

            self.set_valve_state(self.collection_num)

            if vial_fill_time_s is not None:
                effective_timeout = min(per_vial_timeout, vial_fill_time_s, remaining)
            else:
                effective_timeout = min(per_vial_timeout, remaining)

            print(
                f"[{reaction_name}] Filling vial {loc_index} "
                f"(switch at {threshold_drops} drops OR {effective_timeout:.0f} s, "
                f"{remaining:.0f} s left in window)...\n"
            )

            vial_start = time.time()
            if use_drops:
                success = self.counter.wait_for_drops(
                    threshold_drops,
                    timeout=effective_timeout,
                    poll_interval=poll_interval,
                )
            else:
                time.sleep(effective_timeout)
                success = False
            vial_elapsed = time.time() - vial_start
            vials_used.append(loc_index)
            loc_index += 1

            if success:
                print(f"[{reaction_name}] Vial {loc_index - 1}: drop threshold reached ({threshold_drops} drops). Moving to next vial.\n")
                self.set_valve_state(self.waste_num)
            else:
                remaining_after = collection_duration_s - (time.time() - collection_start)
                if remaining_after <= 0:
                    print(f"[{reaction_name}] Vial {loc_index - 1}: collection window closed.\n")
                    break
                if vial_fill_time_s is not None and vial_elapsed < per_vial_timeout - 2:
                    # Flow-rate time limit fired before the hard timeout
                    print(f"[{reaction_name}] Vial {loc_index - 1}: time limit ({vial_fill_time_s:.0f} s) reached. Moving to next vial.\n")
                    self.set_valve_state(self.waste_num)
                else:
                    # Hard per-vial timeout — unexpected; abort collection
                    print(f"[{reaction_name}] Vial {loc_index - 1}: per-vial timeout ({per_vial_timeout} s) exceeded. Ending collection.\n")
                    break

        # Close collection valve — end of collection window
        self.set_valve_state(self.waste_num)

        result = {
            "reaction_name": reaction_name,
            "vials_used": vials_used,
            "num_vials": len(vials_used),
            "start_time": collection_start,
            "end_time": time.time(),
        }
        print(
            f"[{reaction_name}] Reaction collection complete. "
            f"{len(vials_used)} vial(s) used at indices {vials_used}.\n"
        )
        return result


    def set_valve_state(self, port):
        """Set the valve to a specific port."""
        self.valve.set_current_port(port)

    def move_to_waste(self, location = "cnc_waste_location", location_index=0, safe=True):
        """Close valve and move to the CNC waste location."""
        self.set_valve_state(self.waste_num)
        self.cnc_machine.move_to_location(location, location_index, safe=safe)
        # self.cnc_machine.move_to_point(z=-35)
