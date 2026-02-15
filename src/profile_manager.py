import json
import os
import uuid
import shutil
from datetime import datetime


class ProfileManager:
    """Manages Minecraft profiles — each profile is a full game instance
    located at .minecraft/versions/<ProfileName>/."""

    # Standard Minecraft directories to create for each profile
    INSTANCE_DIRS = ["mods", "config", "saves", "resourcepacks", "shaderpacks", "logs"]

    def __init__(self, app_dir):
        self.app_dir = app_dir
        self.minecraft_dir = os.path.join(os.getenv('APPDATA'), '.minecraft')
        self.profiles_file = os.path.join(app_dir, "profiles.json")
        self.profiles = []
        self.active_profile_id = None
        self._load()

    def _load(self):
        """Load profiles from disk."""
        try:
            if os.path.exists(self.profiles_file):
                with open(self.profiles_file, "r") as f:
                    data = json.load(f)
                self.profiles = data.get("profiles", [])
                self.active_profile_id = data.get("active_profile_id")
        except Exception as e:
            print(f"[ProfileManager] Error loading profiles: {e}")
            self.profiles = []

        # Create default profile if none exist
        if not self.profiles:
            self.create_profile("Default", "1.21.4", "Vanilla", "#4ade80")

    def _save(self):
        """Save profiles to disk."""
        try:
            data = {
                "active_profile_id": self.active_profile_id,
                "profiles": self.profiles
            }
            with open(self.profiles_file, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"[ProfileManager] Error saving profiles: {e}")

    def _safe_name(self, name):
        """Sanitize profile name for use as directory name."""
        # Replace characters that are invalid in file/folder names
        invalid = '<>:"/\\|?*'
        safe = name.strip()
        for c in invalid:
            safe = safe.replace(c, '_')
        return safe if safe else "Profile"

    def get_profiles(self):
        """Return all profiles."""
        return self.profiles

    def get_active_profile(self):
        """Return the active profile, or the first one."""
        if self.active_profile_id:
            for p in self.profiles:
                if p["id"] == self.active_profile_id:
                    return p
        if self.profiles:
            return self.profiles[0]
        return None

    def set_active_profile(self, profile_id):
        """Set the active profile by ID."""
        self.active_profile_id = profile_id
        self._save()

    def create_profile(self, name, version="1.21.4", loader="Vanilla", color="#4ade80"):
        """Create a new profile with its own game directory."""
        profile = {
            "id": str(uuid.uuid4())[:8],
            "name": name,
            "version": version,
            "loader": loader,
            "color": color,
            "created_at": datetime.now().isoformat()
        }
        self.profiles.append(profile)

        # Create instance directory with full Minecraft folder structure
        inst_dir = self.get_instance_dir(profile["id"])
        os.makedirs(inst_dir, exist_ok=True)
        for subdir in self.INSTANCE_DIRS:
            os.makedirs(os.path.join(inst_dir, subdir), exist_ok=True)

        if self.active_profile_id is None:
            self.active_profile_id = profile["id"]

        self._save()
        return profile

    def update_profile(self, profile_id, **kwargs):
        """Update fields of a profile. If name changes, rename the directory."""
        for p in self.profiles:
            if p["id"] == profile_id:
                old_name = p.get("name")
                for key, value in kwargs.items():
                    if key in ("name", "version", "loader", "color"):
                        p[key] = value

                # Rename directory if name changed
                new_name = p.get("name")
                if old_name and new_name and old_name != new_name:
                    old_dir = os.path.join(self.minecraft_dir, "versions", self._safe_name(old_name))
                    new_dir = os.path.join(self.minecraft_dir, "versions", self._safe_name(new_name))
                    if os.path.exists(old_dir) and not os.path.exists(new_dir):
                        try:
                            os.rename(old_dir, new_dir)
                        except Exception as e:
                            print(f"[ProfileManager] Could not rename directory: {e}")

                self._save()
                return p
        return None

    def delete_profile(self, profile_id):
        """Delete a profile. Cannot delete the last profile."""
        if len(self.profiles) <= 1:
            return False

        # Find the profile to get its directory
        target = None
        for p in self.profiles:
            if p["id"] == profile_id:
                target = p
                break

        self.profiles = [p for p in self.profiles if p["id"] != profile_id]
        if self.active_profile_id == profile_id:
            self.active_profile_id = self.profiles[0]["id"] if self.profiles else None

        # Optionally remove the instance directory (we keep it for safety)
        # User can manually delete from .minecraft/versions/<name>/

        self._save()
        return True

    def duplicate_profile(self, profile_id):
        """Duplicate an existing profile including its directory."""
        source = None
        for p in self.profiles:
            if p["id"] == profile_id:
                source = p
                break
        if not source:
            return None

        new_profile = self.create_profile(
            name=f"{source['name']} (Copy)",
            version=source["version"],
            loader=source["loader"],
            color=source["color"]
        )

        # Copy files from source to new profile directory
        src_dir = self.get_instance_dir(profile_id)
        dst_dir = self.get_instance_dir(new_profile["id"])
        if os.path.exists(src_dir):
            for subdir in self.INSTANCE_DIRS:
                src_sub = os.path.join(src_dir, subdir)
                dst_sub = os.path.join(dst_dir, subdir)
                if os.path.exists(src_sub):
                    try:
                        shutil.copytree(src_sub, dst_sub, dirs_exist_ok=True)
                    except Exception as e:
                        print(f"[ProfileManager] Error copying {subdir}: {e}")

        return new_profile

    def get_instance_dir(self, profile_id):
        """Get the game directory for a specific profile.
        Located at .minecraft/versions/<ProfileName>/"""
        profile = None
        for p in self.profiles:
            if p["id"] == profile_id:
                profile = p
                break
        if profile:
            return os.path.join(self.minecraft_dir, "versions", self._safe_name(profile["name"]))
        # Fallback
        return os.path.join(self.minecraft_dir, "versions", profile_id)

    def get_mods_dir(self, profile_id):
        """Get the mods directory for a specific profile."""
        return os.path.join(self.get_instance_dir(profile_id), "mods")

    def get_game_dir(self, profile_id):
        """Get the full game directory used for launching.
        This is the same as instance_dir — the game uses this as --gameDir."""
        return self.get_instance_dir(profile_id)
