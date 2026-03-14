<div align="center">

```
 ██╗    ██╗██████╗  ██████╗ ███████╗████████╗
 ██║    ██║██╔══██╗██╔════╝ ██╔════╝╚══██╔══╝
 ██║ █╗ ██║██████╔╝██║  ███╗█████╗     ██║   
 ██║███╗██║██╔═══╝ ██║   ██║██╔══╝     ██║   
 ╚███╔███╔╝██║     ╚██████╔╝███████╗   ██║   
  ╚══╝╚══╝ ╚═╝      ╚═════╝ ╚══════╝   ╚═╝   
```

**your new wallpaper engine downloader is here.**

![Python](https://img.shields.io/badge/python-3.10+-blue?style=flat-square&logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/platform-linux%20%7C%20windows-lightgrey?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)
![Status](https://img.shields.io/badge/status-active-brightgreen?style=flat-square)

</div>

---

Tired of bloated, janky scripts to download Wallpaper Engine wallpapers? **wpget** is different. No garbage code, no hacks. Just a clean, lightweight, and optimized desktop app that downloads Steam Workshop wallpapers straight to your machine.

> Built with [DepotDownloader](https://github.com/SteamRE/DepotDownloader) in a slick UI =)

---

## Features

- **Passwordless Steam login:** scan a QR code with the Steam mobile app, no credentials stored manually
- **Wallpaper preview:** see the title and type before downloading
- **One-click download:** paste the Workshop URL and hit download, that's it
- **Open folder shortcut:** jump straight to your downloaded files
- **Junk cleaner:** removes leftover depot files after download
- **Cross-platform:** native builds for **Linux** and **Windows**

---

## Output Format

**wpget** downloads the raw workshop content, what you get depends on the wallpaper type:

| Type | Output | Notes |
|------|--------|-------|
| `video` | `.mp4` file | Ready to use directly |
| `scene` | `.pkg` file | Package with textures/assets, used by Wallpaper Engine |
| `web` | web assets | HTML/JS bundle |

> **Note:** only `video` wallpapers produce a standalone `.mp4`. Scene wallpapers return a `.pkg` with raw engine assets, these require Wallpaper Engine to run or a package construct.

---

## Getting Started

### Pre-built binaries

Head to the [Releases](../../releases) page and grab the build for your OS:

- **Linux** → `wpget-linux` (Standalone binary built with PyInstaller)
- **Windows** → `wpget-windows.exe` (built via GitHub Actions)

No install needed, just run the binary.

---

### Run from source

**Requirements:**
- Python 3.10+
- pip

```bash
# Clone the repo
git clone https://github.com/efelleto/wpget.git
cd wpget

# Install dependencies
pip install -r requirements.txt

# Run
python main.py
```

---

## Authentication

wpget uses **Steam QR login**, no username or password is ever typed into the app.

1. Click **"connect with steam"**
2. A QR code popup will appear
3. Open the **Steam mobile app** → tap the QR icon → scan
4. Done, you're in!

The QR code refreshes automatically if it expires.

---

## How to Download a Wallpaper

1. Find a wallpaper on [Steam Workshop](https://steamcommunity.com/app/431960/workshop/)
2. Copy the URL (e.g. `https://steamcommunity.com/sharedfiles/filedetails/?id=XXXXXXXXX`)
3. Paste it into wpget
4. A preview card will appear with the wallpaper info
5. Click **↓ download**
6. Use **📂 open folder** to access the downloaded file
7. Optionally, click **🗑️ clear junk files** to remove leftover depot data


---

## Building

### Linux (PyInstaller)

```bash
pyinstaller --onefile --windowed main.py \
  --add-data "assets:assets" \
  --add-data "ui:ui" \
  --add-data "core:core" \
  --add-binary "bin/DepotDownloader:bin"
```

The output will be in `dist/`.

### Windows (GitHub Actions)

The Windows `.exe` is built automatically via GitHub Actions on every release push. See `.github/workflows/build-windows.yml` for the workflow configuration.

---

## Credits

- Download engine powered by [DepotDownloader](https://github.com/SteamRE/DepotDownloader) by SteamRE
- UI built with [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- Wallpaper metadata via Steam Community scraping

---

## License

MIT - do whatever you want with it.
