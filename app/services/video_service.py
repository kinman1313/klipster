from pytube import YouTube
import os
from moviepy.video.io.VideoFileClip import VideoFileClip
import speech_recognition as sr

def download_video(url):
    yt = YouTube(url)
    stream = yt.streams.filter(progressive=True, file_extension='mp4').first()
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    video_path = stream.download(output_path='downloads')
    return video_path

def transcribe_video(video_path):
    r = sr.Recognizer()
    with sr.AudioFile(video_path) as source:
        audio = r.record(source)
    return r.recognize_google(audio)

from moviepy.video.VideoClip import TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip

def generate_clips(video_path, transcription, subtitle_color='white', emojis=None, effects=None):
    video_clip = VideoFileClip(video_path)

    # Simple logic to find a key part
    start_time = 5
    end_time = 15

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

    clip_path = os.path.join('clips', f"clip_{os.path.basename(video_path)}")
    final_clip.write_videofile(clip_path, codec='libx264')
    return clip_path
