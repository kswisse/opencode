from pydantic import BaseModel, Field
from uuid import UUID


class BrandColors(BaseModel):
    primary: str = "#3b82f6"
    secondary: str = "#1e40af"


class SubtitleStyle(BaseModel):
    font: str = "Inter"
    color: str = "#ffffff"
    position: str = "bottom"
    background_opacity: float = 0.5


class AutoEditPreferences(BaseModel):
    zoom_style: str = "static"
    background_blur: bool = False
    silence_removal: bool = True


class CreatorProfile(BaseModel):
    id: UUID
    name: str = ""
    brand_colors: BrandColors = Field(default_factory=BrandColors)
    subtitle_style: SubtitleStyle = Field(default_factory=SubtitleStyle)
    preferred_duration: int = 60
    auto_edit_preferences: AutoEditPreferences = Field(default_factory=AutoEditPreferences)
