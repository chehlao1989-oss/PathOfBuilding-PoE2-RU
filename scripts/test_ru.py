"""Run offline RU regression tests using a synthetic build and temporary fixtures."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--directory", required=True, type=Path)
args = parser.parse_args()
directory = args.directory.resolve()
tests = ROOT / "tests/localization"
with tempfile.TemporaryDirectory(prefix="pob-ru-qa-") as tmp:
    scratch = Path(tmp)
    (scratch / "upstream-downloads").mkdir()
    shutil.copyfile(tests / "HeadlessWrapper.lua", scratch / "upstream-downloads/HeadlessWrapper.lua")
    shutil.copyfile(tests / "verify_pob.lua", scratch / "verify_pob.lua")
    shutil.copyfile(tests / "fixtures/reference-build.xml", scratch / "reference-build.xml")
    env = dict(os.environ, POB_FIXTURE_ROOT=str(scratch), POB_EXPECTED_LANGUAGE="ru")
    for name in (
        "check_trade_locale.lua",
        "check_trade_results_locale.lua",
        "check_character_import_locale.lua",
        "check_ui_layout.lua",
        "check_tree_search_editing.lua",
    ):
        print("Running " + name, flush=True)
        subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "scripts/run_pob_headless.py"), str(directory), str(tests / name)], env=env, check=True)
print("All offline RU checks passed")
