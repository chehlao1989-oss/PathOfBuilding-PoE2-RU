from fetch_upstream import download, I18N
from concurrent.futures import ThreadPoolExecutor


files = ["fmt.dll", "abseil_dll.dll", "lua51.dll", "re2.dll", "libGLESv2.dll", "libEGL.dll", "libcurl.dll"]
downloads = [(f"reference/runtime/{name}", I18N + "runtime/" + name) for name in files]
downloads.append(("reference/pefile.py", "https://raw.githubusercontent.com/erocarrera/pefile/v2024.8.26/pefile.py"))

with ThreadPoolExecutor(max_workers=8) as pool:
    list(pool.map(download, downloads))
