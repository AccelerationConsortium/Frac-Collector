import yaml
from pathlib import Path

YAML_PATH = Path(__file__).parent / "vial_status.yaml"
NUM_VIALS = 48

data = {"vials": [{"index": i, "label": "", "reaction_name": "", "volume_ml": 0.0} for i in range(NUM_VIALS)]}

with open(YAML_PATH, "w") as f:
    yaml.dump(data, f, default_flow_style=False, sort_keys=False)

print(f"Reset {NUM_VIALS} vials in {YAML_PATH}")
