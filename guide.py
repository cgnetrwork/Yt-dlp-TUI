"""
Guide content for yt-dlp TUI.
Structured data for the in-app guide tab.
"""

GUIDE_SECTIONS = [
    {
        "title": "§1 Folder Setup & Binary Paths",
        "content": """
[yellow]Binary Setup[/yellow]

The application looks for binaries in this order:
  1. ./bin/ folder (application root)
  2. System PATH

[bold]Required binaries:[/bold]
• [cyan]yt-dlp[/cyan] — Main download engine
• [cyan]ffmpeg[/cyan] — Post-processing (merge, convert, extract)
• [cyan]ffprobe[/cyan] — Media info (usually bundled with ffmpeg)
• [cyan]aria2c[/cyan] — Multi-connection downloader (optional but recommended)

[bold]OS-specific names:[/bold]
• Windows: yt-dlp.exe, ffmpeg.exe, ffprobe.exe, aria2c.exe
• macOS/Linux: yt-dlp, ffmpeg, ffprobe, aria2c

[bold]Download links:[/bold]
• yt-dlp: https://github.com/yt-dlp/yt-dlp/releases
• FFmpeg: https://github.com/BtbN/FFmpeg-Builds/releases
• aria2c: https://github.com/aria2/aria2/releases

[bold]yt-dlp-ejs requirement:[/bold]
As of current yt-dlp versions, JavaScript extraction support requires
the yt-dlp-ejs package. Install a JS runtime (deno recommended):
  • deno: https://deno.land/
  
Then yt-dlp will auto-detect it.
""",
    },
    {
        "title": "§2 Format Selection Syntax (-f / --format)",
        "content": """
[yellow]Basic Selectors[/yellow]
• [cyan]best[/cyan] — Best quality single file
• [cyan]bestvideo[/cyan] — Best video-only stream
• [cyan]bestaudio[/cyan] — Best audio-only stream
• [cyan]worst[/cyan] — Worst quality single file

[yellow]Compound Selectors[/yellow]
• [cyan]bestvideo+bestaudio/best[/cyan] — Merge best video+audio, fallback to best single
• [cyan]bestvideo[height<=1080]+bestaudio[/cyan] — 1080p or lower + best audio

[yellow]Filtering Attributes[/yellow]
• [cyan][height<=1080][/cyan] — Height at most 1080 pixels
• [cyan][height>=720][/cyan] — Height at least 720 pixels
• [cyan][ext=mp4][/cyan] — MP4 container only
• [cyan][vcodec^=avc1][/cyan] — Video codec starts with avc1 (h264)
• [cyan][acodec^=mp3][/cyan] — Audio codec is mp3
• [cyan][tbr>=128][/cyan] — Total bitrate at least 128 kbps
• [cyan][fps>=60][/cyan] — 60fps or higher

[yellow]Sorting (-S)[/yellow]
Sort by preference when multiple formats match:
• [cyan]-S "res:1080,fps,codec:h264"[/cyan] — Prefer 1080p, then fps, then h264
• [cyan]-S "quality,br,res,fps"[/cyan] — Sort by quality, bitrate, resolution, fps

[yellow]Built-in Presets (-t)[/yellow]
• [cyan]-t mp3[/cyan] — Extract to MP3 (uses: -f 'ba[acodec^=mp3]/ba/b' -x --audio-format mp3)
• [cyan]-t aac[/cyan] — Extract to AAC
• [cyan]-t mp4[/cyan] — MP4 with h264 preference
• [cyan]-t mkv[/cyan] — MKV container
• [cyan]-t sleep[/cyan] — Polite mode with delays
""",
    },
    {
        "title": "§3 Output Template Variables",
        "content": """
[yellow]Basic Variables[/yellow]
• [cyan]%(id)s[/cyan] — Video ID
• [cyan]%(title)s[/cyan] — Video title
• [cyan]%(fulltitle)s[/cyan] — Full title without truncation
• [cyan]%(ext)s[/cyan] — File extension
• [cyan]%(url)s[/cyan] — Video URL

[yellow]Uploader/Channel Info[/yellow]
• [cyan]%(uploader)s[/cyan] — Uploader name
• [cyan]%(channel)s[/cyan] — Channel name
• [cyan]%(channel_id)s[/cyan] — Channel ID
• [cyan]%(uploader_id)s[/cyan] — Uploader ID
• [cyan]%(uploader_url)s[/cyan] — Uploader profile URL

[yellow]Date/Time[/yellow]
• [cyan]%(upload_date)s[/cyan] — Upload date as YYYYMMDD
• [cyan]%(upload_date>%Y-%m-%d)s[/cyan] — Formatted: 2024-01-15
• [cyan]%(timestamp)s[/cyan] — Unix timestamp
• [cyan]%(release_date)s[/cyan] — Release date
• [cyan]%(release_year)s[/cyan] — Release year

[yellow]Media Info[/yellow]
• [cyan]%(duration)s[/cyan] — Duration in seconds
• [cyan]%(duration_string)s[/cyan] — Human-readable: HH:MM:SS
• [cyan]%(view_count)d[/cyan] — View count (integer)
• [cyan]%(like_count)d[/cyan] — Like count
• [cyan]%(width)d[/cyan] — Video width
• [cyan]%(height)d[/cyan] — Video height
• [cyan]%(resolution)s[/cyan] — Resolution string

[yellow]Playlist Variables[/yellow]
• [cyan]%(playlist_title)s[/cyan] — Playlist name
• [cyan]%(playlist_index)d[/cyan] — Position in playlist (1-based)
• [cyan]%(playlist_index)03d[/cyan] — Zero-padded: 001, 002...
• [cyan]%(playlist_index+10)03d[/cyan] — Arithmetic: 011, 012...
• [cyan]%(playlist_id)s[/cyan] — Playlist ID
• [cyan]%(playlist_count)d[/cyan] — Total videos in playlist

[yellow]Fallback Syntax[/yellow]
• [cyan]%(uploader|Unknown)s[/cyan] — Use "Unknown" if uploader is missing

[yellow]Examples[/yellow]
• [cyan]%(uploader)s/%(title)s.%(ext)s[/cyan]
• [cyan]%(upload_date>%Y-%m-%d)s %(title)s.%(ext)s[/cyan]
• [cyan]%(playlist_title)s/%(playlist_index)03d %(title)s.%(ext)s[/cyan]
• [cyan]%(channel)s/%(upload_date>%Y)s/%(title)s.%(ext)s[/cyan]
""",
    },
    {
        "title": "§4 aria2c Integration",
        "content": """
[yellow]Why Use aria2c?[/yellow]
aria2c is a multi-protocol, multi-source downloader that can significantly
increase download speeds by using multiple connections per file.

[yellow]How yt-dlp Invokes aria2c[/yellow]
[cyan]--downloader aria2c[/cyan] tells yt-dlp to use aria2c instead of native downloader.

[yellow]Passing Arguments[/yellow]
[cyan]--downloader-args "aria2c:-x 16 -s 16 -k 1M --continue"[/cyan]

[yellow]Key aria2c Options[/yellow]
• [cyan]-x N[/cyan] — Max connections per server (default: 1, recommended: 16)
• [cyan]-s N[/cyan] — Split file into N segments (default: 1, recommended: 16)
• [cyan]-k SIZE[/cyan] — Min segment size (default: 1M, e.g., 1M, 256K)
• [cyan]-j N[/cyan] — Max parallel downloads (default: 5)
• [cyan]--continue[/cyan] — Resume partial downloads

[yellow]When NOT to Use aria2c[/yellow]
aria2c does NOT work with DASH or HLS streams (YouTube uses DASH).
For these, use native downloader:

[cyan]--downloader aria2c --downloader "dash,m3u8:native"[/cyan]

This tells yt-dlp to use aria2c for regular downloads but native
downloader for DASH and m3u8 (HLS) streams.

[yellow]Recommended Settings[/yellow]
For best results with compatible streams:
• -x 16 (16 connections per server)
• -s 16 (split into 16 parts)
• -k 1M (min 1MB per segment)
• -j 5 (max 5 concurrent downloads)
""",
    },
    {
        "title": "§5 FFmpeg Post-Processing Recipes",
        "content": """
[yellow]Remux Without Re-encoding[/yellow]
Change container without re-encoding (fast, lossless):
[cyan]--remux-video mp4[/cyan]
Supported: mp4, mkv, webm, mov, avi, flv

[yellow]Re-encode Video[/yellow]
Actually re-encode video (slower, may lose quality):
[cyan]--recode-video mp4[/cyan]

[yellow]Extract Audio[/yellow]
MP3 at 320kbps:
[cyan]-x --audio-format mp3 --audio-quality 320K[/cyan]

FLAC lossless:
[cyan]-x --audio-format flac[/cyan]

M4A (AAC):
[cyan]-x --audio-format m4a[/cyan]

Audio quality values: 0 (best) to 10 (worst), or bitrate like 192K, 320K

[yellow]Embed Thumbnail[/yellow]
[cyan]--embed-thumbnail[/cyan]
Uses mutagen (audio) or AtomicParsley (MP4)

[yellow]Embed Subtitles[/yellow]
[cyan]--embed-subs[/cyan]
Works with: mp4, webm, mkv only

[yellow]Split by Chapters[/yellow]
[cyan]--split-chapters[/cyan]
Creates separate files for each chapter

[yellow]Custom FFmpeg Arguments[/yellow]
[cyan]--postprocessor-args "ffmpeg:-vf scale=1280:720"[/cyan]

[yellow]Named Post-processors[/yellow]
• Merger — Merge video+audio streams
• ModifyChapters — Edit chapter markers
• SplitChapters — Split video by chapters
• ExtractAudio — Extract audio track
• VideoRemuxer — Change container
• VideoConvertor — Re-encode video
• Metadata — Add metadata tags
• EmbedSubtitle — Embed subtitles
• EmbedThumbnail — Embed thumbnail image
""",
    },
    {
        "title": "§6 SponsorBlock",
        "content": """
[yellow]What is SponsorBlock?[/yellow]
SponsorBlock automatically skips sponsored segments, intros, outros,
and other annoying parts in YouTube videos.

[yellow]Available Categories[/yellow]
• [cyan]sponsor[/cyan] — Paid promotion within the video
• [cyan]intro[/cyan] — Intro animation/jingle
• [cyan]outro[/cyan] — Outro/end screen
• [cyan]selfpromo[/cyan] — Self-promotion (merch, Patreon)
• [cyan]preview[/cyan] — Preview/recap of content
• [cyan]filler[/cyan] — Filler content not related to main topic
• [cyan]interaction[/cyan] — Reminder to like/subscribe
• [cyan]music_offtopic[/cyan] — Off-topic music segments
• [cyan]hook[/cyan] — Hook at the beginning
• [cyan]poi_highlight[/cyan] — Point of interest highlight
• [cyan]chapter[/cyan] — Chapter markers

[yellow]Mark Segments (Create Chapters)[/yellow]
[cyan]--sponsorblock-mark all,-preview[/cyan]
Marks all categories except preview as chapters.

[yellow]Remove Segments (Cut Out)[/yellow]
[cyan]--sponsorblock-remove sponsor,intro,outro[/cyan]
Physically removes these segments from the video.

[yellow]Shortcuts[/yellow]
• [cyan]all[/cyan] — All categories
• [cyan]default[/cyan] (for remove) — All except filler: [cyan]all,-filler[/cyan]

[yellow]Custom API URL[/yellow]
[cyan]--sponsorblock-api https://sponsor.ajay.app[/cyan]

[yellow]Example: Clean 1080p Download[/yellow]
[cyan]-f "bestvideo[height<=1080]+bestaudio" --sponsorblock-remove all,-filler[/cyan]
""",
    },
    {
        "title": "§7 Subtitles and Metadata",
        "content": """
[yellow]Fetch Manual Subtitles[/yellow]
[cyan]--write-subs --sub-langs "en,ja" --sub-format srt[/cyan]

[yellow]Fetch Auto-Generated Subtitles[/yellow]
[cyan]--write-auto-subs[/cyan]

[yellow]Subtitle Language Codes[/yellow]
• [cyan]en[/cyan] — English only
• [cyan]en.*[/cyan] — All English variants
• [cyan]ja[/cyan] — Japanese
• [cyan]all[/cyan] — All available languages
• [cyan]en,ja,zh-Hans[/cyan] — Multiple specific languages

[yellow]Subtitle Formats[/yellow]
• [cyan]srt[/cyan] — SubRip (most compatible)
• [cyan]ass[/cyan] — Advanced SubStation Alpha (styled)
• [cyan]vtt[/cyan] — WebVTT
• [cyan]lrc[/cyan] — Lyrics format
• [cyan]best[/cyan] — Best available format

[yellow]Embed Subtitles[/yellow]
[cyan]--embed-subs[/cyan]
Only works with mp4, webm, mkv containers

[yellow]Convert Subtitle Format[/yellow]
[cyan]--convert-subs srt[/cyan]

[yellow]Embed All Metadata[/yellow]
[cyan]--embed-metadata[/cyan] (alias: [cyan]--add-metadata[/cyan])

[yellow]Write Info JSON[/yellow]
[cyan]--write-info-json[/cyan]
Creates a .info.json sidecar file with all video metadata

[yellow]Embed Chapters[/yellow]
[cyan]--embed-chapters[/cyan]
Adds chapter markers to the output file
""",
    },
    {
        "title": "§8 Authentication and Cookies",
        "content": """
[yellow]Cookies File (Netscape Format)[/yellow]
[cyan]--cookies cookies.txt[/cyan]

Export cookies from browser using an extension like:
• Get cookies.txt (Chrome/Firefox extension)
• cookies.txt (Firefox extension)

[yellow]Load Cookies from Browser[/yellow]
[cyan]--cookies-from-browser chrome[/cyan]

Supported browsers:
• brave, chrome, chromium, edge, firefox, opera, safari, vivaldi, whale

With profile:
[cyan]--cookies-from-browser chrome:Profile1[/cyan]

[yellow]Netrc File[/yellow]
[cyan]--netrc[/cyan]
Uses ~/.netrc file for credentials (per-extractor storage)

Format: machine extractor-name login USERNAME password PASSWORD

[yellow]Username/Password[/yellow]
[cyan]-u USERNAME -p PASSWORD[/cyan]
(Not recommended for security reasons)

[yellow]Client Certificates[/yellow]
[cyan]--client-certificate CERTFILE[/cyan]
For sites requiring certificate authentication

[yellow]Troubleshooting YouTube 403 Errors[/yellow]
If you get "HTTP Error 403" or bot detection:
1. Try [cyan]--cookies-from-browser chrome[/cyan]
2. Or use [cyan]--impersonate chrome[/cyan]
""",
    },
    {
        "title": "§9 Geo-Restriction Workarounds",
        "content": """
[yellow]X-Forwarded-For Header[/yellow]
[cyan]--xff VALUE[/cyan]

VALUE can be:
• ISO 3166-2 country code: [cyan]US[/cyan], [cyan]GB[/cyan], [cyan]JP[/cyan]
• CIDR block: [cyan]1.2.3.4/24[/cyan]

[yellow]Proxy[/yellow]
[cyan]--proxy socks5://user:pass@127.0.0.1:1080/[/cyan]

Supported protocols: http, https, socks4, socks5

[yellow]Geo-Verification Proxy[/yellow]
[cyan]--geo-verification-proxy URL[/cyan]
Only used for geo-verification, actual download uses normal connection

[yellow]Example: Access US-Only Content[/yellow]
[cyan]--xff US --proxy socks5://localhost:1080[/cyan]
""",
    },
    {
        "title": "§10 Configuration Files",
        "content": """
[yellow]yt-dlp.conf Locations[/yellow]

[bold]Windows:[/bold]
• %APPDATA%\\yt-dlp\\config\\yt-dlp.conf
• %APPDATA%\\yt-dlp.conf
• Installation directory\\yt-dlp.conf

[bold]macOS:[/bold]
• ~/.config/yt-dlp/config
• ~/.yt-dlp.conf

[bold]Linux:[/bold]
• ~/.config/yt-dlp/config
• ~/.yt-dlp.conf
• /etc/yt-dlp.conf

[yellow]Using Custom Config Location[/yellow]
[cyan]--config-locations PATH[/cyan]
Specify custom config file path(s)

[yellow]Portable Config[/yellow]
Place [cyan]yt-dlp.conf[/cyan] next to the yt-dlp binary for portable usage.

[yellow]Config File Syntax[/yellow]
Each line is one option:
```
# Comment lines start with #
-o '%(title)s.%(ext)s'
-f bestvideo+bestaudio/best
--embed-metadata
--sponsorblock-remove all,-filler
```

[yellow]Multiple Config Files[/yellow]
You can specify multiple config files; later ones override earlier:
[cyan]--config-locations global.conf,user.conf[/cyan]
""",
    },
    {
        "title": "§11 Keyboard Shortcuts",
        "content": """
[yellow]Navigation[/yellow]
• [cyan]Tab / Shift+Tab[/cyan] — Switch tabs forward/backward
• [cyan]1-6[/cyan] — Jump to specific tab (1=Downloader, 6=Guide)
• [cyan]↑↓[/cyan] — Navigate lists
• [cyan]/[/cyan] — Focus search/URL field

[yellow]Download Actions[/yellow]
• [cyan]Enter[/cyan] — Start download / confirm action
• [cyan]Space[/cyan] — Pause/resume selected queue item
• [cyan]D[/cyan] — Cancel and delete selected download
• [cyan]R[/cyan] — Retry failed download
• [cyan]C[/cyan] — Copy command to clipboard
• [cyan]O[/cyan] — Open download folder

[yellow]App Controls[/yellow]
• [cyan]S[/cyan] — Open settings tab
• [cyan]F1[/cyan] — Toggle Guide tab
• [cyan]Q[/cyan] — Quit application
• [cyan]Ctrl+Q[/cyan] — Quit application (alternative)
""",
    },
    {
        "title": "§12 Troubleshooting",
        "content": """
[yellow]"yt-dlp warns about outdated version"[/yellow]
→ Run with [cyan]--update-to nightly[/cyan] or update manually

[yellow]"Requested format is not available"[/yellow]
→ Check available formats with [cyan]-F[/cyan] flag
→ The video may not have your requested quality
→ Try a different format selector

[yellow]"ffmpeg merge fails"[/yellow]
→ Verify [cyan]--ffmpeg-location[/cyan] points to correct directory
→ Ensure both ffmpeg AND ffprobe are present
→ Check that ffmpeg is not blocked by antivirus

[yellow]"aria2c errors on YouTube"[/yellow]
→ YouTube uses DASH which aria2c doesn't support
→ Use: [cyan]--downloader aria2c --downloader "dash,m3u8:native"[/cyan]

[yellow]"HTTP Error 403" or bot detection[/yellow]
→ Use [cyan]--cookies-from-browser chrome[/cyan]
→ Or try [cyan]--impersonate chrome[/cyan]
→ Update yt-dlp to latest version

[yellow]"Subtitle embed fails"[/yellow]
→ Only works with mp4, webm, mkv containers
→ Remux to compatible format first: [cyan]--remux-video mkv[/cyan]

[yellow]"Rate limiting / Too many requests"[/yellow]
→ Use [cyan]-t sleep[/cyan] preset
→ Or set [cyan]--sleep-interval 10 --max-sleep-interval 20[/cyan]
→ Add [cyan]--sleep-requests 0.75[/cyan]

[yellow]"Certificate verification failed"[/yellow]
→ Update certifi package: [cyan]pip install --upgrade certifi[/cyan]
→ Or temporarily use [cyan]--no-check-certificates[/cyan]

[yellow]"Download archive not working"[/yellow]
→ Ensure path is writable
→ Archive file is created automatically if it doesn't exist
→ Check permissions on ./data/archive.txt

[yellow]"Queue not persisting"[/yellow]
→ Check that ./data/ directory exists and is writable
→ Queue saves to ./data/queue.json

[yellow]"Template not loading"[/yellow]
→ Verify JSON syntax is valid
→ Check template is in ./templates/ directory
→ Filename must end with .json
""",
    },
]


def get_guide_sections():
    """Return all guide sections."""
    return GUIDE_SECTIONS


def get_section_by_title(title: str):
    """Get a specific section by title."""
    for section in GUIDE_SECTIONS:
        if section["title"] == title:
            return section
    return None
