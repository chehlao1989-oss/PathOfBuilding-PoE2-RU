def patch_build_warnings(edit, build):
    edit("Modules/Build.lua", [
        (
            "local pairs = pairs",
            'local localizeBuildWarning = LoadModule("Modules/BuildWarningLocale")\nlocal pairs = pairs',
        ),
        (
            '\t\t\t\tfor k,v in pairs(self.controls.warnings.lines) do miscTooltip:AddLine(16, v) end',
            '\t\t\t\tmiscTooltip.maxWidth = 600\n'
            '\t\t\t\tfor _, warning in ipairs(self.controls.warnings.lines) do\n'
            '\t\t\t\t\tmiscTooltip:AddLine(16, localizeBuildWarning(warning, self))\n'
            '\t\t\t\tend',
        ),
    ], source=build)
