import yaml
import os

NUM_VIALS = 48
VALID_LABELS = {"GPC", "sample", ""}
DEFAULT_YAML_PATH = os.path.join(os.path.dirname(__file__), "vial_status.yaml")


class VialTracker:
    """Persistent vial tracking for a 48-vial rack.

    The YAML file is created on first use and persists across runs.
    Call reset() explicitly to clear all entries.

    Each vial entry contains:
        index         (int)   — 0-based position in the rack
        reaction_name (str)   — name of the reaction that filled this vial
        label         (str)   — "GPC" | "sample" | "" (empty = unused)
        volume_ml     (float) — volume collected in mL
    """

    def __init__(self, yaml_path: str = DEFAULT_YAML_PATH, num_vials: int = NUM_VIALS):
        self.yaml_path = yaml_path
        self.num_vials = num_vials

        if os.path.exists(yaml_path):
            self._load()
        else:
            self._initialize()
            self._save()
            print(f"Vial tracker created: {self.yaml_path}")

    # ---- Internal ----

    def _initialize(self):
        self.vials = [
            {"index": i, "reaction_name": "", "label": "", "volume_ml": 0.0}
            for i in range(self.num_vials)
        ]

    def _load(self):
        with open(self.yaml_path, "r") as f:
            data = yaml.safe_load(f)
        self.vials = data.get("vials", [])

        # Ensure the list always has exactly num_vials slots
        while len(self.vials) < self.num_vials:
            i = len(self.vials)
            self.vials.append({"index": i, "reaction_name": "", "label": "", "volume_ml": 0.0})
        self.vials = self.vials[: self.num_vials]

    def _save(self):
        with open(self.yaml_path, "w") as f:
            yaml.dump({"vials": self.vials}, f, default_flow_style=False, allow_unicode=True)

    # ---- Public API ----

    def reset(self):
        """Clear reaction_name, label, and volume_ml for all vials. Slot indices are preserved."""
        for vial in self.vials:
            vial["reaction_name"] = ""
            vial["label"] = ""
            vial["volume_ml"] = 0.0
        self._save()
        print(f"Vial tracker reset: {self.num_vials} slots cleared.")

    def update(self, index: int, reaction_name: str, label: str, volume_ml: float):
        """Update a single vial entry and persist to disk.

        Args:
            index:         0-based vial index.
            reaction_name: name of the reaction that filled this vial.
            label:         "GPC" or "sample".
            volume_ml:     volume collected in mL.
        """
        if not 0 <= index < self.num_vials:
            raise IndexError(f"Vial index {index} out of range (0–{self.num_vials - 1})")
        if label not in VALID_LABELS:
            raise ValueError(f"Label must be 'GPC' or 'sample', got {label!r}")

        self.vials[index]["reaction_name"] = reaction_name
        self.vials[index]["label"] = label
        self.vials[index]["volume_ml"] = round(volume_ml, 4)
        self._save()

    def get(self, index: int) -> dict:
        """Return a copy of the vial entry at *index*."""
        if not 0 <= index < self.num_vials:
            raise IndexError(f"Vial index {index} out of range (0–{self.num_vials - 1})")
        return dict(self.vials[index])

    def summary(self) -> list:
        """Return all vial entries that have been labelled (non-empty label)."""
        return [dict(v) for v in self.vials if v["label"]]

    def print_summary(self):
        """Print a formatted table of all labelled vials."""
        filled = self.summary()
        if not filled:
            print("No vials have been recorded yet.")
            return
        print(f"\n{'Index':<8} {'Label':<8} {'Volume (mL)':<14} Reaction")
        print("-" * 50)
        for v in filled:
            print(f"{v['index']:<8} {v['label']:<8} {v['volume_ml']:<14.4f} {v['reaction_name']}")
    def next_available_index(self) -> int:
        """Return the index of the first vial with an empty label (i.e. unused).

        Returns num_vials if all vials are occupied.
        """
        for v in self.vials:
            if not (v.get("label") or "").strip():
                return v["index"]
        return self.num_vials