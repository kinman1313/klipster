import os
from moviepy.video.io.VideoFileClip import VideoFileClip

def get_youtube_captions(url):
    """
    Try to fetch YouTube captions/subtitles (instant, no download needed).

    Returns:
        dict: {'text': full_text, 'segments': [{'start': float, 'end': float, 'text': str}]}
        or None if no captions available
    """
    try:
        import yt_dlp

        ydl_opts = {
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['en'],
            'quiet': True,
            'no_warnings': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            # Check for captions
            subtitles = info.get('subtitles', {})
            automatic_captions = info.get('automatic_captions', {})

            # Prefer manual subtitles, fall back to auto-generated
            captions_data = subtitles.get('en') or automatic_captions.get('en')

            if not captions_data:
                return None

            # Find JSON format captions (has timestamps)
            json_caption = None
            for caption in captions_data:
                if caption.get('ext') == 'json3':
                    json_caption = caption
                    break

            if not json_caption:
                return None

            # Download and parse the captions
            import urllib.request
            import json

            with urllib.request.urlopen(json_caption['url']) as response:
                caption_data = json.loads(response.read().decode('utf-8'))

            # Parse caption segments
            segments = []
            full_text_parts = []

            for event in caption_data.get('events', []):
                if 'segs' not in event:
                    continue

                start_time = event.get('tStartMs', 0) / 1000.0  # Convert to seconds
                duration = event.get('dDurationMs', 0) / 1000.0
                end_time = start_time + duration

                # Combine all text segments in this event
                text_parts = [seg.get('utf8', '') for seg in event.get('segs', [])]
                text = ''.join(text_parts).strip()

                if text:
                    segments.append({
                        'start': start_time,
                        'end': end_time,
                        'text': text
                    })
                    full_text_parts.append(text)

            print(f"✅ Found YouTube captions! {len(segments)} segments")
            return {
                'text': ' '.join(full_text_parts),
                'segments': segments
            }

    except Exception as e:
        print(f"Could not fetch captions: {e}")
        return None

def download_audio_only(url):
    """
    Download only the audio track from YouTube (much faster and smaller than full video).

    Returns:
        str: Path to the downloaded audio file
    """
    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    try:
        import yt_dlp

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'downloads/%(title)s_audio.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '64',
            }],
            'quiet': True,
            'no_warnings': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # yt-dlp changes extension to mp3 after conversion
            base_path = ydl.prepare_filename(info)
            audio_path = base_path.rsplit('.', 1)[0] + '.mp3'
            print(f"✅ Downloaded audio only: {os.path.basename(audio_path)}")
            return audio_path

    except ImportError:
        # Fallback: download full video and extract audio
        print("yt-dlp not available, downloading full video...")
        return None

def download_video(url):
    """Download full video from YouTube using yt-dlp (more reliable than pytube)."""
    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    try:
        # Try yt-dlp first (more reliable)
        import yt_dlp

        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_path = ydl.prepare_filename(info)
            print(f"✅ Downloaded video: {os.path.basename(video_path)}")
            return video_path

    except ImportError:
        # Fallback to pytube if yt-dlp not installed
        from pytube import YouTube
        yt = YouTube(url)
        stream = yt.streams.filter(progressive=True, file_extension='mp4').first()
        video_path = stream.download(output_path='downloads')
        return video_path

import openai

def get_transcription_optimized(url):
    """
    OPTIMIZED: Get transcription using the fastest available method.

    Workflow:
    1. Try YouTube captions first (instant, free!)
    2. If no captions: Download audio only (much smaller/faster)
    3. Transcribe audio with Whisper
    4. Return transcription data

    Returns:
        dict: {'text': full_text, 'segments': timestamped_segments, 'method': str}
    """
    print("🔍 Trying to fetch YouTube captions...")

    # Step 1: Try captions first (instant!)
    captions = get_youtube_captions(url)
    if captions:
        print("⚡ Using YouTube captions (instant, no transcription needed!)")
        captions['method'] = 'youtube_captions'
        return captions

    print("⚠️  No captions available, downloading audio...")

    # Step 2: Download audio only (much faster than full video)
    audio_path = download_audio_only(url)

    if not audio_path:
        # Fallback: download full video
        print("⚠️  Downloading full video as fallback...")
        video_path = download_video(url)
        audio_path = video_path

    # Step 3: Transcribe audio with Whisper
    print("🎤 Transcribing audio with Whisper...")
    transcription = transcribe_audio_file(audio_path)
    transcription['method'] = 'whisper_transcription'

    # Clean up audio file if it was audio-only download
    if audio_path.endswith('_audio.mp3') and os.path.exists(audio_path):
        os.remove(audio_path)
        print(f"🧹 Cleaned up temporary audio file")

    return transcription

