"""
Downloader module for yt-dlp TUI.
Handles yt-dlp subprocess execution, progress parsing, and queue management.
"""

import asyncio
import json
import os
import re
import signal
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
import shutil

from config import get_app_root, Config, get_ffmpeg_location, get_aria2c_args


class DownloadStatus(Enum):
    """Status of a download item."""
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DownloadProgress:
    """Parsed progress information from yt-dlp output."""
    percentage: float = 0.0
    speed: str = ""
    eta: str = ""
    size_downloaded: str = ""
    total_size: str = ""
    filename: str = ""
    
    @classmethod
    def parse_line(cls, line: str) -> Optional['DownloadProgress']:
        """Parse a yt-dlp progress line (with --newline format)."""
        # Pattern: [download]   0.5% of    1.00MiB at    2.34KiB/s ETA 00:10
        # Or: [download] Destination: filename.mp4
        
        # Filename pattern
        filename_match = re.search(r'\[download\] Destination: (.+)', line)
        if filename_match:
            prog = cls()
            prog.filename = filename_match.group(1).strip()
            return prog
        
        # Progress pattern - multiple formats
        patterns = [
            # Standard format: XX.X% of XX.XX MiB at XX.XX KiB/s ETA XX:XX
            r'\[download\]\s+(\d+\.\d+)%\s+of\s+(\S+)\s+at\s+(\S+)\s+ETA\s+(\S+)',
            # Alternative: XX.X% of ~XX.XX MiB at XX.XX KiB/s ETA XX:XX
            r'\[download\]\s+(\d+\.\d+)%\s+of\s+~?(\S+)\s+at\s+(\S+)\s+ETA\s+(\S+)',
            # No ETA: XX.X% of XX.XX MiB at XX.XX KiB/s
            r'\[download\]\s+(\d+\.\d+)%\s+of\s+(\S+)\s+at\s+(\S+)',
            # Downloaded: XX.XX MiB / XX.XX MiB
            r'\[download\]\s+(\S+)\s+/\s+(\S+)',
        ]
        
        for i, pattern in enumerate(patterns):
            match = re.search(pattern, line)
            if match:
                prog = cls()
                if i < 3:  # Percentage patterns
                    prog.percentage = float(match.group(1))
                    prog.total_size = match.group(2)
                    if i < 2 and len(match.groups()) >= 4:
                        prog.speed = match.group(3)
                        prog.eta = match.group(4)
                    elif len(match.groups()) >= 3:
                        prog.speed = match.group(3)
                else:  # Downloaded/Total pattern
                    prog.size_downloaded = match.group(1)
                    prog.total_size = match.group(2)
                return prog
        
        return None


@dataclass
class DownloadItem:
    """Represents a single download in the queue."""
    id: int
    url: str
    status: DownloadStatus = DownloadStatus.QUEUED
    progress: DownloadProgress = field(default_factory=DownloadProgress)
    error_message: str = ""
    created_at: str = ""
    started_at: str = ""
    completed_at: str = ""
    output_path: str = ""
    command_args: List[str] = field(default_factory=list)
    process: Optional[asyncio.subprocess.Process] = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "url": self.url,
            "status": self.status.value,
            "progress": {
                "percentage": self.progress.percentage,
                "speed": self.progress.speed,
                "eta": self.progress.eta,
                "size_downloaded": self.progress.size_downloaded,
                "total_size": self.progress.total_size,
                "filename": self.progress.filename,
            },
            "error_message": self.error_message,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "output_path": self.output_path,
            "command_args": self.command_args,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DownloadItem':
        item = cls(
            id=data["id"],
            url=data["url"],
            status=DownloadStatus(data["status"]),
            error_message=data.get("error_message", ""),
            created_at=data.get("created_at", ""),
            started_at=data.get("started_at", ""),
            completed_at=data.get("completed_at", ""),
            output_path=data.get("output_path", ""),
            command_args=data.get("command_args", []),
        )
        progress_data = data.get("progress", {})
        item.progress = DownloadProgress(**progress_data) if progress_data else DownloadProgress()
        return item


