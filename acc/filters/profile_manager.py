import os
import yaml
from typing import Dict, Any

class ProfileManager:
    def __init__(self, profiles_dir: str = None):
        if profiles_dir is None:
            # Default to acc/profiles/
            base_dir = os.path.dirname(os.path.dirname(__file__))
            self.profiles_dir = os.path.join(base_dir, "profiles")
        else:
            self.profiles_dir = profiles_dir
            
    def load_profile(self, name: str) -> Dict[str, Any]:
        """Loads a YAML profile by name."""
        profile_path = os.path.join(self.profiles_dir, f"{name}.yaml")
        if not os.path.exists(profile_path):
            return {}
            
        with open(profile_path, "r") as f:
            return yaml.safe_load(f)