def transcribe_audio_file(audio_path):
    """
    Transcribe an audio or video file using Whisper.
    Handles compression if file is too large.

    Returns:
        dict: {'text': full_text, 'segments': timestamped_segments}
    """
    # Check if we need to extract/compress audio from video
    is_video = audio_path.endswith('.mp4') or audio_path.endswith('.mkv') or audio_path.endswith('.avi')

    if is_video:
        # Extract audio from video
        temp_audio_path = audio_path.rsplit('.', 1)[0] + '_audio.mp3'
        video = VideoFileClip(audio_path)
        video.audio.write_audiofile(temp_audio_path, codec='mp3', bitrate='64k', logger=None)
        video.close()
        audio_to_transcribe = temp_audio_path
    else:
        audio_to_transcribe = audio_path
        temp_audio_path = None

    try:
        # Check file size (Whisper has 25MB limit)
        audio_size_mb = os.path.getsize(audio_to_transcribe) / (1024 * 1024)
        print(f"📊 Audio file size: {audio_size_mb:.2f} MB")

        if audio_size_mb > 24:
            # Re-encode with lower bitrate if too large
            print("⚠️  Audio too large, re-encoding with lower bitrate...")
            compressed_path = audio_to_transcribe.replace('.mp3', '_compressed.mp3')

            if is_video:
                video = VideoFileClip(audio_path)
                video.audio.write_audiofile(compressed_path, codec='mp3', bitrate='32k', logger=None)
                video.close()
            else:
                # Use ffmpeg to compress existing audio
                import subprocess
                subprocess.run(['ffmpeg', '-i', audio_to_transcribe, '-b:a', '32k', compressed_path, '-y'],
                             capture_output=True)

            if temp_audio_path and os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
            audio_to_transcribe = compressed_path
            temp_audio_path = compressed_path

        # Transcribe using Whisper
        with open(audio_to_transcribe, "rb") as audio_file:
            transcript = openai.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["segment"]
            )

        # Clean up temporary audio file
        if temp_audio_path and os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)

        # Return both full text and segments with timestamps
        return {
            'text': transcript.text,
            'segments': transcript.segments if hasattr(transcript, 'segments') else []
        }

    except Exception as e:
        # Clean up on error
        if temp_audio_path and os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
        raise e

def transcribe_video(video_path):
    """
    Transcribe video using Whisper and return both full text and timestamped segments.
    Returns a dict with 'text' (full transcription) and 'segments' (timestamped segments).

    Extracts audio from video and compresses if needed to stay under Whisper's 25MB limit.
    """
    # Extract audio from video to a temporary file
    audio_path = video_path.rsplit('.', 1)[0] + '_audio.mp3'

    try:
        # Use moviepy to extract audio
        video = VideoFileClip(video_path)
        video.audio.write_audiofile(audio_path, codec='mp3', bitrate='64k', logger=None)
        video.close()

        # Check file size (Whisper has 25MB limit)
        audio_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
        print(f"Audio file size: {audio_size_mb:.2f} MB")

        if audio_size_mb > 24:
            # Re-encode with lower bitrate if too large
            print("Audio too large, re-encoding with lower bitrate...")
            temp_path = audio_path.replace('.mp3', '_temp.mp3')
            os.rename(audio_path, temp_path)

            video = VideoFileClip(video_path)
            video.audio.write_audiofile(audio_path, codec='mp3', bitrate='32k', logger=None)
            video.close()
            os.remove(temp_path)

        # Transcribe using Whisper
        with open(audio_path, "rb") as audio_file:
            transcript = openai.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["segment"]
            )

        # Clean up audio file
        if os.path.exists(audio_path):
            os.remove(audio_path)

        # Return both full text and segments with timestamps
        return {
            'text': transcript.text,
            'segments': transcript.segments if hasattr(transcript, 'segments') else []
        }

    except Exception as e:
        # Clean up on error
        if os.path.exists(audio_path):
            os.remove(audio_path)
        raise e

from moviepy.video.VideoClip import TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from scenedetect import open_video, SceneManager
from scenedetect.detectors import ContentDetector

import json

