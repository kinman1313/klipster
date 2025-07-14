import instaloader

def upload_to_instagram(username, password, clip_path, caption):
    L = instaloader.Instaloader()
    try:
        L.load_session_from_file(username)
    except FileNotFoundError:
        L.context.log("Session file does not exist yet - Logging in.")
        L.context.log("Use `instaloader --login YOUR_USERNAME` to create a session file.")
        return

    try:
        L.upload_video(clip_path, caption=caption)
    except Exception as e:
        print(f"Error uploading to Instagram: {e}")
