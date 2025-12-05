# Klipster - AI Video Clipper

Automatically generate engaging 30 second to 2 minute social media clips from YouTube videos using AI.

> 🪟 **Windows Users:** See the detailed [Windows Setup Guide](WINDOWS_SETUP.md) for step-by-step instructions!

## Features

- 🎬 Download videos from YouTube
- 🗣️ AI-powered transcription using OpenAI Whisper
- ✂️ Intelligent clip generation (30s-2min) using GPT
- 📝 Automatic subtitles with customizable colors
- ✨ Video effects (speed, fade in/out)
- 📅 Scheduled social media posting
- 📱 Instagram integration

## Prerequisites

- Python 3.8 or higher
- OpenAI API key
- FFmpeg (required by moviepy)

### Install FFmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd klipster
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Environment Variables

Create a `.env` file or export the following:

```bash
export OPENAI_API_KEY="your-openai-api-key-here"
```

**Or on Windows:**
```cmd
set OPENAI_API_KEY=your-openai-api-key-here
```

### 5. Initialize the Database

The database will be created automatically on first run, but you can also create it manually:

```bash
python3 -c "from app import create_app; app = create_app(); app.app_context().push(); from app.models import db; db.create_all()"
```

## Running the Application

### Start the Flask Server

```bash
python3 run.py
```

The application will be available at: **http://localhost:5000**

### Development Mode

The app runs in debug mode by default (see `run.py`). For production, modify `run.py`:

```python
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
```

## Usage

### Web Interface

1. Navigate to `http://localhost:5000`
2. Paste a YouTube URL
3. (Optional) Customize:
   - Subtitle color
   - Emojis to add
   - Effects (e.g., "speed:1.5,fadein:0.5,fadeout:0.5")
   - Schedule interval for posting
4. Click "Generate Clip"
5. Wait for processing (this may take a few minutes depending on video length)

### API Endpoint

**POST** `/api/clip`

**Request Body:**
```json
{
  "url": "https://www.youtube.com/watch?v=...",
  "subtitle_color": "#FFFFFF",
  "emojis": "🔥",
  "effects": "speed:1.5,fadein:0.5,fadeout:0.5",
  "schedule_interval": 24,
  "schedule_unit": "hours"
}
```

**Response:**
```json
{
  "message": "Clip generated successfully",
  "paths": ["clips/clip_0_video.mp4", "clips/clip_1_video.mp4"],
  "transcription": "Full video transcription...",
  "clips_generated": 2
}
```

## Video Effects

Combine multiple effects using comma-separated format:

- **speed:X** - Adjust playback speed (e.g., `speed:1.5` for 1.5x, `speed:0.5` for slow motion)
- **fadein:X** - Fade in duration in seconds (e.g., `fadein:1`)
- **fadeout:X** - Fade out duration in seconds (e.g., `fadeout:1`)

Example: `"speed:1.2,fadein:0.5,fadeout:0.5"`

## Project Structure

```
klipster/
├── app/
│   ├── __init__.py          # Flask app initialization & routes
│   ├── models.py            # Database models (User, Clip)
│   ├── services/
│   │   ├── video_service.py      # Video processing & AI logic
│   │   ├── social_media_service.py  # Instagram integration
│   │   └── scheduler_service.py     # Scheduling functionality
│   ├── templates/
│   │   └── index.html       # Web interface
│   └── static/
│       ├── script.js        # Frontend JavaScript
│       └── style.css        # Styling
├── run.py                   # Application entry point
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## How It Works

1. **Download**: Video is downloaded from YouTube using pytube
2. **Transcribe**: Audio is transcribed with timestamps using OpenAI Whisper
3. **Analyze**: GPT-3.5 analyzes the transcript to identify engaging moments
4. **Validate**: Clips are filtered to ensure 30s-2min duration
5. **Generate**: Video segments are extracted with:
   - Segment-specific subtitles
   - Custom colors and emojis
   - Applied effects
6. **Output**: Clips are saved to the `clips/` directory

## Troubleshooting

### "No module named 'moviepy'"
```bash
pip install moviepy
```

### "FFmpeg not found"
Install FFmpeg (see Prerequisites section above)

### "OpenAI API error"
- Verify your API key is set correctly
- Check your OpenAI account has credits
- Ensure you have access to Whisper and GPT-3.5-turbo

### "pytube error downloading video"
pytube can break when YouTube changes their API. If this happens:
```bash
pip install --upgrade pytube
```

### Clips are empty or corrupted
- Ensure FFmpeg is properly installed
- Check that the source video downloaded successfully to `downloads/`
- Verify disk space is available

## Notes

- First run will create a `db.sqlite` database file
- Videos are stored in `downloads/` directory
- Generated clips are stored in `clips/` directory
- The login/signup functionality is currently placeholder (not implemented)
- Instagram uploads require a valid Instagram session (see instaloader docs)

## Future Enhancements

- [ ] Implement user authentication
- [ ] Add support for more social media platforms
- [ ] Batch processing multiple videos
- [ ] Custom clip duration settings
- [ ] Advanced video editing features
- [ ] Web-based clip preview before download

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
