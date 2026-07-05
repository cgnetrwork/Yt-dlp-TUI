#!/usr/bin/env python3
"""
yt-dlp TUI - Terminal User Interface for yt-dlp
A polished keyboard-navigable interface for downloading videos.
"""

import asyncio
import os
import sys
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, List

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Header, Footer, TabbedContent, TabPane, Button, Input, 
    Label, Static, ProgressBar, ListView, ListItem, Switch, 
    Select, DataTable, DirectoryTree, RichLog, Checkbox
)
from textual.message import Message
from textual.worker import Worker, get_current_worker
from rich.text import Text
from rich.panel import Panel

from config import load_config, Config, resolve_binary_path, get_app_root
from downloader import DownloadQueue, DownloadItem, DownloadStatus, DownloadProgress
from templates import Template, BUILTIN_TEMPLATES, get_all_templates, save_template, export_template_to_command
from guide import get_guide_sections


# =============================================================================
# MAIN APPLICATION
# =============================================================================

class YtDlpTUI(App):
    """Main TUI application for yt-dlp."""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    .tab-content {
        height: 1fr;
    }
    
    .form-section {
        background: $boost;
        padding: 1 2;
        margin: 1 0;
        border: solid $primary;
    }
    
    .form-row {
        height: auto;
        margin: 1 0;
    }
    
    .form-label {
        width: 25;
        content-align: right middle;
        text-style: bold;
    }
    
    .form-input {
        width: 1fr;
    }
    
    .button-row {
        align: center middle;
        height: auto;
        margin-top: 1;
    }
    
    .progress-panel {
        background: $boost;
        padding: 1 2;
        margin: 1 0;
        border: solid $success;
    }
    
    .status-queued { color: $warning; }
    .status-downloading { color: $success; }
    .status-paused { color: $warning; }
    .status-completed { color: $success; }
    .status-failed { color: $error; }
    .status-cancelled { color: $secondary; }
    
    .guide-section {
        background: $boost;
        padding: 1 2;
        margin: 1 0;
    }
    
    .guide-title {
        text-style: bold;
        color: $primary;
    }
    
    .template-card {
        width: 40;
        height: 8;
        background: $boost;
        border: solid $primary;
        padding: 1 2;
        margin: 1;
    }
    
    .binary-ok { color: $success; }
    .binary-missing { color: $error; }
    .binary-warning { color: $warning; }
    
    #url-input {
        height: 5;
    }
    
    #log-output {
        height: 1fr;
        background: $background;
        border: solid $primary;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("ctrl+q", "quit", "Quit"),
        Binding("1", "switch_tab(1)", "Downloader"),
        Binding("2", "switch_tab(2)", "Queue"),
        Binding("3", "switch_tab(3)", "Settings"),
        Binding("4", "switch_tab(4)", "Templates"),
        Binding("5", "switch_tab(5)", "Creator"),
        Binding("6", "switch_tab(6)", "Guide"),
        Binding("d", "delete_selected", "Delete"),
        Binding("r", "retry_selected", "Retry"),
        Binding("c", "copy_command", "Copy Cmd"),
        Binding("s", "goto_settings", "Settings"),
        Binding("f1", "toggle_guide", "Guide"),
        Binding("/", "focus_url", "Focus URL"),
    ]
    
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.queue = DownloadQueue(self.config)
        self.binary_warnings: List[str] = []
        self.current_download_worker: Optional[Worker] = None
    
    def on_mount(self) -> None:
        """Called when app starts."""
        self.title = "yt-dlp TUI"
        self.sub_title = "Terminal Video Downloader"
        
        # Check binaries
        self._check_binaries()
        
        # Show warnings if any
        if self.binary_warnings:
            self.notify("\n".join(self.binary_warnings), severity="warning", timeout=10)
    
    def _check_binaries(self) -> None:
        """Check for required binaries."""
        is_windows = sys.platform == "win32"
        bin_dir = get_app_root() / self.config.bin_dir
        
        # Ensure bin directory exists
        bin_dir.mkdir(parents=True, exist_ok=True)
        
        binaries = ["yt-dlp", "ffmpeg", "ffprobe", "aria2c"]
        
        for binary in binaries:
            suffix = ".exe" if is_windows else ""
            bin_name = f"{binary}{suffix}"
            
            # Check ./bin/ first
            bin_path = bin_dir / bin_name
            bin_ok = bin_path.exists()
            
            # Check PATH
            path_ok = shutil.which(binary) is not None
            
            if not bin_ok and not path_ok:
                self.binary_warnings.append(
                    f"[red]⚠ {bin_name}[/red] not found in ./bin/ or PATH"
                )
        
        # Special note about yt-dlp-ejs
        yt_dlp_path = resolve_binary_path("yt-dlp", self.config)
        if yt_dlp_path:
            # Note about JS runtime
            pass  # Could check for deno/node but not critical
    
    def compose(self) -> ComposeResult:
        """Create the UI layout."""
        yield Header()
        
        with TabbedContent(id="main-tabs"):
            # TAB 1: DOWNLOADER
            with TabPane("Downloader", id="tab-downloader"):
                yield self._compose_downloader_tab()
            
            # TAB 2: QUEUE
            with TabPane("Queue", id="tab-queue"):
                yield self._compose_queue_tab()
            
            # TAB 3: SETTINGS
            with TabPane("Settings", id="tab-settings"):
                yield self._compose_settings_tab()
            
            # TAB 4: QUICK TEMPLATES
            with TabPane("Templates", id="tab-templates"):
                yield self._compose_templates_tab()
            
            # TAB 5: TEMPLATE CREATOR
            with TabPane("Creator", id="tab-creator"):
                yield self._compose_creator_tab()
            
            # TAB 6: GUIDE
            with TabPane("Guide", id="tab-guide"):
                yield self._compose_guide_tab()
        
        yield Footer()
    
    def _compose_downloader_tab(self) -> Container:
        """Compose the Downloader tab."""
        with Container():
            with Vertical(classes="form-section"):
                yield Label("URLs (one per line):", classes="form-label")
                yield Input(placeholder="https://youtube.com/watch?v=...\nhttps://...", id="url-input", type="text")
            
            with Horizontal(classes="form-row"):
                yield Label("Format:", classes="form-label")
                yield Select(
                    [
                        ("Best (auto)", "best_auto"),
                        ("4K", "4k"),
                        ("1080p", "1080p"),
                        ("720p", "720p"),
                        ("480p", "480p"),
                        ("Audio only (best)", "audio_only"),
                        ("MP3 (built-in)", "-t mp3"),
                        ("AAC (built-in)", "-t aac"),
                        ("MP4 (built-in)", "-t mp4"),
                        ("MKV (built-in)", "-t mkv"),
                        ("Custom", "custom"),
                    ],
                    value="best_auto",
                    id="format-select",
                    allow_blank=False,
                )
            
            with Horizontal(classes="form-row", id="custom-format-row"):
                yield Label("Custom format:", classes="form-label")
                yield Input(placeholder="bestvideo+bestaudio/best", id="custom-format-input")
            
            with Horizontal(classes="form-row"):
                yield Label("Output template:", classes="form-label")
                yield Select(
                    [
                        ("%(title)s [%(id)s].%(ext)s", "%(title)s [%(id)s].%(ext)s"),
                        ("%(uploader)s/%(title)s.%(ext)s", "%(uploader)s/%(title)s.%(ext)s"),
                        ("%(upload_date>%Y-%m-%d)s %(title)s.%(ext)s", "%(upload_date>%Y-%m-%d)s %(title)s.%(ext)s"),
                        ("%(playlist_title)s/%(playlist_index)03d %(title)s.%(ext)s", "%(playlist_title)s/%(playlist_index)03d %(title)s.%(ext)s"),
                        ("%(channel)s/%(upload_date>%Y)s/%(title)s.%(ext)s", "%(channel)s/%(upload_date>%Y)s/%(title)s.%(ext)s"),
                    ],
                    value="%(title)s [%(id)s].%(ext)s",
                    id="output-template-select",
                    allow_blank=False,
                )
            
            with Horizontal(classes="form-row"):
                yield Label("Output directory:", classes="form-label")
                yield Input(value=self.config.output.default_save_path, id="output-dir-input")
                yield Button("Browse", id="browse-btn", variant="default")
            
            with Horizontal(classes="form-row"):
                yield Label("Concurrent fragments:", classes="form-label")
                yield Input(value=str(self.config.download.concurrent_fragments), id="concurrent-fragments-input", type="integer")
            
            with Horizontal(classes="button-row"):
                yield Button("Start Download", id="start-download-btn", variant="success")
                yield Button("Pause", id="pause-btn", variant="warning")
                yield Button("Cancel", id="cancel-btn", variant="error")
                yield Button("Open Folder", id="open-folder-btn", variant="default")
            
            with Vertical(classes="progress-panel"):
                yield Label("Live Progress:", classes="form-label")
                yield ProgressBar(show_eta=True, show_percentage=True, id="live-progress-bar")
                yield Static("", id="progress-details")
            
            yield RichLog(markup=True, highlight=True, id="log-output")
        
        return Container()
    
    def _compose_queue_tab(self) -> Container:
        """Compose the Queue tab."""
        with Container():
            with Horizontal(classes="button-row"):
                yield Button("Refresh", id="refresh-queue-btn", variant="default")
                yield Button("Clear Completed", id="clear-completed-btn", variant="warning")
            
            dt = DataTable(id="queue-table")
            dt.add_columns("ID", "Status", "Filename", "Progress", "Speed", "ETA", "Error")
            yield dt
        
        return Container()
    
    def _compose_settings_tab(self) -> Container:
        """Compose the Settings tab."""
        with ScrollableContainer():
            # OUTPUT section
            yield Static("[bold]── OUTPUT ───────────────────────────────[/bold]", markup=True)
            with Vertical(classes="form-section"):
                yield self._setting_row("Default save path", "-P / --paths", 
                    Input(value=self.config.output.default_save_path, id="setting-save-path"))
                yield self._setting_row("Filename template", "-o / --output",
                    Input(value=self.config.output.default_filename_template, id="setting-filename-template"))
                yield self._setting_row("Restrict filenames (ASCII)", "--restrict-filenames",
                    Switch(value=self.config.output.restrict_filenames, id="setting-restrict-filenames"))
                yield self._setting_row("Trim filename length", "--trim-filenames LENGTH",
                    Input(value=str(self.config.output.trim_filenames), id="setting-trim-filenames", type="integer"))
                yield self._setting_row("Write .info.json", "--write-info-json",
                    Switch(value=self.config.output.write_info_json, id="setting-write-info-json"))
                yield self._setting_row("Write .description", "--write-description",
                    Switch(value=self.config.output.write_description, id="setting-write-description"))
                yield self._setting_row("Use Last-modified for mtime", "--mtime",
                    Switch(value=self.config.output.use_mtime, id="setting-use-mtime"))
            
            # DOWNLOAD section
            yield Static("[bold]── DOWNLOAD ─────────────────────────────[/bold]", markup=True)
            with Vertical(classes="form-section"):
                yield self._setting_row("Concurrent fragments", "-N / --concurrent-fragments (1-16)",
                    Input(value=str(self.config.download.concurrent_fragments), id="setting-concurrent-fragments", type="integer"))
                yield self._setting_row("Rate limit", "-r / --limit-rate (e.g. 4M, 500K)",
                    Input(value=self.config.download.rate_limit, id="setting-rate-limit"))
                yield self._setting_row("Retry count", "-R / --retries (default 10)",
                    Input(value=str(self.config.download.retry_count), id="setting-retry-count", type="integer"))
                yield self._setting_row("Continue partial downloads", "-c / --continue",
                    Switch(value=self.config.download.continue_partial, id="setting-continue-partial"))
                yield self._setting_row("Use download archive", "--download-archive",
                    Switch(value=self.config.download.use_download_archive, id="setting-use-archive"))
                yield self._setting_row("Playlist items range", "-I / --playlist-items (e.g. 1:10)",
                    Input(value=self.config.download.playlist_items, id="setting-playlist-items"))
                yield self._setting_row("Min filesize", "--min-filesize",
                    Input(value=self.config.download.min_filesize, id="setting-min-filesize"))
                yield self._setting_row("Max filesize", "--max-filesize",
                    Input(value=self.config.download.max_filesize, id="setting-max-filesize"))
                yield self._setting_row("Max downloads per run", "--max-downloads NUMBER",
                    Input(value=str(self.config.download.max_downloads), id="setting-max-downloads", type="integer"))
                yield self._setting_row("Sleep interval (sec)", "--sleep-interval",
                    Input(value=str(self.config.download.sleep_interval), id="setting-sleep-interval", type="number"))
                yield self._setting_row("Max sleep interval", "--max-sleep-interval",
                    Input(value=str(self.config.download.max_sleep_interval), id="setting-max-sleep-interval", type="number"))
            
            # ARIA2C section
            yield Static("[bold]── ARIA2C INTEGRATION ────────────────────[/bold]", markup=True)
            with Vertical(classes="form-section"):
                yield self._setting_row("Enable aria2c", "--downloader aria2c",
                    Switch(value=self.config.aria2c.enabled, id="setting-aria2c-enabled"))
                yield self._setting_row("Connections per server", "-x N (default 16)",
                    Input(value=str(self.config.aria2c.connections_per_server), id="setting-aria2c-connections", type="integer"))
                yield self._setting_row("Split count", "-s N (default 16)",
                    Input(value=str(self.config.aria2c.split_count), id="setting-aria2c-splits", type="integer"))
                yield self._setting_row("Min split size", "-k SIZE (e.g. 1M)",
                    Input(value=self.config.aria2c.min_split_size, id="setting-aria2c-min-split"))
                yield self._setting_row("Max concurrent aria2c", "-j N",
                    Input(value=str(self.config.aria2c.max_concurrent), id="setting-aria2c-max-concurrent", type="integer"))
                
                aria2c_preview = get_app_root()
                yield Static(f"[dim]Preview: --downloader-args \"aria2c:{self._get_aria2c_preview()}\"[/dim]", 
                    id="aria2c-preview", markup=True)
            
            # FFMPEG section
            yield Static("[bold]── FFMPEG / POST-PROCESSING ─────────────[/bold]", markup=True)
            with Vertical(classes="form-section"):
                yield self._setting_row("Remux container", "--remux-video FORMAT",
                    Input(value=self.config.ffmpeg.remux_video, id="setting-remux-video"))
                yield self._setting_row("Re-encode video", "--recode-video FORMAT",
                    Input(value=self.config.ffmpeg.recode_video, id="setting-recode-video"))
                yield self._setting_row("Audio format", "--audio-format (mp3/aac/flac...)",
                    Input(value=self.config.ffmpeg.audio_format, id="setting-audio-format"))
                yield self._setting_row("Audio quality", "--audio-quality (0-10 or 192K)",
                    Input(value=self.config.ffmpeg.audio_quality, id="setting-audio-quality"))
                yield self._setting_row("Keep intermediate video", "-k / --keep-video",
                    Switch(value=self.config.ffmpeg.keep_video, id="setting-keep-video"))
                yield self._setting_row("Split by chapters", "--split-chapters",
                    Switch(value=self.config.ffmpeg.split_chapters, id="setting-split-chapters"))
                yield self._setting_row("Force keyframes at cuts", "--force-keyframes-at-cuts",
                    Switch(value=self.config.ffmpeg.force_keyframes, id="setting-force-keyframes"))
                yield self._setting_row("Custom ffmpeg args", "--postprocessor-args",
                    Input(value=self.config.ffmpeg.postprocessor_args, id="setting-postprocessor-args"))
            
            # SUBTITLES section
            yield Static("[bold]── SUBTITLES ────────────────────────────[/bold]", markup=True)
            with Vertical(classes="form-section"):
                yield self._setting_row("Write subtitles", "--write-subs",
                    Switch(value=self.config.subtitles.write_subs, id="setting-write-subs"))
                yield self._setting_row("Write auto-generated", "--write-auto-subs",
                    Switch(value=self.config.subtitles.write_auto_subs, id="setting-write-auto-subs"))
                yield self._setting_row("Subtitle languages", "--sub-langs (e.g. en,ja)",
                    Input(value=self.config.subtitles.sub_langs, id="setting-sub-langs"))
                yield self._setting_row("Subtitle format", "--sub-format (srt/ass/best)",
                    Input(value=self.config.subtitles.sub_format, id="setting-sub-format"))
                yield self._setting_row("Embed subtitles", "--embed-subs",
                    Switch(value=self.config.subtitles.embed_subs, id="setting-embed-subs"))
                yield self._setting_row("Convert subtitle format", "--convert-subs FORMAT",
                    Input(value=self.config.subtitles.convert_subs, id="setting-convert-subs"))
            
            # METADATA section
            yield Static("[bold]── METADATA & THUMBNAILS ────────────────[/bold]", markup=True)
            with Vertical(classes="form-section"):
                yield self._setting_row("Embed thumbnail", "--embed-thumbnail",
                    Switch(value=self.config.metadata.embed_thumbnail, id="setting-embed-thumbnail"))
                yield self._setting_row("Embed metadata", "--embed-metadata",
                    Switch(value=self.config.metadata.embed_metadata, id="setting-embed-metadata"))
                yield self._setting_row("Embed chapters", "--embed-chapters",
                    Switch(value=self.config.metadata.embed_chapters, id="setting-embed-chapters"))
                yield self._setting_row("Write thumbnail to disk", "--write-thumbnail",
                    Switch(value=self.config.metadata.write_thumbnail, id="setting-write-thumbnail"))
                yield self._setting_row("Convert thumbnails", "--convert-thumbnails FORMAT",
                    Input(value=self.config.metadata.convert_thumbnails, id="setting-convert-thumbnails"))
            
            # SPONSORBLOCK section
            yield Static("[bold]── SPONSORBLOCK ─────────────────────────[/bold]", markup=True)
            with Vertical(classes="form-section"):
                yield self._setting_row("Mark categories", "--sponsorblock-mark CATS",
                    Input(value=self.config.sponsorblock.mark_categories, id="setting-sb-mark"))
                yield self._setting_row("Remove categories", "--sponsorblock-remove CATS",
                    Input(value=self.config.sponsorblock.remove_categories, id="setting-sb-remove"))
                yield self._setting_row("API URL", "--sponsorblock-api URL",
                    Input(value=self.config.sponsorblock.api_url, id="setting-sb-api"))
            
            # NETWORK section
            yield Static("[bold]── NETWORK & AUTH ───────────────────────[/bold]", markup=True)
            with Vertical(classes="form-section"):
                yield self._setting_row("Proxy", "--proxy URL",
                    Input(value=self.config.network.proxy, id="setting-proxy"))
                yield self._setting_row("Impersonate browser", "--impersonate CLIENT",
                    Input(value=self.config.network.impersonate, id="setting-impersonate"))
                yield self._setting_row("Cookies file", "--cookies FILE",
                    Input(value=self.config.network.cookies_file, id="setting-cookies-file"))
                yield self._setting_row("Cookies from browser", "--cookies-from-browser",
                    Input(value=self.config.network.cookies_from_browser, id="setting-cookies-browser"))
                yield self._setting_row("Socket timeout", "--socket-timeout SECONDS",
                    Input(value=str(self.config.network.socket_timeout), id="setting-socket-timeout", type="integer"))
                yield self._setting_row("Force IPv4", "-4",
                    Switch(value=self.config.network.force_ipv4, id="setting-ipv4"))
                yield self._setting_row("Force IPv6", "-6",
                    Switch(value=self.config.network.force_ipv6, id="setting-ipv6"))
            
            # ADVANCED section
            yield Static("[bold]── ADVANCED ─────────────────────────────[/bold]", markup=True)
            with Vertical(classes="form-section"):
                yield self._setting_row("Update channel", "--update-to CHANNEL",
                    Input(value=self.config.advanced.update_channel, id="setting-update-channel"))
                yield self._setting_row("Geo-bypass (XFF)", "--xff VALUE",
                    Input(value=self.config.advanced.geo_bypass, id="setting-geo-bypass"))
                yield self._setting_row("Ignore errors", "-i / --ignore-errors",
                    Switch(value=self.config.advanced.ignore_errors, id="setting-ignore-errors"))
                yield self._setting_row("Verbose output", "-v / --verbose",
                    Switch(value=self.config.advanced.verbose, id="setting-verbose"))
                yield self._setting_row("Max concurrent downloads", "App setting",
                    Input(value=str(self.config.max_concurrent_downloads), id="setting-max-concurrent", type="integer"))
            
            with Horizontal(classes="button-row"):
                yield Button("Save Settings", id="save-settings-btn", variant="success")
                yield Button("Reset to Defaults", id="reset-settings-btn", variant="warning")
        
        return Container()
    
    def _setting_row(self, label: str, flag_hint: str, widget) -> Horizontal:
        """Create a settings row with label, widget, and flag hint."""
        with Horizontal(classes="form-row"):
            yield Label(label, classes="form-label")
            yield widget
            yield Static(f"[dim]{flag_hint}[/dim]", markup=True)
        return Horizontal()
    
    def _get_aria2c_preview(self) -> str:
        """Get preview of aria2c arguments."""
        aria = self.config.aria2c
        args = []
        if aria.enabled:
            args.append(f"-x {aria.connections_per_server}")
            args.append(f"-s {aria.split_count}")
            args.append(f"-k {aria.min_split_size}")
            args.append(f"-j {aria.max_concurrent}")
            if self.config.download.continue_partial:
                args.append("--continue")
        return " ".join(args)
    
    def _compose_templates_tab(self) -> Container:
        """Compose the Quick Templates tab."""
        with ScrollableContainer():
            for i, template in enumerate(BUILTIN_TEMPLATES):
                flags_str = " ".join(template.flags[:3])
                if len(template.flags) > 3:
                    flags_str += "..."
                
                card_content = f"[bold]{template.name}[/bold]\n[dim]{template.description}[/dim]\n[cyan]-f {template.format}[/cyan] {flags_str}"
                
                with Container(classes="template-card"):
                    yield Static(card_content, markup=True, id=f"template-card-{i}")
                    yield Button("Use This", id=f"use-template-{i}", variant="primary")
        
        return Container()
    
    def _compose_creator_tab(self) -> Container:
        """Compose the Template Creator tab."""
        with ScrollableContainer():
            yield Static("[bold]Template Creator[/bold]", markup=True)
            
            with Vertical(classes="form-section"):
                yield self._setting_row("Template name", "(required)",
                    Input(placeholder="My Custom Template", id="creator-name"))
                yield self._setting_row("Description", "",
                    Input(placeholder="Brief description...", id="creator-description"))
            
            yield Static("[bold]Format Settings[/bold]", markup=True)
            with Vertical(classes="form-section"):
                yield self._setting_row("Format preset", "",
                    Select(
                        [
                            ("Best (auto)", "best_auto"),
                            ("4K", "4k"),
                            ("1080p", "1080p"),
                            ("720p", "720p"),
                            ("480p", "480p"),
                            ("Audio only", "audio_only"),
                            ("MP3", "-t mp3"),
                            ("AAC", "-t aac"),
                            ("MP4", "-t mp4"),
                            ("MKV", "-t mkv"),
                            ("Custom", "custom"),
                        ],
                        value="best_auto",
                        id="creator-format-select",
                    ))
                yield self._setting_row("Custom format string", "--format",
                    Input(placeholder="bestvideo+bestaudio/best", id="creator-custom-format"))
                yield self._setting_row("Output template", "-o",
                    Input(value="%(title)s [%(id)s].%(ext)s", id="creator-output-template"))
            
            yield Static("[bold]Flags[/bold]", markup=True)
            with Vertical(classes="form-section"):
                yield self._setting_row("Extra flags (space-separated)", "Appended verbatim",
                    Input(placeholder="--embed-metadata --embed-thumbnail", id="creator-extra-flags"))
                yield self._setting_row("aria2c args", "--downloader-args",
                    Input(placeholder="-x 16 -s 16 -k 1M", id="creator-aria2c-args"))
            
            yield Static("[bold]Command Preview[/bold]", markup=True)
            with Vertical(classes="form-section"):
                yield Static("[dim]Command will appear here...[/dim]", id="creator-command-preview", markup=True)
            
            with Horizontal(classes="button-row"):
                yield Button("Preview Command", id="creator-preview-btn", variant="default")
                yield Button("Save Template", id="creator-save-btn", variant="success")
                yield Button("Export to Clipboard", id="creator-export-btn", variant="primary")
        
        return Container()
    
    def _compose_guide_tab(self) -> Container:
        """Compose the Guide tab."""
        with ScrollableContainer():
            for section in get_guide_sections():
                yield Static(f"[bold]{section['title']}[/bold]", markup=True, classes="guide-title")
                yield Static(section["content"], markup=True, classes="guide-section")
        
        return Container()
    
    # =========================================================================
    # ACTION HANDLERS
    # =========================================================================
    
    def action_switch_tab(self, tab_num: int) -> None:
        """Switch to a specific tab."""
        tabs = ["tab-downloader", "tab-queue", "tab-settings", "tab-templates", "tab-creator", "tab-guide"]
        if 1 <= tab_num <= len(tabs):
            self.query_one("#main-tabs", TabbedContent).active = tabs[tab_num - 1]
    
    def action_goto_settings(self) -> None:
        """Go to settings tab."""
        self.action_switch_tab(3)
    
    def action_toggle_guide(self) -> None:
        """Toggle guide tab."""
        self.action_switch_tab(6)
    
    def action_focus_url(self) -> None:
        """Focus the URL input field."""
        url_input = self.query_one("#url-input", Input)
        url_input.focus()
    
    def action_delete_selected(self) -> None:
        """Delete selected queue item."""
        # Implementation would go here
        pass
    
    def action_retry_selected(self) -> None:
        """Retry selected failed download."""
        # Implementation would go here
        pass
    
    def action_copy_command(self) -> None:
        """Copy command to clipboard."""
        # Implementation would go here
        self.notify("Command copied to clipboard (not implemented)")
    
    # =========================================================================
    # EVENT HANDLERS
    # =========================================================================
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        btn_id = event.button.id
        
        if btn_id == "start-download-btn":
            self._start_download()
        elif btn_id == "pause-btn":
            self._pause_download()
        elif btn_id == "cancel-btn":
            self._cancel_download()
        elif btn_id == "open-folder-btn":
            self._open_folder()
        elif btn_id == "refresh-queue-btn":
            self._refresh_queue()
        elif btn_id == "clear-completed-btn":
            self._clear_completed()
        elif btn_id == "save-settings-btn":
            self._save_settings()
        elif btn_id == "reset-settings-btn":
            self._reset_settings()
        elif btn_id.startswith("use-template-"):
            idx = int(btn_id.split("-")[-1])
            self._use_template(idx)
        elif btn_id == "creator-preview-btn":
            self._preview_creator_command()
        elif btn_id == "creator-save-btn":
            self._save_creator_template()
        elif btn_id == "creator-export-btn":
            self._export_creator_template()
    
    def _start_download(self) -> None:
        """Start a download from the Downloader tab."""
        url_input = self.query_one("#url-input", Input)
        urls = [u.strip() for u in url_input.value.split("\n") if u.strip()]
        
        if not urls:
            self.notify("Please enter at least one URL", severity="error")
            return
        
        # Get format
        format_select = self.query_one("#format-select", Select)
        format_value = format_select.value
        
        custom_format_input = self.query_one("#custom-format-input", Input)
        custom_format = custom_format_input.value if format_value == "custom" else ""
        
        # Map select values to format strings
        format_map = {
            "best_auto": "bestvideo+bestaudio/best",
            "4k": "bestvideo[height<=2160]+bestaudio/best",
            "1080p": "bestvideo[height<=1080]+bestaudio/best",
            "720p": "bestvideo[height<=720]+bestaudio/best",
            "480p": "bestvideo[height<=480]+bestaudio/best",
            "audio_only": "bestaudio/best",
        }
        
        if format_value.startswith("-t "):
            format_str = format_value  # Built-in preset
        else:
            format_str = format_map.get(format_value, "bestvideo+bestaudio/best")
            if custom_format:
                format_str = custom_format
        
        # Get output template
        output_select = self.query_one("#output-template-select", Select)
        output_template = output_select.value
        
        # Get output directory
        dir_input = self.query_one("#output-dir-input", Input)
        output_dir = dir_input.value
        
        # Get concurrent fragments
        frag_input = self.query_one("#concurrent-fragments-input", Input)
        try:
            concurrent_frags = int(frag_input.value) if frag_input.value else 1
        except ValueError:
            concurrent_frags = 1
        
        # Build command args
        cmd_args = [
            "-f", format_str,
            "-o", f"{output_dir}/{output_template}",
            "-N", str(concurrent_frags),
        ]
        
        # Add settings-based flags
        if self.config.output.restrict_filenames:
            cmd_args.append("--restrict-filenames")
        if self.config.output.write_info_json:
            cmd_args.append("--write-info-json")
        if self.config.output.write_description:
            cmd_args.append("--write-description")
        if self.config.ffmpeg.embed_thumbnail:
            cmd_args.append("--embed-thumbnail")
        if self.config.ffmpeg.embed_metadata:
            cmd_args.append("--embed-metadata")
        if self.config.subtitles.embed_subs:
            cmd_args.append("--embed-subs")
        if self.config.sponsorblock.remove_categories:
            cmd_args.extend(["--sponsorblock-remove", self.config.sponsorblock.remove_categories])
        
        # Add each URL as a separate download item
        for url in urls:
            item = self.queue.add_item(url, cmd_args.copy())
            self.notify(f"Added to queue: {url[:50]}...")
        
        # Start processing queue
        self._process_queue()
    
    async def _process_queue(self) -> None:
        """Process the download queue."""
        while True:
            active = self.queue.get_active_count()
            queued = self.queue.get_queued_count()
            
            if queued == 0 and active == 0:
                break
            
            if active >= self.config.max_concurrent_downloads:
                await asyncio.sleep(1)
                continue
            
            # Find next queued item
            for item in self.queue.items:
                if item.status == DownloadStatus.QUEUED:
                    # Start download in worker
                    self.run_worker(
                        self._run_download(item),
                        exclusive=True,
                        description=f"Downloading {item.url[:30]}...",
                    )
                    break
            
            await asyncio.sleep(0.5)
    
    async def _run_download(self, item: DownloadItem) -> None:
        """Run a single download."""
        await self.queue.start_download(
            item,
            progress_callback=self._on_download_progress
        )
    
    def _on_download_progress(self, item: DownloadItem, line: str) -> None:
        """Handle download progress updates."""
        # Update progress bar
        try:
            progress_bar = self.query_one("#live-progress-bar", ProgressBar)
            progress_bar.progress = item.progress.percentage
            
            details = self.query_one("#progress-details", Static)
            details.update(
                f"[cyan]{item.progress.filename}[/cyan]\n"
                f"Speed: {item.progress.speed} | ETA: {item.progress.eta}\n"
                f"Size: {item.progress.total_size}"
            )
        except Exception:
            pass
        
        # Log output
        try:
            log = self.query_one("#log-output", RichLog)
            log.write(line)
        except Exception:
            pass
    
    def _pause_download(self) -> None:
        """Pause current download."""
        self.notify("Pause not fully implemented")
    
    def _cancel_download(self) -> None:
        """Cancel current download."""
        self.notify("Cancel not fully implemented")
    
    def _open_folder(self) -> None:
        """Open download folder."""
        dir_input = self.query_one("#output-dir-input", Input)
        output_dir = Path(dir_input.value)
        
        if output_dir.exists():
            import subprocess
            if sys.platform == "win32":
                subprocess.Popen(["explorer", str(output_dir.absolute())])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(output_dir.absolute())])
            else:
                subprocess.Popen(["xdg-open", str(output_dir.absolute())])
            self.notify(f"Opening {output_dir}")
        else:
            self.notify(f"Directory does not exist: {output_dir}", severity="warning")
    
    def _refresh_queue(self) -> None:
        """Refresh the queue table."""
        self._update_queue_table()
    
    def _update_queue_table(self) -> None:
        """Update the queue DataTable."""
        try:
            dt = self.query_one("#queue-table", DataTable)
            dt.clear()
            
            for item in self.queue.items:
                status_style = {
                    DownloadStatus.QUEUED: "[yellow]queued[/yellow]",
                    DownloadStatus.DOWNLOADING: "[green]downloading[/green]",
                    DownloadStatus.PAUSED: "[orange]paused[/orange]",
                    DownloadStatus.COMPLETED: "[green]completed[/green]",
                    DownloadStatus.FAILED: "[red]failed[/red]",
                    DownloadStatus.CANCELLED: "[blue]cancelled[/blue]",
                }.get(item.status, str(item.status))
                
                progress_str = f"{item.progress.percentage:.1f}%" if item.progress.percentage > 0 else "-"
                
                dt.add_row(
                    str(item.id),
                    status_style,
                    item.progress.filename or "-",
                    progress_str,
                    item.progress.speed or "-",
                    item.progress.eta or "-",
                    item.error_message[:30] if item.error_message else "-",
                )
        except Exception:
            pass
    
    def _clear_completed(self) -> None:
        """Clear completed downloads from queue."""
        removed = self.queue.clear_completed()
        self.notify(f"Cleared {removed} completed downloads")
        self._update_queue_table()
    
    def _save_settings(self) -> None:
        """Save settings from the Settings tab."""
        # Read all settings and update config
        # This is a simplified version - full implementation would read all fields
        
        # Example: Save output settings
        try:
            save_path = self.query_one("#setting-save-path", Input).value
            self.config.output.default_save_path = save_path
            
            max_concurrent = self.query_one("#setting-max-concurrent", Input).value
            self.config.max_concurrent_downloads = int(max_concurrent) if max_concurrent else 3
            
            # Save to file
            from config import save_config
            save_config(self.config)
            
            self.notify("Settings saved!", severity="information")
        except Exception as e:
            self.notify(f"Error saving settings: {e}", severity="error")
    
    def _reset_settings(self) -> None:
        """Reset settings to defaults."""
        from config import Config
        self.config = Config()
        self.notify("Settings reset to defaults")
    
    def _use_template(self, index: int) -> None:
        """Apply a built-in template to the Downloader tab."""
        if 0 <= index < len(BUILTIN_TEMPLATES):
            template = BUILTIN_TEMPLATES[index]
            
            # Set format
            format_select = self.query_one("#format-select", Select)
            if template.format.startswith("-t "):
                format_select.value = template.format
            else:
                format_select.value = "custom"
                custom_input = self.query_one("#custom-format-input", Input)
                custom_input.value = template.format
            
            # Set output template
            output_select = self.query_one("#output-template-select", Select)
            output_select.value = template.output_template
            
            self.notify(f"Applied template: {template.name}")
            self.action_switch_tab(1)
    
    def _preview_creator_command(self) -> None:
        """Preview the command from Template Creator."""
        try:
            name = self.query_one("#creator-name", Input).value or "template"
            format_select = self.query_one("#creator-format-select", Select)
            custom_format = self.query_one("#creator-custom-format", Input).value
            output_template = self.query_one("#creator-output-template", Input).value
            extra_flags = self.query_one("#creator-extra-flags", Input).value
            aria2c_args = self.query_one("#creator-aria2c-args", Input).value
            
            # Build format string
            format_map = {
                "best_auto": "bestvideo+bestaudio/best",
                "4k": "bestvideo[height<=2160]+bestaudio/best",
                "1080p": "bestvideo[height<=1080]+bestaudio/best",
                "720p": "bestvideo[height<=720]+bestaudio/best",
                "480p": "bestvideo[height<=480]+bestaudio/best",
                "audio_only": "bestaudio/best",
            }
            
            if format_select.value.startswith("-t "):
                format_str = format_select.value
            elif custom_format:
                format_str = custom_format
            else:
                format_str = format_map.get(format_select.value, "bestvideo+bestaudio/best")
            
            cmd_parts = ["yt-dlp"]
            
            if format_str.startswith("-t "):
                cmd_parts.append(format_str)
            else:
                cmd_parts.extend(["-f", format_str])
            
            cmd_parts.extend(["-o", output_template])
            
            if extra_flags:
                cmd_parts.extend(extra_flags.split())
            
            if aria2c_args:
                cmd_parts.extend(["--downloader", "aria2c"])
                cmd_parts.extend(["--downloader-args", f'aria2c:{aria2c_args}'])
            
            cmd_parts.append("URL")
            
            preview = " ".join(cmd_parts)
            preview_widget = self.query_one("#creator-command-preview", Static)
            preview_widget.update(f"[cyan]{preview}[/cyan]")
        except Exception as e:
            self.notify(f"Error building preview: {e}", severity="error")
    
    def _save_creator_template(self) -> None:
        """Save template from Creator tab."""
        try:
            name = self.query_one("#creator-name", Input).value
            if not name:
                self.notify("Template name is required", severity="error")
                return
            
            description = self.query_one("#creator-description", Input).value
            format_select = self.query_one("#creator-format-select", Select)
            custom_format = self.query_one("#creator-custom-format", Input).value
            output_template = self.query_one("#creator-output-template", Input).value
            extra_flags = self.query_one("#creator-extra-flags", Input).value
            aria2c_args = self.query_one("#creator-aria2c-args", Input).value
            
            # Determine format string
            if format_select.value.startswith("-t "):
                format_str = format_select.value
            elif custom_format:
                format_str = custom_format
            else:
                format_map = {
                    "best_auto": "bestvideo+bestaudio/best",
                    "audio_only": "bestaudio/best",
                }
                format_str = format_map.get(format_select.value, "bestvideo+bestaudio/best")
            
            # Parse extra flags
            flags = extra_flags.split() if extra_flags else []
            
            template = Template(
                name=name,
                description=description,
                format=format_str,
                output_template=output_template,
                flags=flags,
                aria2c_args=aria2c_args,
            )
            
            save_template(template, self.config)
            self.notify(f"Template '{name}' saved!")
        except Exception as e:
            self.notify(f"Error saving template: {e}", severity="error")
    
    def _export_creator_template(self) -> None:
        """Export template as shell command."""
        self._preview_creator_command()
        self.notify("Export to clipboard not fully implemented")


def main():
    """Entry point."""
    app = YtDlpTUI()
    app.run()


if __name__ == "__main__":
    main()
