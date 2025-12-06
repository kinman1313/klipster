from flask import Flask, request, jsonify, render_template
from app.services.video_service import download_video, generate_clips, transcribe_video
from app.services.scheduler_service import schedule_upload
from app.models import db, User, Clip
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os

import openai

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your_secret_key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
    app.config['OPENAI_API_KEY'] = os.getenv("OPENAI_API_KEY")
    openai.api_key = app.config['OPENAI_API_KEY']
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    def upload_task(clip_paths, caption):
        # Placeholder for social media upload logic
        from app.services.social_media_service import upload_to_instagram
        # For now, we'll just upload the first clip
        upload_to_instagram(current_user.username, current_user.password, clip_paths[0], caption)

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        # Placeholder for login logic
        return "Login Page"

    @app.route('/signup', methods=['GET', 'POST'])
    def signup():
        # Placeholder for signup logic
        return "Signup Page"

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return "Logged out"

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
            transcription_data = transcribe_video(video_path)
            clip_paths = generate_clips(video_path, transcription_data, subtitle_color, emojis, effects)

            # Extract full text for storage in database
            full_transcription = transcription_data.get('text', '')

            # Save to database only if user is logged in
            if current_user.is_authenticated:
                for clip_path in clip_paths:
                    new_clip = Clip(user_id=current_user.id, clip_path=clip_path, transcription=full_transcription, subtitle_color=subtitle_color, emojis=emojis, effects=effects)
                    db.session.add(new_clip)
                db.session.commit()

            if schedule_interval and schedule_unit:
                schedule_upload(lambda: upload_task(clip_paths), schedule_interval, schedule_unit)
                return jsonify({
                    'message': 'Clip generation and scheduling successful',
                    'paths': clip_paths,
                    'transcription': full_transcription,
                    'clips_generated': len(clip_paths)
                })

            return jsonify({
                'message': 'Clip generated successfully',
                'paths': clip_paths,
                'transcription': full_transcription,
                'clips_generated': len(clip_paths)
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    with app.app_context():
        db.create_all()

    return app
