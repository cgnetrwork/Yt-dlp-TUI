# yt-dlp TUI

A polished Terminal User Interface (TUI) for yt-dlp with keyboard navigation, queue management, and template support.

![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)
![Framework](https://img.shields.io/badge/framework-Textual-green.svg)

## Features

- **6 Tab Interface**: Downloader, Queue, Settings, Templates, Creator, Guide
- **Binary Auto-Detection**: Checks `./bin/` first, then falls back to PATH
- **Queue Management**: Concurrent downloads with pause/resume/retry
- **Template System**: 15 built-in templates + custom template creator
- **Real-time Progress**: Live progress bars parsing yt-dlp's `--newline` output
- **Comprehensive Settings**: All major yt-dlp options exposed with flag hints
- **In-App Guide**: Complete documentation accessible from the app

## Prerequisites

- **Python 3.10+** (matches yt-dlp's minimum requirement)
- **yt-dlp-ejs**: JavaScript runtime for full YouTube support (deno recommended)

### Installing Dependencies

```bash
pip install -r requirements.txt
```

## Binary Setup (./bin/ folder)

The application looks for binaries in this order:
1. `./bin/` folder (application root)
2. System PATH

### Required Binaries

| Binary | Purpose | Download |
|--------|---------|----------|
| yt-dlp | Main download engine | [GitHub Releases](https://github.com/yt-dlp/yt-dlp/releases) |
| ffmpeg | Post-processing (merge, convert) | [FFmpeg-Builds](https://github.com/BtbN/FFmpeg-Builds/releases) |
| ffprobe | Media info (bundled with ffmpeg) | Same as ffmpeg |
| aria2c | Multi-connection downloader | [aria2 Releases](https://github.com/aria2/aria2/releases) |

### OS-Specific Names

- **Windows**: `yt-dlp.exe`, `ffmpeg.exe`, `ffprobe.exe`, `aria2c.exe`
- **macOS/Linux**: `yt-dlp`, `ffmpeg`, `ffprobe`, `aria2c`

### Setup Instructions

```bash
# Create bin directory
mkdir -p ./bin

# Download binaries (Linux example)
cd ./bin
wget https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp
wget https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.gz
wget https://github.com/aria2/aria2/releases/latest/download/aria2-1.37.0-linux-gnu-64bit-http2-ssl.tar.gz

# Make executable
chmod +x yt-dlp
tar -xzf ffmpeg-*.tar.gz && mv ffmpeg-*/bin/* .
tar -xzf aria2-*.tar.gz && mv aria2-*/src/aria2c .
```

### yt-dlp-ejs Requirement

As of current yt-dlp versions, JavaScript extraction support requires a JS runtime:

```bash
# Install deno (recommended)
curl -fsSL https://deno.land/install.sh | sh

# Or use Node.js
npm install -g yt-dlp-ejs
```

## Running the Application

```bash
python main.py
```

Or make it executable:

```bash
chmod +x main.py
./main.py
```

## Configuration (config.toml)

Configuration is stored in `./config/config.toml`. Created automatically on first run.

### Full Field Reference

#### `[output]` Section

| Field | Default | yt-dlp Flag | Description |
|-------|---------|-------------|-------------|
| `default_save_path` | `"./downloads"` | `-P` / `--paths` | Default output directory |
| `default_filename_template` | `"%(title)s [%(id)s].(ext)s"` | `-o` / `--output` | Filename template |
| `restrict_filenames` | `false` | `--restrict-filenames` | ASCII-only filenames |
| `trim_filenames` | `0` | `--trim-filenames LENGTH` | Max filename length (0=disabled) |
| `write_info_json` | `false` | `--write-info-json` | Write metadata JSON sidecar |
| `write_description` | `false` | `--write-description` | Write description file |
| `use_mtime` | `true` | `--mtime` | Use Last-modified header for mtime |

#### `[download]` Section

| Field | Default | yt-dlp Flag | Description |
|-------|---------|-------------|-------------|
| `concurrent_fragments` | `1` | `-N` / `--concurrent-fragments` | Fragments per download (1-16) |
| `rate_limit` | `""` | `-r` / `--limit-rate` | Rate limit (e.g., "4M", "500K") |
| `retry_count` | `10` | `-R` / `--retries` | Number of retries |
| `continue_partial` | `true` | `-c` / `--continue` | Resume partial downloads |
| `use_download_archive` | `true` | `--download-archive` | Deduplication via archive |
| `playlist_items` | `""` | `-I` / `--playlist-items` | Range (e.g., "1:10", "-5::") |
| `min_filesize` | `""` | `--min-filesize` | Minimum file size filter |
| `max_filesize` | `""` | `--max-filesize` | Maximum file size filter |
| `date_filter` | `""` | `--date` | Filter by date |
| `datebefore` | `""` | `--datebefore` | Before date filter |
| `dateafter` | `""` | `--dateafter` | After date filter |
| `max_downloads` | `0` | `--max-downloads` | Max downloads per run (0=unlimited) |
| `sleep_interval` | `0.0` | `--sleep-interval` | Min sleep between downloads |
| `max_sleep_interval` | `0.0` | `--max-sleep-interval` | Max sleep between downloads |

#### `[aria2c]` Section

| Field | Default | aria2c Flag | Description |
|-------|---------|-------------|-------------|
| `enabled` | `true` | `--downloader aria2c` | Enable aria2c integration |
| `connections_per_server` | `16` | `-x N` | Connections per server |
| `split_count` | `16` | `-s N` | File split count |
| `min_split_size` | `"1M"` | `-k SIZE` | Minimum split size |
| `max_concurrent` | `5` | `-j N` | Max parallel aria2c downloads |

#### `[ffmpeg]` Section

| Field | Default | yt-dlp Flag | Description |
|-------|---------|-------------|-------------|
| `remux_video` | `""` | `--remux-video FORMAT` | Container format (mp4/mkv/webm) |
| `recode_video` | `""` | `--recode-video FORMAT` | Re-encode video format |
| `audio_format` | `""` | `--audio-format` | Audio format (mp3/aac/flac) |
| `audio_quality` | `""` | `--audio-quality` | Quality (0-10 or bitrate) |
| `keep_video` | `false` | `-k` / `--keep-video` | Keep intermediate video |
| `split_chapters` | `false` | `--split-chapters` | Split by chapters |
| `force_keyframes` | `false` | `--force-keyframes-at-cuts` | Force keyframes at cuts |
| `postprocessor_args` | `""` | `--postprocessor-args` | Custom ffmpeg args |

#### `[subtitles]` Section

| Field | Default | yt-dlp Flag | Description |
|-------|---------|-------------|-------------|
| `write_subs` | `false` | `--write-subs` | Download subtitles |
| `write_auto_subs` | `false` | `--write-auto-subs` | Download auto-generated subs |
| `sub_langs` | `"en"` | `--sub-langs` | Language codes (e.g., "en,ja") |
| `sub_format` | `"best"` | `--sub-format` | Format (srt/ass/vtt/best) |
| `embed_subs` | `false` | `--embed-subs` | Embed in video (mp4/webm/mkv) |
| `convert_subs` | `""` | `--convert-subs FORMAT` | Convert subtitle format |

#### `[metadata]` Section

| Field | Default | yt-dlp Flag | Description |
|-------|---------|-------------|-------------|
| `embed_thumbnail` | `true` | `--embed-thumbnail` | Embed thumbnail as cover art |
| `embed_metadata` | `true` | `--embed-metadata` | Embed all metadata tags |
| `embed_chapters` | `false` | `--embed-chapters` | Add chapter markers |
| `write_thumbnail` | `false` | `--write-thumbnail` | Write thumbnail to disk |
| `convert_thumbnails` | `""` | `--convert-thumbnails` | Convert thumbnail format |
| `parse_metadata` | `""` | `--parse-metadata` | Parse/modify metadata fields |

#### `[sponsorblock]` Section

| Field | Default | yt-dlp Flag | Description |
|-------|---------|-------------|-------------|
| `mark_categories` | `""` | `--sponsorblock-mark CATS` | Mark segments as chapters |
| `remove_categories` | `""` | `--sponsorblock-remove CATS` | Remove segments from video |
| `api_url` | `""` | `--sponsorblock-api URL` | Custom SponsorBlock API URL |

#### `[network]` Section

| Field | Default | yt-dlp Flag | Description |
|-------|---------|-------------|-------------|
| `proxy` | `""` | `--proxy URL` | HTTP/SOCKS proxy URL |
| `impersonate` | `""` | `--impersonate CLIENT` | Browser impersonation |
| `cookies_file` | `""` | `--cookies FILE` | Netscape cookies file |
| `cookies_from_browser` | `""` | `--cookies-from-browser` | Load from browser |
| `socket_timeout` | `0` | `--socket-timeout` | Socket timeout seconds |
| `add_headers` | `""` | `--add-headers` | Custom HTTP headers |
| `force_ipv4` | `false` | `-4` | Force IPv4 |
| `force_ipv6` | `false` | `-6` | Force IPv6 |
| `sleep_requests` | `0.0` | `--sleep-requests` | Sleep between requests |

#### `[advanced]` Section

| Field | Default | yt-dlp Flag | Description |
|-------|---------|-------------|-------------|
| `update_channel` | `""` | `--update-to CHANNEL` | Update channel (stable/nightly) |
| `geo_bypass` | `""` | `--xff VALUE` | Geo-restriction workaround |
| `ignore_errors` | `false` | `-i` / `--ignore-errors` | Continue on errors |
| `verbose` | `false` | `-v` / `--verbose` | Verbose output |

#### App Settings (Root Level)

| Field | Default | Description |
|-------|---------|-------------|
| `max_concurrent_downloads` | `3` | Maximum parallel downloads |
| `queue_file` | `"./data/queue.json"` | Queue persistence file |
| `archive_file` | `"./data/archive.txt"` | Download archive file |
| `templates_dir` | `"./templates"` | Templates directory |
| `bin_dir` | `"./bin"` | Binaries directory |

## Template JSON Schema

Templates are stored in `./templates/*.json`:

```json
{
  "name": "string (required)",
  "description": "string",
  "format": "string",
  "output_template": "string",
  "flags": ["--flag1", "value1", "--flag2"],
  "aria2c_args": "string",
  "created": "ISO8601 timestamp"
}
```

### Example Template

```json
{
  "name": "My MP3 Template",
  "description": "High quality MP3 with metadata",
  "format": "-t mp3",
  "output_template": "%(title)s.%(ext)s",
  "flags": ["--audio-quality", "320K", "--embed-metadata"],
  "aria2c_args": "-x 16 -s 16 -k 1M",
  "created": "2024-01-15T10:30:00"
}
```

## Built-in Templates (15 Total)

| # | Name | Format | Flags |
|---|------|--------|-------|
| 1 | Best quality | `bestvideo+bestaudio/best` | `--embed-metadata --embed-thumbnail` |
| 2 | MP3 192k | `-t mp3` | `--audio-quality 192K --embed-metadata` |
| 3 | MP3 320k | `-t mp3` | `--audio-quality 320K --embed-metadata` |
| 4 | AAC audio | `-t aac` | `--embed-metadata` |
| 5 | FLAC lossless | `bestaudio` | `-x --audio-format flac` |
| 6 | 1080p MP4 + subs | `-t mp4` | `-f bestvideo[height<=1080]+bestaudio --write-auto-subs --embed-subs` |
| 7 | 720p MP4 | `-t mp4` | `-f bestvideo[height<=720]+bestaudio` |
| 8 | Full playlist (numbered) | `bestvideo+bestaudio/best` | `-o "%(playlist_title)s/%(playlist_index)03d %(title)s.%(ext)s" --yes-playlist` |
| 9 | Playlist audio only | `-t mp3` | `-o "%(playlist_title)s/%(playlist_index)03d %(title)s.%(ext)s" --yes-playlist` |
| 10 | SponsorBlock clean 1080p | `bestvideo[height<=1080]+bestaudio` | `--sponsorblock-remove all,-filler` |
| 11 | Subtitled + chapters | `bestvideo+bestaudio/best` | `--write-auto-subs --embed-subs --embed-chapters --embed-metadata` |
| 12 | Archive mode (no re-dl) | `bestvideo+bestaudio/best` | `--download-archive ./data/archive.txt` |
| 13 | Slow/polite mode | `-t sleep` | (built-in preset with delays) |
| 14 | Cookies from Chrome | `bestvideo+bestaudio/best` | `--cookies-from-browser chrome` |
| 15 | aria2c turbo | `bestvideo+bestaudio/best` | `--downloader aria2c --downloader-args "aria2c:-x 16 -s 16 -k 1M"` |

## Output Template Variables

| Variable | Description |
|----------|-------------|
| `%(id)s` | Video ID |
| `%(title)s` | Video title |
| `%(fulltitle)s` | Full title without truncation |
| `%(ext)s` | File extension |
| `%(url)s` | Video URL |
| `%(uploader)s` | Uploader name |
| `%(channel)s` | Channel name |
| `%(channel_id)s` | Channel ID |
| `%(uploader_id)s` | Uploader ID |
| `%(upload_date)s` | Upload date (YYYYMMDD) |
| `%(upload_date>%Y-%m-%d)s` | Formatted date |
| `%(duration)s` | Duration in seconds |
| `%(duration_string)s` | Human-readable duration |
| `%(view_count)d` | View count |
| `%(like_count)d` | Like count |
| `%(width)d` | Video width |
| `%(height)d` | Video height |
| `%(playlist_title)s` | Playlist name |
| `%(playlist_index)d` | Position in playlist |
| `%(playlist_index)03d` | Zero-padded position |
| `%(playlist_index+10)03d` | Arithmetic expression |

### Examples

- `%(uploader)s/%(title)s.%(ext)s`
- `%(upload_date>%Y-%m-%d)s %(title)s.%(ext)s`
- `%(playlist_title)s/%(playlist_index)03d %(title)s.%(ext)s`
- `%(channel)s/%(upload_date>%Y)s/%(title)s.%(ext)s`

## Format Selection Syntax Cheat-Sheet

### Basic Selectors
- `best` — Best quality single file
- `bestvideo` — Best video-only stream
- `bestaudio` — Best audio-only stream
- `worst` — Worst quality

### Compound Selectors
- `bestvideo+bestaudio/best` — Merge best video+audio, fallback to best single
- `bestvideo[height<=1080]+bestaudio` — 1080p or lower + best audio

### Filtering
- `[height<=1080]` — Height at most 1080 pixels
- `[height>=720]` — Height at least 720 pixels
- `[ext=mp4]` — MP4 container only
- `[vcodec^=avc1]` — Video codec starts with avc1 (h264)
- `[acodec^=mp3]` — Audio codec is mp3
- `[tbr>=128]` — Total bitrate at least 128 kbps
- `[fps>=60]` — 60fps or higher

### Sorting (-S)
- `-S "res:1080,fps,codec:h264"` — Prefer 1080p, then fps, then h264
- `-S "quality,br,res,fps"` — Sort by quality, bitrate, resolution, fps

### Built-in Presets (-t)
- `-t mp3` — Extract to MP3
- `-t aac` — Extract to AAC
- `-t mp4` — MP4 with h264 preference
- `-t mkv` — MKV container
- `-t sleep` — Polite mode with delays

## aria2c Tuning Guide

### Key Options

| Option | Flag | Default | Recommended | Description |
|--------|------|---------|-------------|-------------|
| Connections | `-x N` | 1 | 16 | Max connections per server |
| Splits | `-s N` | 1 | 16 | Split file into N segments |
| Min split size | `-k SIZE` | 1M | 1M | Minimum segment size |
| Parallel downloads | `-j N` | 5 | 5 | Max concurrent downloads |

### Trade-offs

- **Higher `-x`**: More connections = faster downloads but more server load
- **Higher `-s`**: More splits = better parallelism but more overhead
- **Smaller `-k`**: Smaller segments = finer granularity but more requests

### When NOT to Use aria2c

YouTube uses DASH which aria2c doesn't support. The app handles this by using:
```
--downloader aria2c --downloader "dash,m3u8:native"
```

This uses aria2c for regular downloads but native downloader for DASH/HLS streams.

## FFmpeg Post-Processing Command Reference

### Remux Without Re-encoding
```bash
--remux-video mp4    # Fast, lossless container change
```

### Re-encode Video
```bash
--recode-video mp4   # Slower, may lose quality
```

### Extract Audio
```bash
# MP3 at 320kbps
-x --audio-format mp3 --audio-quality 320K

# FLAC lossless
-x --audio-format flac

# M4A (AAC)
-x --audio-format m4a
```

### Embed Media
```bash
--embed-thumbnail     # Embed cover art
--embed-subs          # Embed subtitles (mp4/webm/mkv only)
--embed-chapters      # Add chapter markers
--embed-metadata      # Embed all metadata
```

### Split by Chapters
```bash
--split-chapters      # Create separate files per chapter
```

### Custom FFmpeg Args
```bash
--postprocessor-args "ffmpeg:-vf scale=1280:720"
```

## SponsorBlock Category Reference

| Category | Description |
|----------|-------------|
| `sponsor` | Paid promotion within the video |
| `intro` | Intro animation/jingle |
| `outro` | Outro/end screen |
| `selfpromo` | Self-promotion (merch, Patreon) |
| `preview` | Preview/recap of content |
| `filler` | Filler content not related to main topic |
| `interaction` | Reminder to like/subscribe |
| `music_offtopic` | Off-topic music segments |
| `hook` | Hook at the beginning |
| `poi_highlight` | Point of interest highlight |
| `chapter` | Chapter markers |

### Shortcuts
- `all` — All categories
- `default` (for remove) — All except filler: `all,-filler`

### Examples
```bash
# Mark all except preview as chapters
--sponsorblock-mark all,-preview

# Remove sponsor, intro, outro
--sponsorblock-remove sponsor,intro,outro

# Remove everything except filler
--sponsorblock-remove all,-filler
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Tab` / `Shift+Tab` | Switch tabs forward/backward |
| `1-6` | Jump to specific tab |
| `↑↓` | Navigate lists |
| `/` | Focus URL field |
| `Enter` | Start download / confirm |
| `Space` | Pause/resume selected item |
| `D` | Cancel and delete selected |
| `R` | Retry failed download |
| `C` | Copy command to clipboard |
| `O` | Open download folder |
| `S` | Go to settings |
| `F1` | Toggle guide |
| `Q` / `Ctrl+Q` | Quit application |

## Troubleshooting (Common Errors)

### 1. "yt-dlp warns about outdated version"
**Solution**: Run with `--update-to nightly` or update manually.

### 2. "Requested format is not available"
**Solution**: Check available formats with `-F` flag. The video may not have your requested quality.

### 3. "ffmpeg merge fails"
**Solution**: 
- Verify `--ffmpeg-location` points to correct directory
- Ensure both ffmpeg AND ffprobe are present
- Check ffmpeg isn't blocked by antivirus

### 4. "aria2c errors on YouTube"
**Solution**: YouTube uses DASH which aria2c doesn't support. Use:
```bash
--downloader aria2c --downloader "dash,m3u8:native"
```

### 5. "HTTP Error 403" or bot detection
**Solution**:
- Use `--cookies-from-browser chrome`
- Or try `--impersonate chrome`
- Update yt-dlp to latest version

### 6. "Subtitle embed fails"
**Solution**: Only works with mp4, webm, mkv containers. Remux first:
```bash
--remux-video mkv
```

### 7. "Rate limiting / Too many requests"
**Solution**: Use polite mode:
```bash
-t sleep
# Or manually:
--sleep-interval 10 --max-sleep-interval 20 --sleep-requests 0.75
```

### 8. "Certificate verification failed"
**Solution**: 
```bash
pip install --upgrade certifi
# Or temporarily:
--no-check-certificates
```

### 9. "Download archive not working"
**Solution**: 
- Ensure path is writable
- Archive file is created automatically if it doesn't exist
- Check permissions on `./data/archive.txt`

### 10. "Queue not persisting"
**Solution**: Check that `./data/` directory exists and is writable. Queue saves to `./data/queue.json`.

### 11. "Template not loading"
**Solution**:
- Verify JSON syntax is valid
- Check template is in `./templates/` directory
- Filename must end with `.json`

### 12. "Binary not found" warnings
**Solution**: Download required binaries to `./bin/` or ensure they're in PATH. See [Binary Setup](#binary-setup-bin-folder) section.

## License

MIT License

## Contributing

Contributions welcome! Please open an issue or submit a PR.
