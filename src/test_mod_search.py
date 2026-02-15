from src.mod_manager import ModrinthBackend
import json

def test_search():
    backend = ModrinthBackend("test_mods")
    print("Testing search with empty query and index='downloads'...")
    
    # Simulate the call made by the UI
    results = backend.search_mods("", limit=10, index="downloads")
    
    print(f"Results found: {len(results)}")
    for mod in results:
        print(f"- {mod['title']} ({mod['slug']}) - Downloads: {mod.get('downloads')}")

if __name__ == "__main__":
    test_search()
