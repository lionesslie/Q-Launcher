import requests
import os
import json


class ModrinthBackend:
    """Modrinth API backend for mod searching and downloading."""
    
    def __init__(self, mods_directory):
        self.mods_directory = mods_directory
        if not os.path.exists(self.mods_directory):
            os.makedirs(self.mods_directory)
        self.base_url = "https://api.modrinth.com/v2"

    def search_mods(self, query, version=None, loader=None, limit=20, index="relevance", category=None):
        """Searches for mods on Modrinth with optional filters."""
        try:
            facets = [['project_type:mod']]
            if version:
                facets.append([f'versions:{version}'])
            if loader and loader.lower() != 'vanilla':
                facets.append([f'categories:{loader.lower()}'])
            if category and category != "All":
                 facets.append([f'categories:{category.lower()}'])

            params = {
                "query": query,
                "limit": limit,
                "index": index,
                "facets": json.dumps(facets)
            }
            
            response = requests.get(f"{self.base_url}/search", params=params)
            response.raise_for_status()
            data = response.json()
            return data.get('hits', [])
        except Exception as e:
            print(f"Error searching mods: {e}")
            return []

    def get_mod_versions(self, slug_or_id):
        """Gets versions for a mod."""
        try:
            response = requests.get(f"{self.base_url}/project/{slug_or_id}/version")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching mod versions: {e}")
            return []

    def download_mod(self, version_data, callback=None):
        """Downloads a specific mod version."""
        try:
            primary_file = next((f for f in version_data['files'] if f['primary']), version_data['files'][0])
            url = primary_file['url']
            filename = primary_file['filename']
            path = os.path.join(self.mods_directory, filename)
            
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if callback and total_size > 0:
                        callback(downloaded, total_size)
            
            return True, path
        except Exception as e:
            print(f"Error downloading mod: {e}")
            return False, str(e)


class CurseForgeBackend:
    """CurseForge API backend for mod searching and downloading."""

    # CurseForge API key for open-source launchers
    API_KEY = "$2a$10$bL4bIL5pUWqfcO7KQtnMReakwtfHbNKh6v1uTpKlg4tRMPAMpeJOy"
    GAME_ID_MINECRAFT = 432
    CLASS_ID_MODS = 6

    def __init__(self, mods_directory):
        self.mods_directory = mods_directory
        if not os.path.exists(self.mods_directory):
            os.makedirs(self.mods_directory)
        self.base_url = "https://api.curseforge.com/v1"
        self.headers = {
            "Accept": "application/json",
            "x-api-key": self.API_KEY
        }

    def search_mods(self, query, version=None, loader=None, limit=20, index="relevance", category=None):
        """Searches for mods on CurseForge."""
        try:
            # Map sort index
            sort_map = {
                "relevance": 1,    # Popularity
                "downloads": 6,    # TotalDownloads
                "newest": 11,      # DateCreated
                "updated": 3,      # LastUpdated
            }
            sort_field = sort_map.get(index, 1)

            # Map loader to modLoaderType
            loader_map = {
                "forge": 1,
                "fabric": 4,
                "quilt": 5,
                "neoforge": 6,
            }

            params = {
                "gameId": self.GAME_ID_MINECRAFT,
                "classId": self.CLASS_ID_MODS,
                "searchFilter": query,
                "pageSize": limit,
                "sortField": sort_field,
                "sortOrder": "desc",
            }
            if version:
                params["gameVersion"] = version
            if loader and loader.lower() in loader_map:
                params["modLoaderType"] = loader_map[loader.lower()]

            response = requests.get(
                f"{self.base_url}/mods/search",
                params=params,
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()

            # Normalize to Modrinth-like format for UI compatibility
            results = []
            for mod in data.get("data", []):
                logo = mod.get("logo")
                results.append({
                    "title": mod.get("name", ""),
                    "slug": str(mod.get("id", "")),
                    "project_id": str(mod.get("id", "")),
                    "description": mod.get("summary", ""),
                    "author": mod.get("authors", [{}])[0].get("name", "Unknown") if mod.get("authors") else "Unknown",
                    "downloads": mod.get("downloadCount", 0),
                    "icon_url": logo.get("url", "") if logo else "",
                    "_source": "curseforge",
                    "_cf_data": mod,
                })
            return results
        except Exception as e:
            print(f"[CurseForge] Error searching mods: {e}")
            return []

    def get_mod_versions(self, mod_id):
        """Gets versions (files) for a CurseForge mod."""
        try:
            response = requests.get(
                f"{self.base_url}/mods/{mod_id}/files",
                headers=self.headers,
                params={"pageSize": 50}
            )
            response.raise_for_status()
            data = response.json()

            # Normalize to Modrinth-like version format
            versions = []
            for f in data.get("data", []):
                versions.append({
                    "name": f.get("displayName", ""),
                    "version_number": f.get("fileName", ""),
                    "game_versions": f.get("gameVersions", []),
                    "loaders": self._extract_loaders(f),
                    "_source": "curseforge",
                    "_cf_file": f,
                    "files": [{
                        "url": f.get("downloadUrl", ""),
                        "filename": f.get("fileName", ""),
                        "primary": True,
                    }]
                })
            return versions
        except Exception as e:
            print(f"[CurseForge] Error fetching mod files: {e}")
            return []

    def _extract_loaders(self, file_data):
        """Extract loader names from CurseForge file data."""
        loaders = []
        for gv in file_data.get("gameVersions", []):
            gv_lower = gv.lower()
            if gv_lower in ("forge", "fabric", "quilt", "neoforge"):
                loaders.append(gv_lower)
        return loaders if loaders else ["unknown"]

    def download_mod(self, version_data, callback=None):
        """Downloads a CF mod file."""
        try:
            cf_file = version_data.get("_cf_file", {})
            url = cf_file.get("downloadUrl", "")
            filename = cf_file.get("fileName", "mod.jar")

            if not url:
                # Some CF mods don't provide direct download URL
                file_id = cf_file.get("id")
                mod_id = cf_file.get("modId")
                if file_id and mod_id:
                    url = f"https://edge.forgecdn.net/files/{str(file_id)[:4]}/{str(file_id)[4:]}/{filename}"

            path = os.path.join(self.mods_directory, filename)
            response = requests.get(url, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if callback and total_size > 0:
                        callback(downloaded, total_size)

            return True, path
        except Exception as e:
            print(f"[CurseForge] Error downloading mod: {e}")
            return False, str(e)
