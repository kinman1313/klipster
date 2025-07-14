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
from scenedetect import open_video, SceneManager
from scenedetect.detectors import ContentDetector

def find_scenes(video_path, threshold=30.0):
    video = open_video(video_path)
    scene_manager = SceneManager()
    scene_manager.add_detector(ContentDetector(threshold=threshold))
    scene_manager.detect_scenes(video=video)
    return scene_manager.get_scene_list()

def generate_clips(video_path, transcription, subtitle_color='white', emojis=None, effects=None):
    scene_list = find_scenes(video_path)
    video_clip = VideoFileClip(video_path)
    clip_paths = []

    for i, scene in enumerate(scene_list):
        start_time, end_time = scene[0].get_seconds(), scene[1].get_seconds()

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
