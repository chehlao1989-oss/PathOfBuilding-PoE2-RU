"""Add optional support links to the localization fork, without changing builds."""
from pathlib import Path


def patch_project_support(build: Path):
    path = build / "Modules/Main.lua"
    source = path.read_text(encoding="utf-8")
    replacements = [
        ('\tself.controls.applyUpdate = new("ButtonControl",', '''\tself.controls.supportProject = new("ButtonControl", {"BOTTOMLEFT",self.anchorMain,"BOTTOMLEFT"}, {0, -24, 160, 20}, "Support project", function()
\t\tself:OpenSupportPage()
\tend)
\tself.controls.supportProject.tooltipText = "Optional one-time support for the Russian localization on Boosty. PoB remains free."
\tself.controls.supportProject.shown = function()
\t\treturn not launch.devMode and (not launch.updateAvailable or launch.updateAvailable == "none")
\tend
\tself.controls.applyUpdate = new("ButtonControl",'''),
        ('{148, -26, 0, 16}, ""', '{168, -26, 0, 14}, ""'),
        ('function main:OpenAboutPopup(helpSectionIndex)', '''function main:OpenSupportPage()
\tOpenURL("https://boosty.to/dota2timer/donate")
end

function main:OpenAboutPopup(helpSectionIndex)'''),
        ('\tcontrols.verLabel = new("ButtonControl",', '''\tcontrols.supportProject = new("ButtonControl", nil, {0, 85, 190, 20}, "Support project", function()
\t\tself:OpenSupportPage()
\tend)
\tcontrols.supportNote = new("LabelControl", nil, {0, 110, 0, 14}, "Optional one-time support for the Russian localization on Boosty. PoB remains free.")
\tcontrols.verLabel = new("ButtonControl",'''),
        ('{10, 85, 100, 18}, "^7Version history:"', '{10, 133, 100, 18}, "^7Version history:"'),
        ('{-10, 85, 40, 18}, "^7Help:"', '{-10, 133, 40, 18}, "^7Help:"'),
        ('{0, 103, popupWidth - 20, 515}', '{0, 151, popupWidth - 20, 467}'),
    ]
    for old, new in replacements:
        if source.count(old) != 1:
            raise ValueError(f"Support UI patch expected one match: {old!r}")
        source = source.replace(old, new, 1)
    path.write_text(source, encoding="utf-8", newline="\n")
