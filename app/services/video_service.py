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
    with open(video_path, "rb") as audio_file:
        transcript = openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json"
        )
    return transcript['text']

from moviepy.video.VideoClip import TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.fx import fadein, fadeout, speedx
from scenedetect import open_video, SceneManager
from scenedetect.detectors import ContentDetector

import json

def find_key_moments(transcription):
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that identifies key moments in a video transcription. Respond with a JSON object containing a list of key moments, each with a start_time and end_time in seconds."},
            {"role": "user", "content": f"Here is the transcription:\n\n{transcription}\n\nPlease identify the key moments."}
        ]
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

def generate_clips(video_path, transcription, subtitle_color='white', emojis=None, effects=None):
    key_moments = find_key_moments(transcription)
    video_clip = VideoFileClip(video_path)
    clip_paths = []

    for i, moment in enumerate(key_moments['moments']):
        start_time, end_time = moment['start_time'], moment['end_time']

        # Create a text clip for subtitles
        subtitle_text = transcription
        if emojis:
            subtitle_text = f"{emojis} {subtitle_text}"

        subtitle = TextClip(subtitle_text, fontsize=24, color=subtitle_color, bg_color='black')
        subtitle = subtitle.set_pos(('center', 'bottom')).set_duration(end_time - start_time)

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