class DownloadQueue:
    """Manages the download queue with concurrent execution."""
    
    def __init__(self, config: Config):
        self.config = config
        self.items: List[DownloadItem] = []
        self.next_id = 1
        self.active_count = 0
        self.max_concurrent = config.max_concurrent_downloads
        self._lock = asyncio.Lock()
        self._running = True
        
        # Load queue from file
        self.load_queue()
    
    def load_queue(self) -> None:
        """Load queue from JSON file."""
        queue_path = get_app_root() / self.config.queue_file
        
        if not queue_path.exists():
            return
        
        try:
            with open(queue_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            self.items = [DownloadItem.from_dict(item) for item in data.get("items", [])]
            self.next_id = data.get("next_id", 1)
            
            # Reset active downloads to queued (they can't survive restart)
            for item in self.items:
                if item.status == DownloadStatus.DOWNLOADING:
                    item.status = DownloadStatus.QUEUED
        except Exception as e:
            print(f"Warning: Could not load queue: {e}")
    
    def save_queue(self) -> None:
        """Save queue to JSON file."""
        queue_path = get_app_root() / self.config.queue_file
        queue_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "items": [item.to_dict() for item in self.items],
            "next_id": self.next_id,
        }
        
        with open(queue_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    
    def add_item(self, url: str, command_args: List[str]) -> DownloadItem:
        """Add a new download item to the queue."""
        item = DownloadItem(
            id=self.next_id,
            url=url,
            command_args=command_args,
        )
        self.next_id += 1
        self.items.append(item)
        self.save_queue()
        return item
    
    def get_active_count(self) -> int:
        """Count currently downloading items."""
        return sum(1 for item in self.items if item.status == DownloadStatus.DOWNLOADING)
    
    def get_queued_count(self) -> int:
        """Count queued items waiting to start."""
        return sum(1 for item in self.items if item.status == DownloadStatus.QUEUED)
    
    async def start_download(self, item: DownloadItem, 
                             progress_callback: Optional[Callable] = None) -> None:
        """Start a download for the given item."""
        if item.status != DownloadStatus.QUEUED:
            return
        
        item.status = DownloadStatus.DOWNLOADING
        item.started_at = datetime.now().isoformat()
        self.save_queue()
        
        try:
            # Build command
            cmd = ["yt-dlp"]
            cmd.extend(item.command_args)
            cmd.append(item.url)
            
            # Get binary paths
            is_windows = sys.platform == "win32"
            bin_dir = get_app_root() / self.config.bin_dir
            
            # Check for yt-dlp in bin directory
            yt_dlp_name = "yt-dlp.exe" if is_windows else "yt-dlp"
            yt_dlp_bin = bin_dir / yt_dlp_name
            
            if yt_dlp_bin.exists():
                cmd[0] = str(yt_dlp_bin.absolute())
            
            # Add ffmpeg location
            ffmpeg_loc = get_ffmpeg_location(self.config)
            if ffmpeg_loc:
                cmd.extend(["--ffmpeg-location", ffmpeg_loc])
            
            # Add aria2c args if enabled
            if self.config.aria2c.enabled:
                aria2c_args = get_aria2c_args(self.config)
                if aria2c_args:
                    # Only use aria2c for non-DASH/HLS
                    cmd.extend(["--downloader", "aria2c"])
                    cmd.extend(["--downloader-args", f"aria2c:{aria2c_args}"])
                    # Use native for DASH/HLS
                    cmd.extend(["--downloader", "dash,m3u8:native"])
            
            # Add archive file
            if self.config.download.use_download_archive:
                archive_path = get_app_root() / self.config.archive_file
                archive_path.parent.mkdir(parents=True, exist_ok=True)
                cmd.extend(["--download-archive", str(archive_path)])
            
            # Add newline for progress parsing
            cmd.append("--newline")
            
            # Start process
            item.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            
            # Read output
            while item.process.poll() is None:
                line = await item.process.stdout.readline()
                if not line:
                    break
                
                line_str = line.decode('utf-8', errors='replace').strip()
                
                # Parse progress
                progress = DownloadProgress.parse_line(line_str)
                if progress:
                    if progress.filename:
                        item.progress.filename = progress.filename
                    if progress.percentage > 0:
                        item.progress = progress
                    
                    if progress_callback:
                        await progress_callback(item, line_str)
            
            # Wait for process to complete
            returncode = await item.process.wait()
            item.process = None
            
            if returncode == 0:
                item.status = DownloadStatus.COMPLETED
                item.completed_at = datetime.now().isoformat()
            else:
                item.status = DownloadStatus.FAILED
                item.error_message = f"Exit code: {returncode}"
                item.completed_at = datetime.now().isoformat()
                
        except asyncio.CancelledError:
            item.status = DownloadStatus.CANCELLED
            item.completed_at = datetime.now().isoformat()
            raise
        except Exception as e:
            item.status = DownloadStatus.FAILED
            item.error_message = str(e)
            item.completed_at = datetime.now().isoformat()
        
        self.save_queue()
    
    async def pause_download(self, item: DownloadItem) -> bool:
        """Pause a running download."""
        if item.status != DownloadStatus.DOWNLOADING or not item.process:
            return False
        
        try:
            if sys.platform == "win32":
                # Windows doesn't support SIGSTOP, kill instead
                item.process.kill()
            else:
                os.kill(item.process.pid, signal.SIGSTOP)
            
            item.status = DownloadStatus.PAUSED
            self.save_queue()
            return True
        except Exception:
            return False
    
    async def resume_download(self, item: DownloadItem) -> bool:
        """Resume a paused download."""
        if item.status != DownloadStatus.PAUSED or not item.process:
            return False
        
        try:
            if sys.platform != "win32":
                os.kill(item.process.pid, signal.SIGCONT)
                item.status = DownloadStatus.DOWNLOADING
                self.save_queue()
                return True
        except Exception:
            pass
        
        # Can't truly resume on Windows or if process died, restart
        item.status = DownloadStatus.QUEUED
        self.save_queue()
        return True
    
    async def cancel_download(self, item: DownloadItem) -> bool:
        """Cancel a running download."""
        if item.status not in [DownloadStatus.DOWNLOADING, DownloadStatus.PAUSED]:
            return False
        
        if item.process:
            try:
                item.process.kill()
                await item.process.wait()
            except Exception:
                pass
        
        item.status = DownloadStatus.CANCELLED
        item.completed_at = datetime.now().isoformat()
        item.process = None
        self.save_queue()
        return True
    
    def remove_item(self, item_id: int) -> bool:
        """Remove an item from the queue."""
        for i, item in enumerate(self.items):
            if item.id == item_id:
                del self.items[i]
                self.save_queue()
                return True
        return False
    
    def retry_item(self, item_id: int) -> Optional[DownloadItem]:
        """Reset a failed/cancelled item for retry."""
        for item in self.items:
            if item.id == item_id:
                if item.status in [DownloadStatus.FAILED, DownloadStatus.CANCELLED]:
                    item.status = DownloadStatus.QUEUED
                    item.error_message = ""
                    item.started_at = ""
                    item.completed_at = ""
                    item.progress = DownloadProgress()
                    self.save_queue()
                    return item
        return None
    
    def clear_completed(self) -> int:
        """Remove all completed and cancelled items. Returns count removed."""
        initial_count = len(self.items)
        self.items = [
            item for item in self.items 
            if item.status not in [DownloadStatus.COMPLETED, DownloadStatus.CANCELLED]
        ]
        removed = initial_count - len(self.items)
        if removed > 0:
            self.save_queue()
        return removed


def build_format_string(preset: str, custom: str = "") -> str:
    """Build format string from preset selection."""
    presets = {
        "Best (auto)": "bestvideo+bestaudio/best",
        "4K": "bestvideo[height<=2160]+bestaudio/best",
        "1080p": "bestvideo[height<=1080]+bestaudio/best",
        "720p": "bestvideo[height<=720]+bestaudio/best",
        "480p": "bestvideo[height<=480]+bestaudio/best",
        "Audio only (best)": "bestaudio/best",
    }
    
    if preset.startswith("-t "):
        return preset  # Built-in preset like -t mp3
    
    if custom:
        return custom
    
    return presets.get(preset, "bestvideo+bestaudio/best")


def get_output_templates() -> List[str]:
    """Return list of common output templates."""
    return [
        "%(title)s [%(id)s].%(ext)s",
        "%(uploader)s/%(title)s.%(ext)s",
        "%(upload_date>%Y-%m-%d)s %(title)s.%(ext)s",
        "%(playlist_title)s/%(playlist_index)03d %(title)s.%(ext)s",
        "%(channel)s/%(upload_date>%Y)s/%(title)s.%(ext)s",
    ]
