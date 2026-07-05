"""
Configuration module for yt-dlp TUI.
Handles reading/writing config.toml with defaults and validation.
"""

import os
import sys
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import tomli_w


@dataclass
class OutputSettings:
    default_save_path: str = "./downloads"
    default_filename_template: str = "%(title)s [%(id)s].%(ext)s"
    restrict_filenames: bool = False
    trim_filenames: int = 0  # 0 = no trim
    write_info_json: bool = False
    write_description: bool = False
    use_mtime: bool = True  # --mtime


@dataclass
class DownloadSettings:
    concurrent_fragments: int = 1
    rate_limit: str = ""  # e.g., "4M", "500K"
    retry_count: int = 10
    continue_partial: bool = True
    use_download_archive: bool = True
    playlist_items: str = ""
    min_filesize: str = ""
    max_filesize: str = ""
    date_filter: str = ""
    datebefore: str = ""
    dateafter: str = ""
    max_downloads: int = 0  # 0 = unlimited
    sleep_interval: float = 0.0
    max_sleep_interval: float = 0.0


@dataclass
class Aria2cSettings:
    enabled: bool = True
    connections_per_server: int = 16  # -x
    split_count: int = 16  # -s
    min_split_size: str = "1M"  # -k
    max_concurrent: int = 5  # -j for aria2c


@dataclass
class FfmpegSettings:
    remux_video: str = ""  # mp4/mkv/webm/mov/avi/flv
    recode_video: str = ""
    audio_format: str = ""  # mp3/aac/flac/m4a/opus/vorbis/wav/alac
    audio_quality: str = ""  # 0-10 or bitrate like 192K
    keep_video: bool = False
    split_chapters: bool = False
    force_keyframes: bool = False
    postprocessor_args: str = ""


@dataclass
class SubtitleSettings:
    write_subs: bool = False
    write_auto_subs: bool = False
    sub_langs: str = "en"
    sub_format: str = "best"
    embed_subs: bool = False
    convert_subs: str = ""


@dataclass
class MetadataSettings:
    embed_thumbnail: bool = True
    embed_metadata: bool = True
    embed_chapters: bool = False
    write_thumbnail: bool = False
    convert_thumbnails: str = ""
    parse_metadata: str = ""


@dataclass
class SponsorBlockSettings:
    mark_categories: str = ""
    remove_categories: str = ""
    api_url: str = ""


@dataclass
class NetworkSettings:
    proxy: str = ""
    impersonate: str = ""
    cookies_file: str = ""
    cookies_from_browser: str = ""
    socket_timeout: int = 0
    add_headers: str = ""
    force_ipv4: bool = False
    force_ipv6: bool = False
    sleep_requests: float = 0.0


@dataclass
class AdvancedSettings:
    update_channel: str = ""  # stable/nightly/master
    geo_bypass: str = ""  # --xff value
    ignore_errors: bool = False
    verbose: bool = False


@dataclass
class Config:
    output: OutputSettings = field(default_factory=OutputSettings)
    download: DownloadSettings = field(default_factory=DownloadSettings)
    aria2c: Aria2cSettings = field(default_factory=Aria2cSettings)
    ffmpeg: FfmpegSettings = field(default_factory=FfmpegSettings)
    subtitles: SubtitleSettings = field(default_factory=SubtitleSettings)
    metadata: MetadataSettings = field(default_factory=MetadataSettings)
    sponsorblock: SponsorBlockSettings = field(default_factory=SponsorBlockSettings)
    network: NetworkSettings = field(default_factory=NetworkSettings)
    advanced: AdvancedSettings = field(default_factory=AdvancedSettings)
    
    # App settings
    max_concurrent_downloads: int = 3
    queue_file: str = "./data/queue.json"
    archive_file: str = "./data/archive.txt"
    templates_dir: str = "./templates"
    bin_dir: str = "./bin"


def get_app_root() -> Path:
    """Get the application root directory."""
    # If running as a script, use the script's directory
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    # Use the directory containing config.py as app root
    return Path(__file__).resolve().parent


def get_config_path() -> Path:
    """Get the path to config.toml."""
    return get_app_root() / "config" / "config.toml"


