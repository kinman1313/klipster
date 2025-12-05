from pytube import YouTube
import os
from moviepy.video.io.VideoFileClip import VideoFileClip

def download_video(url):
    yt = YouTube(url)
    stream = yt.streams.filter(progressive=True, file_extension='mp4').first()
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    video_path = stream.download(output_path='downloads')
    return video_path

import openai

def transcribe_video(video_path):
    """
    Transcribe video using Whisper and return both full text and timestamped segments.
    Returns a dict with 'text' (full transcription) and 'segments' (timestamped segments).
    """
    with open(video_path, "rb") as audio_file:
        transcript = openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json",
            timestamp_granularities=["segment"]
        )

    # Return both full text and segments with timestamps
    return {
        'text': transcript.text,
        'segments': transcript.segments if hasattr(transcript, 'segments') else []
    }

from moviepy.video.VideoClip import TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
# Import effects using the correct moviepy structure
try:
    # Try newer moviepy import style first
    from moviepy.video.fx.fadein import fadein
    from moviepy.video.fx.fadeout import fadeout
    from moviepy.video.fx.speedx import speedx
except ImportError:
    # Fallback to older import style
    try:
        from moviepy.video.fx import fadein, fadeout, speedx
    except ImportError:
        # If still failing, import as module
        import moviepy.video.fx.all as vfx
        fadein = vfx.fadein
        fadeout = vfx.fadeout
        speedx = vfx.speedx
from scenedetect import open_video, SceneManager
from scenedetect.detectors import ContentDetector

import json

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

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
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
                clip = clip.fx(speedx, speed_factor)
            elif effect_name == 'fadein':
                duration = float(effect_value)
                clip = clip.fx(fadein, duration)
            elif effect_name == 'fadeout':
                duration = float(effect_value)
                clip = clip.fx(fadeout, duration)
        except (ValueError, TypeError) as e:
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
