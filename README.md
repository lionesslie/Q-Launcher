# QLauncher

QLauncher is a modern, lightweight, and custom Minecraft Launcher built with Python and PyQt5. It features a sleek dark UI, integrated mod management via Modrinth, and support for Vanilla, Fabric, and Forge modloaders.

![QLauncher Screenshot](assets/app_icon.ico)

## Features

- **Authentication**: Offline mode (username based) support.
- **Version Management**: Automatically fetches and installs Vanilla Minecraft versions.
- **Modloader Support**: 
  - **Fabric**: Automatic installation and launching.
  - **Forge**: Automatic installation and launching.
- **Mod Management**: 
  - Integrated **Modrinth** search and download.
  - auto-loads popular mods.
  - Filter by game version and loader.
  - Sort by Downloads, Relevance, Newest, etc.
- **Smart Downloads**: Checks for existing versions and modloaders to prevent redundant downloads.
- **Settings**: 
  - Configurable RAM allocation (JVM Arguments).
  - Quick access to the game folder.
- **UI**: 
  - Modern, semi-transparent design.
  - Custom background support (auto-downloads high-quality backgrounds).
  - Custom Minecraft-style application icon.

## Installation

### Running from Source

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/Q-Launcher.git
    cd Q-Launcher
    ```

2.  **Create a Virtual Environment** (Recommended):
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # Linux/Mac
    source venv/bin/activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install PyQt5 minecraft-launcher-lib requests Pillow
    ```

4.  **Run the Launcher**:
    ```bash
    python main.py
    ```

## Dependencies

- [PyQt5](https://pypi.org/project/PyQt5/) - GUI Framework
- [minecraft-launcher-lib](https://pypi.org/project/minecraft-launcher-lib/) - Core Minecraft launching logic
- [requests](https://pypi.org/project/requests/) - HTTP requests (API, downloads)
- [Pillow](https://pypi.org/project/Pillow/) - Image processing (Icon generation)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open-source.

