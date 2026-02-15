import minecraft_launcher_lib
import subprocess
import sys
import os
import requests
import uuid
import json

class LauncherBackend:
    def __init__(self, minecraft_directory):
        self.minecraft_directory = minecraft_directory
        if not os.path.exists(self.minecraft_directory):
            os.makedirs(self.minecraft_directory)

    def get_vanilla_versions(self):
        """Returns a list of installable vanilla versions."""
        try:
            versions = minecraft_launcher_lib.utils.get_version_list()
            return [v['id'] for v in versions if v['type'] == 'release']
        except Exception as e:
            print(f"Error fetching vanilla versions: {e}")
            return []

    def get_installed_versions(self):
        """Returns a list of installed versions."""
        return [v['id'] for v in minecraft_launcher_lib.utils.get_installed_versions(self.minecraft_directory)]

    def install_version(self, version_id, callback=None):
        """Installs the specified Minecraft version."""
        callback_dict = {}
        if callback:
            callback_dict = {
                "setStatus": lambda text: callback(text, 0),
                "setProgress": lambda value: callback(f"Downloading...", value),
                "setMax": lambda value: None # We handle progress as 0-100 usually, but lib uses raw counts
            }
            
        minecraft_launcher_lib.install.install_minecraft_version(
            version=version_id,
            minecraft_directory=self.minecraft_directory,
            callback=callback_dict
        )

    def install_fabric(self, version_id):
        """Installs Fabric for the specific vanilla version."""
        try:
            minecraft_launcher_lib.fabric.install_fabric(
                version_id,
                self.minecraft_directory
            )
            return True
        except Exception as e:
            print(f"Error installing fabric: {e}")
            return False

    def install_forge(self, version_id):
        """Installs Forge for the specific vanilla version."""
        try:
            # Automatic Forge installation is complex and often requires running the installer JAR.
            # minecraft-launcher-lib has support but it can be flaky depending on Forge version.
            # For now we use the simple library call.
            minecraft_launcher_lib.forge.install_forge_version(
                version_id,
                self.minecraft_directory
            )
            return True
        except Exception as e:
             print(f"Error installing forge: {e}")
             return False

    def install_quilt(self, version_id):
        """Installs Quilt for the specific vanilla version."""
        try:
            minecraft_launcher_lib.quilt.install_quilt(
                version_id,
                self.minecraft_directory
            )
            return True
        except Exception as e:
            print(f"Error installing quilt: {e}")
            return False

    def launch_game(self, version_id, modloader, username, progress_callback=None, game_dir=None):
        """Launches the game with the specified version and modloader."""
        print(f"[Backend] Launching {version_id} ({modloader}) for {username}")
        
        # 1. Install Vanilla Version if needed
        if version_id not in self.get_installed_versions():
             print(f"[Backend] Version {version_id} not found. Installing...")
             if progress_callback:
                 progress_callback(f"Installing Vanilla {version_id}...", 0)
             self.install_version(version_id, lambda t, m: progress_callback(t, m) if progress_callback else None)
        else:
             print(f"[Backend] Version {version_id} found.")

        launch_version_id = version_id

        # 2. Install/Resolve Modloader
        if modloader == 'Fabric':
            print("[Backend] Checking Fabric...")
            installed = self.get_installed_versions()
            existing_fabric = next((v for v in installed if "fabric" in v and version_id in v), None)
            
            if existing_fabric:
                 print(f"[Backend] Fabric version already installed: {existing_fabric}")
                 launch_version_id = existing_fabric
            else:
                print("[Backend] Installing Fabric loader...")
                if progress_callback:
                    progress_callback(f"Installing Fabric for {version_id}...", 0)
                try:
                    minecraft_launcher_lib.fabric.install_fabric(version_id, self.minecraft_directory)
                    installed = self.get_installed_versions()
                    fab_id = next((v for v in installed if "fabric" in v and version_id in v), None)
                    if fab_id:
                        launch_version_id = fab_id
                        print(f"[Backend] Fabric version resolved: {launch_version_id}")
                    else:
                        print("[Backend] Could not find installed Fabric version ID.")
                except Exception as e:
                    print(f"Error installing Fabric: {e}")
                    if progress_callback: progress_callback(f"Error installing Fabric: {e}", 0)
                    return

        elif modloader == 'Quilt':
            print("[Backend] Checking Quilt...")
            installed = self.get_installed_versions()
            existing_quilt = next((v for v in installed if "quilt" in v and version_id in v), None)
            
            if existing_quilt:
                print(f"[Backend] Quilt version already installed: {existing_quilt}")
                launch_version_id = existing_quilt
            else:
                print("[Backend] Installing Quilt loader...")
                if progress_callback:
                    progress_callback(f"Installing Quilt for {version_id}...", 0)
                try:
                    minecraft_launcher_lib.quilt.install_quilt(version_id, self.minecraft_directory)
                    installed = self.get_installed_versions()
                    quilt_id = next((v for v in installed if "quilt" in v and version_id in v), None)
                    if quilt_id:
                        launch_version_id = quilt_id
                        print(f"[Backend] Quilt version resolved: {launch_version_id}")
                    else:
                        print("[Backend] Could not find installed Quilt version ID.")
                except Exception as e:
                    print(f"Error installing Quilt: {e}")
                    if progress_callback: progress_callback(f"Error installing Quilt: {e}", 0)
                    return

        elif modloader == 'Forge':
            print("[Backend] Checking Forge...")
            installed = self.get_installed_versions()
            existing_forge = next((v for v in installed if "forge" in v and version_id in v), None)
            
            if existing_forge:
                print(f"[Backend] Forge version already installed: {existing_forge}")
                launch_version_id = existing_forge
            else:
                print("[Backend] Installing Forge...")
                if progress_callback:
                    progress_callback(f"Installing Forge for {version_id}...", 0)
                try:
                     print("[Backend] Running Forge Installer...")
                     minecraft_launcher_lib.forge.install_forge_version(version_id, self.minecraft_directory)
                     
                     installed = self.get_installed_versions()
                     forge_id = next((v for v in installed if "forge" in v and version_id in v), None)
                     if forge_id:
                         launch_version_id = forge_id
                         print(f"[Backend] Forge version resolved: {launch_version_id}")
                     else:
                         print("[Backend] Could not find installed Forge version ID.")
                except Exception as e:
                    print(f"Error installing Forge: {e}")
                    if progress_callback: progress_callback(f"Error installing Forge: {e}", 0)
                    return

        # Settings
        max_memory = 2048
        java_path = None
        width = 854
        height = 480
        fullscreen = False

        try:
            if os.path.exists("settings.json"):
                with open("settings.json", "r") as f:
                    settings = json.load(f)
                    max_memory = settings.get("max_memory", 2048)
                    java_path = settings.get("java_path", "")
                    width = settings.get("width", 854)
                    height = settings.get("height", 480)
                    fullscreen = settings.get("fullscreen", False)
        except:
            pass

        # Options for launching
        options = {
            "username": username,
            "uuid": str(uuid.uuid4()),
            "token": "",
            "launcherName": "QLauncher",
            "launcherVersion": "1.0",
            "jvmArguments": [f"-Xmx{max_memory}M"],
            "customResolution": True,
            "resolutionWidth": str(width),
            "resolutionHeight": str(height),
        }
        
        if java_path and os.path.exists(java_path):
             options["executablePath"] = java_path

        # Use profile-specific game directory if provided
        if game_dir:
            os.makedirs(game_dir, exist_ok=True)
            options["gameDirectory"] = game_dir

        print(f"[Backend] Generating launch command for {launch_version_id} with {max_memory}MB RAM...")
        if game_dir:
            print(f"[Backend] Game directory: {game_dir}")

        # Get launch command
        try:
            minecraft_command = minecraft_launcher_lib.command.get_minecraft_command(
                version=launch_version_id,
                minecraft_directory=self.minecraft_directory,
                options=options
            )
            
            if fullscreen:
                minecraft_command.append("--fullscreen")

            print(f"[Backend] Command generated successfully.")
        except Exception as e:
            print(f"[Backend] Failed to generate launch command: {e}")
            raise e

        # Return launch command for the UI to manage the process
        return minecraft_command
