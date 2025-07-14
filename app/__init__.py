from flask import Flask, request, jsonify
from app.services.video_service import download_video, generate_clips, transcribe_video
from app.services.scheduler_service import schedule_upload
import os

def create_app():
    app = Flask(__name__)

    def upload_task(clip_path):
        # Placeholder for social media upload logic
        print(f"Uploading clip: {clip_path}")

    @app.route('/api/clip', methods=['POST'])
    def clip_video():
        data = request.get_json()
        youtube_url = data.get('url')
        subtitle_color = data.get('subtitle_color', 'white')
        emojis = data.get('emojis')
        effects = data.get('effects')
        schedule_interval = data.get('schedule_interval')
        schedule_unit = data.get('schedule_unit')

        if not youtube_url:
            return jsonify({'error': 'URL is required'}), 400

        try:
            video_path = download_video(youtube_url)
            transcription = transcribe_video(video_path)
            clip_path = generate_clips(video_path, transcription, subtitle_color, emojis, effects)

            if schedule_interval and schedule_unit:
                schedule_upload(lambda: upload_task(clip_path), schedule_interval, schedule_unit)
                return jsonify({'message': 'Clip generation and scheduling successful', 'path': clip_path, 'transcription': transcription})

            return jsonify({'message': 'Clip generated successfully', 'path': clip_path, 'transcription': transcription})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return app
