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

        # Composite the video and subtitle
        final_clip = CompositeVideoClip([video_clip.subclip(start_time, end_time), subtitle])

        if effects:
            # Placeholder for applying effects
            pass

        if not os.path.exists('clips'):
            os.makedirs('clips')

        clip_path = os.path.join('clips', f"clip_{i}_{os.path.basename(video_path)}")
        final_clip.write_videofile(clip_path, codec='libx264')
        clip_paths.append(clip_path)

    return clip_paths
