from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import Request, urlopen


DESTINATION = Path(__file__).parent / "upstream-downloads"
I18N_REF = "8cb176392b923627c42879e6af17d27d4806a4a4"
POB_REF = "7d6f530cbdab20389ff8bc6ba97a37ac27f74e41"
RAW = "https://raw.githubusercontent.com/"
I18N = RAW + f"woolkingx/PathOfBuilding-PoE2-i18n/{I18N_REF}/"
POB = RAW + f"PathOfBuildingCommunity/PathOfBuilding-PoE2/{POB_REF}/"

FILES = {
    "reference/Lang.lua": I18N + "src/Modules/Lang.lua",
    "reference/Main.lua": I18N + "src/Modules/Main.lua",
    "reference/CompileLang.py": I18N + "scripts/compile-lang.py",
    "reference/ExtractUI.py": I18N + "scripts/extract-ui-msgids.py",
    "reference/pob.po": I18N + "locale/zh_TW/LC_MESSAGES/pob.po",
    "reference/r_font.cpp": I18N + "simplegraphic/engine/render/r_font.cpp",
    "reference/UnicodeFallback.tgf": I18N + "runtime/SimpleGraphic/Fonts/UnicodeFallback.tgf",
    "reference/original_font.cpp": POB + "simplegraphic/engine/render/r_font.cpp",
    "reference/original_utf8.cpp": POB + "simplegraphic/engine/script/lua_events.cpp",
    "reference/original_cmake.txt": POB + "simplegraphic/CMakeLists.txt",
    "reference/dat-view.lua": POB + "src/Export/DatView.lua",
    "reference/spec.lua": POB + "src/Export/spec.lua",
    "reference/poe2lab-tree.json": "https://api.github.com/repos/JavelinSx/poe2lab/git/trees/master?recursive=1",
}


def download(entry):
    relative_path, url = entry
    destination = DESTINATION / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        request = Request(url, headers={"User-Agent": "PoB-local-development"})
        with urlopen(request, timeout=25) as response:
            data = response.read()
        destination.write_bytes(data)
        print(f"{relative_path}: {len(data)} bytes")
    except OSError as error:
        print(f"{relative_path}: {error}")


if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(download, FILES.items()))
