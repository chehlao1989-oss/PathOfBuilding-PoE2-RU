-- Path of Building
--
-- Class: Label Control
-- Simple text label.
--
local LabelClass = newClass("LabelControl", "Control", function(self, anchor, rect, label)
	self.Control(anchor, rect)
	self.label = label
	self.width = function()
		return DrawStringWidth(self:GetProperty("height"), "VAR", self:GetProperty("label"))
	end
end)

function LabelClass:SetWrapWidth(width)
	self.wrapWidth = width
	self.lineHeight = self:GetProperty("height")
	self.width = width
	self.height = function(control)
		local _, lines = control:GetWrappedLabel()
		return control.lineHeight * lines
	end
end

function LabelClass:GetWrappedLabel()
	return UILocale.wrap(self, self:GetProperty("label"), self.lineHeight, "VAR", self:GetProperty("wrapWidth"))
end

function LabelClass:Draw()
	local x, y = self:GetPos()
	if self.wrapWidth then
		local text = self:GetWrappedLabel()
		if self.wrapAlign == "RIGHT_X" then
			for line in (text .. "\n"):gmatch("(.-)\n") do
				UILocale.drawRaw(x + self:GetProperty("width"), y, "RIGHT_X", self.lineHeight, "VAR", line)
				y = y + self.lineHeight
			end
		else
			UILocale.drawRaw(x, y, "LEFT", self.lineHeight, "VAR", text)
		end
	else
		DrawString(x, y, "LEFT", self:GetProperty("height"), "VAR", self:GetProperty("label"))
	end
end