def load_config() -> Config:
    """Load configuration from config.toml or return defaults."""
    config_path = get_config_path()
    
    if not config_path.exists():
        # Create default config
        config = Config()
        save_config(config)
        return config
    
    try:
        with open(config_path, "rb") as f:
            data = tomllib.load(f)
        
        # Build config from loaded data
        config = Config()
        
        if "output" in data:
            config.output = OutputSettings(**data["output"])
        if "download" in data:
            config.download = DownloadSettings(**data["download"])
        if "aria2c" in data:
            config.aria2c = Aria2cSettings(**data["aria2c"])
        if "ffmpeg" in data:
            config.ffmpeg = FfmpegSettings(**data["ffmpeg"])
        if "subtitles" in data:
            config.subtitles = SubtitleSettings(**data["subtitles"])
        if "metadata" in data:
            config.metadata = MetadataSettings(**data["metadata"])
        if "sponsorblock" in data:
            config.sponsorblock = SponsorBlockSettings(**data["sponsorblock"])
        if "network" in data:
            config.network = NetworkSettings(**data["network"])
        if "advanced" in data:
            config.advanced = AdvancedSettings(**data["advanced"])
        
        # App settings
        if "max_concurrent_downloads" in data:
            config.max_concurrent_downloads = data["max_concurrent_downloads"]
        if "queue_file" in data:
            config.queue_file = data["queue_file"]
        if "archive_file" in data:
            config.archive_file = data["archive_file"]
        if "templates_dir" in data:
            config.templates_dir = data["templates_dir"]
        if "bin_dir" in data:
            config.bin_dir = data["bin_dir"]
        
        return config
    except Exception as e:
        print(f"Warning: Could not load config.toml: {e}")
        return Config()


def save_config(config: Config) -> None:
    """Save configuration to config.toml."""
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    data = {
        "output": asdict(config.output),
        "download": asdict(config.download),
        "aria2c": asdict(config.aria2c),
        "ffmpeg": asdict(config.ffmpeg),
        "subtitles": asdict(config.subtitles),
        "metadata": asdict(config.metadata),
        "sponsorblock": asdict(config.sponsorblock),
        "network": asdict(config.network),
        "advanced": asdict(config.advanced),
        "max_concurrent_downloads": config.max_concurrent_downloads,
        "queue_file": config.queue_file,
        "archive_file": config.archive_file,
        "templates_dir": config.templates_dir,
        "bin_dir": config.bin_dir,
    }
    
    with open(config_path, "wb") as f:
        tomli_w.dump(data, f)


def resolve_binary_path(bin_name: str, config: Config) -> Optional[str]:
    """
    Resolve binary path, checking ./bin/ first, then PATH.
    Returns the full path if found, None otherwise.
    """
    import shutil
    
    # Determine OS-specific suffix
    is_windows = sys.platform == "win32"
    suffix = ".exe" if is_windows else ""
    
    bin_dir = get_app_root() / config.bin_dir
    
    # Check ./bin/ first
    bin_path = bin_dir / f"{bin_name}{suffix}"
    if bin_path.exists() and os.access(bin_path, os.X_OK):
        return str(bin_path.absolute())
    
    # Fall back to PATH
    found = shutil.which(bin_name)
    if found:
        return found
    
    return None


def get_ffmpeg_location(config: Config) -> Optional[str]:
    """Get ffmpeg location for yt-dlp (--ffmpeg-location accepts directory)."""
    bin_dir = get_app_root() / config.bin_dir
    if bin_dir.exists():
        return str(bin_dir.absolute())
    
    # Try to find ffmpeg in PATH
    ffmpeg_path = resolve_binary_path("ffmpeg", config)
    if ffmpeg_path:
        return str(Path(ffmpeg_path).parent)
    
    return None


def get_aria2c_args(config: Config) -> str:
    """Build aria2c arguments string for --downloader-args."""
    aria = config.aria2c
    args = []
    
    if aria.enabled:
        args.append(f"-x {aria.connections_per_server}")
        args.append(f"-s {aria.split_count}")
        args.append(f"-k {aria.min_split_size}")
        args.append(f"-j {aria.max_concurrent}")
        if config.download.continue_partial:
            args.append("--continue")
    
    return " ".join(args)
