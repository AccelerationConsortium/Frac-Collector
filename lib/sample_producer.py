import threading
import queue
import time
import pandas as pd
import math
from datetime import datetime
from runze_valve import RunzeValve

class SampleProducer:
    def __init__(
        self,
        reaction_profile_csv,
        sample_queue,
        stop_event,
        tubing_length_m=1.0,
        tubing_id_inch=0.03,
        buffer_factor=1.2
    ):
        self.sample_queue = sample_queue
        self.stop_event = stop_event
        self.tubing_length = tubing_length_m
        self.tubing_id = tubing_id_inch
        self.buffer_factor = buffer_factor

        # Load reaction profile
        self.reaction_profile = pd.read_csv(reaction_profile_csv)
        self.reaction_name = self.reaction_profile['REACTION NAME'][0]
        self.waste_time = float(self.reaction_profile['DIVERT TO WASTE (min)'][0]) * 60  # in seconds
        self.collection_time = float(self.reaction_profile['COLLECT FOR (min)'][0]) * 60  # in seconds
        self.flow_rate = (
            float(self.reaction_profile['FLOW RATE CHEMICAL A (ml/min)'][0]) +
            float(self.reaction_profile['FLOW RATE CHEMICAL B (ml/min)'][0])
        )

        # Hardware control
        self.valve = RunzeValve(com_port='COM8', address=0, num_port=10)
        self.producer_thread = threading.Thread(target=self.run, daemon=True)

    def log(self, message):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def print_summary(self):
        self.log("=== Sample Collection Summary ===")
        self.log(f"Reaction name         : {self.reaction_name}")
        self.log(f"Waste time (s)        : {self.waste_time:.1f}")
        self.log(f"Collection time (s)   : {self.collection_time:.1f}")
        self.log(f"Flow rate (mL/min)    : {self.flow_rate:.2f}")
        self.log(f"Tubing length (m)     : {self.tubing_length}")
        self.log(f"Tubing ID (inch)      : {self.tubing_id}")
        self.log(f"Buffer factor         : {self.buffer_factor}")
        tubing_delay = self.calculate_tubing_delay()
        self.log(f"Tubing delay (s)      : {tubing_delay:.1f}")
        self.log(f"Adjusted waste time   : {(self.waste_time + tubing_delay * self.buffer_factor):.1f} s")
        self.log(f"Adjusted collect time : {(self.collection_time * (1 / self.buffer_factor)):.1f} s")
        self.log("=================================")
        
    def wait_with_timer(self, duration, label="", interval=30):
        start = time.time()
        elapsed = 0
        while elapsed < duration:
            if self.stop_event.is_set():
                self.log("Stop signal received. Exiting timer.")
                return
            time.sleep(min(interval, duration - elapsed))
            elapsed = time.time() - start
            self.log(f"{label}... {int(elapsed)} / {int(duration)} seconds elapsed")
        self.log(f"{label} complete. Total duration: {int(elapsed)} seconds")

    def calculate_tubing_delay(self):
        """Calculate residence time of fluid in tubing (seconds)."""
        d_cm = self.tubing_id * 2.54  # Convert inches to cm
        r_cm = d_cm / 2
        length_cm = self.tubing_length * 100  # meters to cm

        volume_ml = math.pi * (r_cm ** 2) * length_cm  # mL
        delay_time_min = volume_ml / self.flow_rate  # min
        return delay_time_min * 60  # sec

    def start(self):
        self.producer_thread.start()

    def stop(self):
        self.stop_event.set()
        self.producer_thread.join()

    def run(self):
        try:
            start_time = time.time()
            self.print_summary()
            tubing_delay = self.calculate_tubing_delay() * self.buffer_factor
            adjusted_collection_time = self.collection_time * (1 / self.buffer_factor)
            adjusted_waste_time = self.waste_time + tubing_delay
            if self.stop_event.is_set():
                return
            # ⏱️ Waste phase
            self.log(f"Starting waste phase for {adjusted_waste_time:.1f} seconds...")
            self.wait_with_timer(adjusted_waste_time, label="Wasting")
            # ⏱️ Sample ready
            sample_label = f"{self.reaction_name}"
            self.log(f"Sample {sample_label} is ready to collect.")
            self.sample_queue.put(sample_label)
            # ⏱️ Collection phase
            self.log(f"Starting collection phase for {adjusted_collection_time:.1f} seconds...")
            self.wait_with_timer(adjusted_collection_time, label="Collecting")
            # ✅ Done
            total_elapsed = time.time() - start_time
            self.log(f"Sample collection complete. Total elapsed time: {total_elapsed:.1f} seconds ({total_elapsed / 60:.2f} minutes)")

        except Exception as e:
            self.log(f"Error in SampleProducer: {e}")
