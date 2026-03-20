import yaml
from pathlib import Path

YAML_PATH = Path(__file__).parent / "vial_status.yaml"
NUM_VIALS = 48

def _vial_name(i, num_y=8):
    return chr(ord('A') + i // num_y) + str(i % num_y + 1)

data = {"vials": [{"index": i, "vial_name": _vial_name(i), "label": "", "reaction_name": "", "volume_ml": 0.0} for i in range(NUM_VIALS)]}

with open(YAML_PATH, "w") as f:
    yaml.dump(data, f, default_flow_style=False, sort_keys=False)

print(f"Reset {NUM_VIALS} vials in {YAML_PATH}")
