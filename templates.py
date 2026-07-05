"""
Templates module for yt-dlp TUI.
Handles loading, saving, exporting, and importing template JSON files.
Includes built-in template registry.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict

from config import get_app_root, Config


@dataclass
class Template:
    """Represents a download template."""
    name: str
    description: str = ""
    format: str = ""  # raw --format value or preset alias (-t)
    output_template: str = "%(title)s [%(id)s].%(ext)s"
    flags: List[str] = None  # ordered list of extra flags
    aria2c_args: str = ""
    created: str = ""
    
    def __post_init__(self):
        if self.flags is None:
            self.flags = []
        if not self.created:
            self.created = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Template':
        return cls(**data)
    
    def build_command(self, url: str, config: Config) -> List[str]:
        """Build the full yt-dlp command from this template."""
        cmd = ["yt-dlp"]
        
        # Handle format - check if it's a -t preset or raw format
        if self.format.startswith("-t "):
            # It's a preset like "-t mp3"
            parts = self.format.split()
            cmd.extend(parts)
        elif self.format:
            cmd.extend(["-f", self.format])
        
        # Output template
        if self.output_template:
            cmd.extend(["-o", self.output_template])
        
        # Add all flags
        cmd.extend(self.flags)
        
        # Add aria2c args if present
        if self.aria2c_args:
            cmd.extend(["--downloader", "aria2c"])
            cmd.extend(["--downloader-args", f"aria2c:{self.aria2c_args}"])
        
        # Add URL
        cmd.append(url)
        
        return cmd


# Built-in templates registry
BUILTIN_TEMPLATES = [
    Template(
        name="Best quality",
        description="Download best video+audio, embed metadata and thumbnail",
        format="bestvideo+bestaudio/best",
        flags=["--embed-metadata", "--embed-thumbnail"],
    ),
    Template(
        name="MP3 192k",
        description="Extract audio as MP3 at 192kbps with metadata",
        format="-t mp3",
        flags=["--audio-quality", "192K", "--embed-metadata"],
    ),
    Template(
        name="MP3 320k",
        description="Extract audio as MP3 at 320kbps with metadata",
        format="-t mp3",
        flags=["--audio-quality", "320K", "--embed-metadata"],
    ),
    Template(
        name="AAC audio",
        description="Extract audio as AAC with metadata",
        format="-t aac",
        flags=["--embed-metadata"],
    ),
    Template(
        name="FLAC lossless",
        description="Extract audio as lossless FLAC",
        format="bestaudio",
        flags=["-x", "--audio-format", "flac"],
    ),
    Template(
        name="1080p MP4 + subs",
        description="Download 1080p MP4 with auto-subtitles embedded",
        format="-t mp4",
        flags=[
            "-f", "bestvideo[height<=1080]+bestaudio",
            "--write-auto-subs", "--embed-subs"
        ],
    ),
    Template(
        name="720p MP4",
        description="Download 720p MP4",
        format="-t mp4",
        flags=["-f", "bestvideo[height<=720]+bestaudio"],
    ),
    Template(
        name="Full playlist (numbered)",
        description="Download entire playlist with numbered filenames",
        format="bestvideo+bestaudio/best",
        output_template="%(playlist_title)s/%(playlist_index)03d %(title)s.%(ext)s",
        flags=["--yes-playlist"],
    ),
    Template(
        name="Playlist audio only",
        description="Download playlist as MP3 files",
        format="-t mp3",
        output_template="%(playlist_title)s/%(playlist_index)03d %(title)s.%(ext)s",
        flags=["--yes-playlist"],
    ),
    Template(
        name="SponsorBlock clean 1080p",
        description="Download 1080p with SponsorBlock segments removed",
        format="bestvideo[height<=1080]+bestaudio",
        flags=["--sponsorblock-remove", "all,-filler"],
    ),
    Template(
        name="Subtitled + chapters",
        description="Best quality with subtitles and chapter markers",
        format="bestvideo+bestaudio/best",
        flags=[
            "--write-auto-subs", "--embed-subs",
            "--embed-chapters", "--embed-metadata"
        ],
    ),
    Template(
        name="Archive mode (no re-dl)",
        description="Use download archive to avoid re-downloading",
        format="bestvideo+bestaudio/best",
        flags=["--download-archive", "./data/archive.txt"],
    ),
    Template(
        name="Slow/polite mode",
        description="Add delays between requests to be polite to servers",
        format="-t sleep",
        flags=[],
    ),
    Template(
        name="Cookies from Chrome",
        description="Use Chrome cookies for authentication",
        format="bestvideo+bestaudio/best",
        flags=["--cookies-from-browser", "chrome"],
    ),
    Template(
        name="aria2c turbo",
        description="Use aria2c with max connections for faster downloads",
        format="bestvideo+bestaudio/best",
        aria2c_args="-x 16 -s 16 -k 1M",
    ),
]


def get_templates_dir(config: Config) -> Path:
    """Get the templates directory path."""
    return get_app_root() / config.templates_dir


def load_template(name: str, config: Config) -> Optional[Template]:
    """Load a template from ./templates/NAME.json."""
    templates_dir = get_templates_dir(config)
    template_path = templates_dir / f"{name}.json"
    
    if not template_path.exists():
        return None
    
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Template.from_dict(data)
    except Exception as e:
        print(f"Error loading template {name}: {e}")
        return None


def save_template(template: Template, config: Config) -> str:
    """Save a template to ./templates/NAME.json. Returns the filename."""
    templates_dir = get_templates_dir(config)
    templates_dir.mkdir(parents=True, exist_ok=True)
    
    # Sanitize filename
    filename = "".join(c for c in template.name if c.isalnum() or c in " _-").strip()
    filename = filename.replace(" ", "_").lower()
    
    template_path = templates_dir / f"{filename}.json"
    
    with open(template_path, "w", encoding="utf-8") as f:
        json.dump(template.to_dict(), f, indent=2)
    
    return filename


def delete_template(name: str, config: Config) -> bool:
    """Delete a template file."""
    templates_dir = get_templates_dir(config)
    template_path = templates_dir / f"{name}.json"
    
    if template_path.exists():
        template_path.unlink()
        return True
    return False


def list_templates(config: Config) -> List[Template]:
    """List all user-created templates."""
    templates_dir = get_templates_dir(config)
    templates = []
    
    if not templates_dir.exists():
        return templates
    
    for file in templates_dir.glob("*.json"):
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
            templates.append(Template.from_dict(data))
        except Exception:
            continue
    
    return templates


def export_template_to_command(template: Template, url: str, config: Config) -> str:
    """Export a template as a shell command string."""
    cmd = template.build_command(url, config)
    return " ".join(cmd)


def import_template_from_json(json_str: str) -> Optional[Template]:
    """Import a template from JSON string."""
    try:
        data = json.loads(json_str)
        return Template.from_dict(data)
    except Exception:
        return None


def get_builtin_template(index: int) -> Optional[Template]:
    """Get a built-in template by index."""
    if 0 <= index < len(BUILTIN_TEMPLATES):
        return BUILTIN_TEMPLATES[index]
    return None


def get_all_templates(config: Config) -> List[tuple[str, Template]]:
    """Get all templates (built-in + user) with source label."""
    result = []
    
    # Built-in templates
    for t in BUILTIN_TEMPLATES:
        result.append(("Built-in", t))
    
    # User templates
    for t in list_templates(config):
        result.append(("User", t))
    
    return result