# Import moviepy effects - handle different versions
def get_moviepy_effects():
    """Get moviepy effect functions compatible with installed version."""
    try:
        # Try moviepy 1.0.3+ style
        from moviepy.video.fx.fadein import fadein
        from moviepy.video.fx.fadeout import fadeout
        from moviepy.video.fx.speedx import speedx
        return fadein, fadeout, speedx
    except (ImportError, ModuleNotFoundError):
        try:
            # Try older import style
            from moviepy.video.fx import fadein, fadeout, speedx
            return fadein, fadeout, speedx
        except (ImportError, AttributeError):
            try:
                # Try vfx module style
                import moviepy.video.fx.all as vfx
                return vfx.fadein, vfx.fadeout, vfx.speedx
            except (ImportError, ModuleNotFoundError, AttributeError):
                # Last resort: return None and we'll handle effects manually
                return None, None, None

fadein, fadeout, speedx = get_moviepy_effects()

def find_key_moments(transcription_data):
    """
    Analyze timestamped transcription segments and identify key moments for clips.

    Args:
        transcription_data: Dict with 'text' (full transcription) and 'segments' (timestamped segments)

    Returns:
        Dict with 'moments' list, each containing start_time, end_time, and text
    """
    segments = transcription_data.get('segments', [])
    full_text = transcription_data.get('text', '')

    # Build a transcript with timestamps for GPT to analyze
    timestamped_transcript = "\n".join([
        f"[{seg.get('start', 0):.1f}s - {seg.get('end', 0):.1f}s]: {seg.get('text', '')}"
        for seg in segments
    ])

    # Check if transcript is too long (estimate ~4 chars per token)
    estimated_tokens = len(timestamped_transcript) / 4

    # If too long for GPT-3.5-turbo (16k limit), use GPT-4o (128k limit)
    if estimated_tokens > 12000:  # Leave room for system prompt and response
        print(f"⚠️  Long transcript ({estimated_tokens:.0f} tokens), using GPT-4o for larger context")
        model = "gpt-4o"
    else:
        model = "gpt-3.5-turbo"

    # If still too long even for GPT-4, sample segments
    if estimated_tokens > 100000:
        print(f"⚠️  Very long transcript, sampling every 3rd segment...")
        sampled_segments = segments[::3]  # Take every 3rd segment
        timestamped_transcript = "\n".join([
            f"[{seg.get('start', 0):.1f}s - {seg.get('end', 0):.1f}s]: {seg.get('text', '')}"
            for seg in sampled_segments
        ])
        print(f"📊 Reduced from {len(segments)} to {len(sampled_segments)} segments")

    system_prompt = """You are an expert video editor that identifies engaging, interesting moments from video transcriptions for social media clips.

REQUIREMENTS:
- Each clip MUST be between 30 seconds and 2 minutes (120 seconds) long
- Identify moments that are self-contained, interesting, funny, insightful, or have viral potential
- Use the actual timestamps provided in the transcription
- Aim for 3-5 key moments from the video
- Each moment should have clear start and end times

Respond ONLY with valid JSON in this exact format:
{
  "moments": [
    {
      "start_time": 10.5,
      "end_time": 45.2,
      "text": "Brief description of what makes this moment interesting"
    }
  ]
}"""

    user_prompt = f"""Analyze this timestamped transcription and identify 3-5 key moments suitable for social media clips.

Timestamped Transcription:
{timestamped_transcript}

Remember: Each clip must be 30-120 seconds long. Use the exact timestamps from the transcription."""

    # Try the selected model, with fallbacks
    models_to_try = []
    if model == "gpt-4o":
        models_to_try = ["gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]
    else:
        models_to_try = ["gpt-3.5-turbo"]

    last_error = None
    for attempt_model in models_to_try:
        try:
            print(f"🤖 Trying model: {attempt_model}")
            response = openai.chat.completions.create(
                model=attempt_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )

            print(f"✅ Successfully used model: {attempt_model}")
            return json.loads(response.choices[0].message.content)

        except Exception as e:
            error_str = str(e)
            if "model_not_found" in error_str or "does not exist" in error_str:
                print(f"⚠️  Model {attempt_model} not available, trying next...")
                last_error = e
                continue
            elif "context_length_exceeded" in error_str:
                print(f"⚠️  Context too long for {attempt_model}, trying next...")
                last_error = e
                continue
            else:
                # Other error, raise it
                raise e

    # If we get here, all models failed - try chunking approach
    print("⚠️  All models failed, using chunked approach with first 30% of video...")
    reduced_segments = segments[:len(segments)//3]
    timestamped_transcript = "\n".join([
        f"[{seg.get('start', 0):.1f}s - {seg.get('end', 0):.1f}s]: {seg.get('text', '')}"
        for seg in reduced_segments
    ])

    user_prompt_chunked = f"""Analyze this timestamped transcription and identify 3-5 key moments suitable for social media clips.

Timestamped Transcription:
{timestamped_transcript}

Remember: Each clip must be 30-120 seconds long. Use the exact timestamps from the transcription."""

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt_chunked}
        ],
        response_format={"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)

def apply_effects(clip, effects_str):
    """
    Apply video effects based on a comma-separated string of effect specifications.

    Supported effects:
    - speed:X (e.g., "speed:1.5" for 1.5x speed, "speed:0.5" for slow motion)
    - fadein:X (e.g., "fadein:1" for 1 second fade in)
    - fadeout:X (e.g., "fadeout:1" for 1 second fade out)

    Example: "speed:1.5,fadein:0.5,fadeout:0.5"
    """
    if not effects_str:
        return clip

    effects_list = [e.strip() for e in effects_str.split(',')]

    for effect in effects_list:
        if ':' not in effect:
            continue

        effect_name, effect_value = effect.split(':', 1)
        effect_name = effect_name.strip().lower()

        try:
            if effect_name == 'speed':
                speed_factor = float(effect_value)
                if speedx is not None:
                    clip = clip.fx(speedx, speed_factor)
                else:
                    # Manual speed effect if import failed
                    clip = clip.speedx(speed_factor)
            elif effect_name == 'fadein':
                duration = float(effect_value)
                if fadein is not None:
                    clip = clip.fx(fadein, duration)
                else:
                    # Manual fadein if import failed
                    clip = clip.fadein(duration)
            elif effect_name == 'fadeout':
                duration = float(effect_value)
                if fadeout is not None:
                    clip = clip.fx(fadeout, duration)
                else:
                    # Manual fadeout if import failed
                    clip = clip.fadeout(duration)
        except (ValueError, TypeError, AttributeError) as e:
            print(f"Warning: Could not apply effect '{effect}': {e}")
            continue

    return clip

def generate_clips(video_path, transcription_data, subtitle_color='white', emojis=None, effects=None):
    """
    Generate video clips from key moments identified in the transcription.

    Args:
        video_path: Path to the source video file
        transcription_data: Dict with 'text' and 'segments' from transcribe_video()
        subtitle_color: Color for subtitle text (default: white)
        emojis: Optional emoji string to prepend to subtitles
        effects: Optional effects string (e.g., "speed:1.5,fadein:0.5")

    Returns:
        List of paths to generated clip files
    """
    key_moments = find_key_moments(transcription_data)
    video_clip = VideoFileClip(video_path)
    clip_paths = []
    segments = transcription_data.get('segments', [])

    for i, moment in enumerate(key_moments['moments']):
        start_time = moment['start_time']
        end_time = moment['end_time']
        clip_duration = end_time - start_time

        # Validate clip duration (30 seconds to 2 minutes)
        if clip_duration < 30:
            print(f"Skipping clip {i}: too short ({clip_duration:.1f}s < 30s)")
            continue
        if clip_duration > 120:
            print(f"Skipping clip {i}: too long ({clip_duration:.1f}s > 120s)")
            continue

        # Extract segment-specific text for this clip
        segment_text = get_text_for_timerange(segments, start_time, end_time)

        # Create subtitle text for this specific segment
        subtitle_text = segment_text
        if emojis:
            subtitle_text = f"{emojis} {subtitle_text}"

        # Create a text clip for subtitles
        subtitle = TextClip(subtitle_text, fontsize=24, color=subtitle_color, bg_color='black')
        subtitle = subtitle.set_pos(('center', 'bottom')).set_duration(clip_duration)

        # Create the subclip
        clip_segment = video_clip.subclip(start_time, end_time)

        # Apply effects if specified
        if effects:
            clip_segment = apply_effects(clip_segment, effects)

        # Composite the video and subtitle
        final_clip = CompositeVideoClip([clip_segment, subtitle])

        if not os.path.exists('clips'):
            os.makedirs('clips')

        clip_path = os.path.join('clips', f"clip_{i}_{os.path.basename(video_path)}")
        final_clip.write_videofile(clip_path, codec='libx264')
        clip_paths.append(clip_path)

    return clip_paths

def get_text_for_timerange(segments, start_time, end_time):
    """
    Extract text from segments that fall within the specified time range.

    Args:
        segments: List of timestamped segments from Whisper
        start_time: Start time in seconds
        end_time: End time in seconds

    Returns:
        Concatenated text from segments in the time range
    """
    relevant_texts = []

    for seg in segments:
        seg_start = seg.get('start', 0)
        seg_end = seg.get('end', 0)

        # Include segments that overlap with our time range
        if seg_end >= start_time and seg_start <= end_time:
            relevant_texts.append(seg.get('text', '').strip())

    return ' '.join(relevant_texts)
