# Changelog

## [Unreleased] - 2026-03-19

### Added
- `location_status.yaml` (`well_plate_location`): added `x_step: 2` so the CNC skips every other physical x-column, giving 24 active vial positions (physical cols 0, 2, 4) out of the 48-well plate.
- `cnc_machine.py` (`get_location_position`): reads optional `x_step` from the location config (defaults to 1). Physical column is computed as `logical_col * x_step`; snake direction still alternates on logical column parity so consecutive filled columns zig-zag correctly.

## [Unreleased] - 2026-03-17

### Fixed
- `collect_reaction`: `per_vial_timeout` was incorrectly included in `effective_timeout` even in time-only mode (`use_drops=False`), capping each vial to 10 s and causing premature end of collection (15-20 s of sample lost). In time-only mode `effective_timeout` is now `min(current_fill_time_s, remaining)` — `per_vial_timeout` is only applied as a safety net when using the drop sensor.
- `collect_reaction`: the per-vial abort (`break`) branch now only fires in drop mode. In time-only mode, vials advance on the time-based trigger regardless of `per_vial_timeout`.

## [Unreleased] - 2026-03-12

### Changed
- `collect_fraction`: `threshold` parameter renamed to `threshold_ml` (volume in mL). `rinse_drop` parameter renamed to `rinse_ml` (default `0.16` mL = 20 drops). Both are converted internally to drop counts using `math.floor(ml / 0.008)` (1 drop = 8 µL).
- `workflow_flowreactor.ipynb`: updated `collect_fraction` call arguments from drop counts (140, 70) to mL values (1.12, 0.56).
- `vapourtec_api/API/20260311_SL_synthesis_collection_workflow.ipynb`: renamed `DROP_THRESHOLD` to `DROP_THRESHOLD_ML = 1.6` and updated the `collect_fraction` keyword argument to `threshold_ml`.

### Added
- `FractionCollector.collect_reaction`: new method that collects an entire reaction across consecutive vials. Sets the fraction collector valve to collect at the start of the collection window and to waste at the end. When a vial reaches `threshold_ml`, the CNC moves to the next vial automatically. Collection continues until `collection_duration_s` elapses. Returns a dict with `reaction_name`, `vials_used` (list of indices), `num_vials`, `start_time`, and `end_time`.
- Module constant `DROP_VOLUME_ML = 0.008` in `fraction_collector.py`.
