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

def find_key_moments(transcription_data, clip_length='30-120', num_clips=3):
    """
    OPTIMIZED: Analyze transcription using smart sampling to minimize token usage.

    Token Optimization Strategy:
    - Condenses transcript format (timestamps only at time ranges)
    - Intelligent sampling based on video length
    - Always tries GPT-3.5-turbo first (cheaper)
    - Reduces tokens by 80-90% vs sending full transcript

    Args:
        transcription_data: Dict with 'text' and 'segments'
        clip_length: Desired clip length range (e.g., "30-60", "60-90", "90-120", "30-120")
        num_clips: Number of clips to generate

    Returns:
        Dict with 'moments' list
    """
    # Parse clip length range
    min_length, max_length = map(int, clip_length.split('-'))
    segments = transcription_data.get('segments', [])

    if not segments:
        return {'moments': []}

    # Calculate video duration
    video_duration = segments[-1].get('end', 0) if segments else 0

    print(f"📊 Video duration: {video_duration/60:.1f} minutes, {len(segments)} segments")

    # SMART SAMPLING: Reduce segments intelligently
    # For long videos, we don't need every segment - sample strategically
    if len(segments) > 200:
        # Sample every Nth segment to keep around 150-200 segments max
        sample_rate = len(segments) // 150
        sampled = segments[::sample_rate]
        print(f"⚡ Sampled {len(sampled)} segments from {len(segments)} (every {sample_rate}th)")
    elif len(segments) > 100:
        # Light sampling for medium videos
        sampled = segments[::2]
        print(f"⚡ Sampled {len(sampled)} segments from {len(segments)} (every 2nd)")
    else:
        sampled = segments

    # CONDENSED FORMAT: Use compact representation
    # Instead of full text for each segment, group into time ranges
    condensed_segments = []
    current_group = []
    current_start = None
    group_duration = 30  # Group segments into 30-second chunks

    for seg in sampled:
        start = seg.get('start', 0)
        end = seg.get('end', 0)
        text = seg.get('text', '').strip()

        if current_start is None:
            current_start = start

        current_group.append(text)

        # Create a group when we hit duration or last segment
        if (end - current_start) >= group_duration or seg == sampled[-1]:
            combined_text = ' '.join(current_group)
            # Truncate very long groups
            if len(combined_text) > 200:
                combined_text = combined_text[:200] + '...'

            condensed_segments.append({
                'time': f"{int(current_start)}-{int(end)}s",
                'content': combined_text
            })
            current_group = []
            current_start = None

    # Build ultra-compact transcript
    compact_transcript = "\n".join([
        f"[{seg['time']}] {seg['content']}"
        for seg in condensed_segments
    ])

    estimated_tokens = len(compact_transcript) / 4
    print(f"💰 Estimated tokens: {estimated_tokens:.0f} (vs {len(' '.join([s.get('text', '') for s in segments]))/4:.0f} original)")

    system_prompt = f"""You are an expert video editor that identifies engaging, interesting moments from video transcriptions for social media clips.

REQUIREMENTS:
- Each clip MUST be between {min_length} and {max_length} seconds long
- Identify EXACTLY {num_clips} moments (no more, no less)
- Moments should be self-contained, interesting, funny, insightful, or have viral potential
- Use the actual timestamps provided in the transcription
- Each moment should have clear start and end times
- Prioritize the MOST engaging content

Respond ONLY with valid JSON in this exact format:
{{
  "moments": [
    {{
      "start_time": 10.5,
      "end_time": 45.2,
      "text": "Brief description of what makes this moment interesting"
    }}
  ]
}}"""

    user_prompt = f"""Analyze this timestamped transcription and identify EXACTLY {num_clips} key moments suitable for social media clips.

Timestamped Transcription:
{compact_transcript}

Remember: Each clip must be {min_length}-{max_length} seconds long. Provide EXACTLY {num_clips} clips. Use the exact timestamps from the transcription."""

    # ALWAYS try GPT-3.5-turbo first (cheapest), then fallback to more expensive models
    models_to_try = ["gpt-3.5-turbo", "gpt-4o", "gpt-4-turbo", "gpt-4"]

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
            result = json.loads(response.choices[0].message.content)

            # Log token savings
            print(f"💰 Token optimization successful! Reduced by ~{100 - (estimated_tokens/(len(' '.join([s.get('text', '') for s in segments]))/4)*100):.0f}%")

            return result

        except Exception as e:
            error_str = str(e)
            if "model_not_found" in error_str or "does not exist" in error_str:
                print(f"⚠️  Model {attempt_model} not available, trying next...")
                last_error = e
                continue
            elif "context_length_exceeded" in error_str or "too large" in error_str.lower() or "429" in error_str:
                print(f"⚠️  Request too large for {attempt_model}, trying next...")
                last_error = e
                continue
            else:
                # Other error, raise it
                raise e

    # If we get here, all models failed - try even more aggressive chunking
    print("⚠️  All models failed, using ultra-compressed approach with first 20% of video...")

    # Take only first 20% of segments and compress even more
    reduced_segments = segments[:max(1, len(segments)//5)]
    ultra_compact = []

    for i in range(0, len(reduced_segments), 10):
        chunk = reduced_segments[i:i+10]
        if chunk:
            start = chunk[0].get('start', 0)
            end = chunk[-1].get('end', 0)
            text = ' '.join([s.get('text', '')[:50] for s in chunk])  # Limit each to 50 chars
            ultra_compact.append(f"[{int(start)}-{int(end)}s] {text[:100]}")

    ultra_compact_transcript = "\n".join(ultra_compact)

    user_prompt_ultra = f"""Analyze this timestamped transcription and identify {min(num_clips, 3)} key moments suitable for social media clips.

Timestamped Transcription:
{ultra_compact_transcript}

Remember: Each clip must be {min_length}-{max_length} seconds long. Use the exact timestamps from the transcription."""

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt_ultra}
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

def create_subtitle_clip(text, color, video_width, duration):
    """
    Create a subtitle TextClip with comprehensive error handling for different MoviePy versions.

    Returns:
        TextClip or None if creation fails
    """
    import os

    # Try multiple font options (Windows needs full paths, Linux/Mac can use names)
    fonts_to_try = []

    # Windows fonts
    if os.path.exists(r'C:\Windows\Fonts'):
        fonts_to_try.extend([
            r'C:\Windows\Fonts\arial.ttf',
            r'C:\Windows\Fonts\verdana.ttf',
            r'C:\Windows\Fonts\calibri.ttf',
            r'C:\Windows\Fonts\times.ttf',
        ])

    # Linux/Mac fonts
    fonts_to_try.extend(['Arial', 'Verdana', 'DejaVu-Sans', 'Helvetica'])

    subtitle = None

    # Try different API approaches with different fonts
    errors = []

    for font in fonts_to_try:
        if subtitle is not None:
            break

        # Approach 1: Font as first positional, text keyword, font_size
        try:
            clip = TextClip(font, text=text, font_size=24, color=color,
                          size=(video_width - 100, None), method='caption')
            # Try to position it
            subtitle = clip.set_position(('center', 'bottom')).set_duration(duration)
            print(f"✅ Subtitle method: Font-first positional with set_position, font={font}")
            return subtitle
        except Exception as e:
            errors.append(f"Approach 1 ({font}): {e}")

        # Approach 2: All keyword arguments
        try:
            clip = TextClip(text=text, font=font, font_size=24, color=color,
                          size=(video_width - 100, None), method='caption')
            subtitle = clip.set_position(('center', 'bottom')).set_duration(duration)
            print(f"✅ Subtitle method: All keywords with set_position, font={font}")
            return subtitle
        except Exception as e:
            errors.append(f"Approach 2 ({font}): {e}")

        # Approach 3: Minimal parameters, try set_pos instead of set_position
        try:
            clip = TextClip(text=text, font=font, fontsize=24, color=color)
            subtitle = clip.set_pos(('center', 'bottom')).set_duration(duration)
            print(f"✅ Subtitle method: Minimal with set_pos, font={font}")
            return subtitle
        except Exception as e:
            errors.append(f"Approach 3 ({font}): {e}")

    # If all attempts failed, print detailed errors and return None
    print(f"⚠️  All subtitle approaches failed. Sample errors:")
    for err in errors[:3]:  # Show first 3 errors
        print(f"   - {err}")
    return None

def generate_clips(video_path, transcription_data, subtitle_color='white', emojis=None, effects=None, clip_length='30-120', num_clips=3):
    """
    Generate video clips from key moments identified in the transcription.

    Args:
        video_path: Path to the source video file
        transcription_data: Dict with 'text' and 'segments' from transcribe_video()
        subtitle_color: Color for subtitle text (default: white)
        emojis: Optional emoji string to prepend to subtitles
        effects: Optional effects string (e.g., "speed:1.5,fadein:0.5")
        clip_length: Desired clip length range (e.g., "30-60", "60-90", "90-120", "30-120")
        num_clips: Number of clips to generate (default: 3)

    Returns:
        List of paths to generated clip files
    """
    key_moments = find_key_moments(transcription_data, clip_length, num_clips)
    video_clip = VideoFileClip(video_path)
    clip_paths = []
    segments = transcription_data.get('segments', [])

    # Parse clip length range for validation
    min_length, max_length = map(int, clip_length.split('-'))

    for i, moment in enumerate(key_moments['moments']):
        start_time = moment['start_time']
        end_time = moment['end_time']
        clip_duration = end_time - start_time

        # Validate clip duration with user-specified range
        if clip_duration < min_length:
            print(f"Skipping clip {i}: too short ({clip_duration:.1f}s < {min_length}s)")
            continue
        if clip_duration > max_length:
            print(f"Skipping clip {i}: too long ({clip_duration:.1f}s > {max_length}s)")
            continue

        # Create the subclip first (try different API methods)
        try:
            clip_segment = video_clip.subclip(start_time, end_time)
        except AttributeError:
            try:
                clip_segment = video_clip.subclipped(start_time, end_time)
            except AttributeError:
                # Some versions use cutout/crop differently
                clip_segment = video_clip.set_start(start_time).set_end(end_time)

        # Apply effects if specified
        if effects:
            clip_segment = apply_effects(clip_segment, effects)

        # Try to add subtitles (optional - will skip if fails)
        final_clip = clip_segment  # Default: no subtitles

        try:
            # Extract segment-specific text for this clip
            segment_text = get_text_for_timerange(segments, start_time, end_time)

            # Create subtitle text for this specific segment
            subtitle_text = segment_text[:500]  # Limit length to avoid issues
            if emojis:
                subtitle_text = f"{emojis} {subtitle_text}"

            # Try to create subtitle with MoviePy (get width safely)
            try:
                video_width = clip_segment.w
            except:
                try:
                    video_width = clip_segment.size[0]
                except:
                    video_width = 1920  # Default HD width

            subtitle = create_subtitle_clip(subtitle_text, subtitle_color, video_width, clip_duration)

            if subtitle:
                # Composite the video and subtitle
                final_clip = CompositeVideoClip([clip_segment, subtitle])
                print(f"✅ Added subtitles to clip {i}")
            else:
                print(f"⚠️  Skipping subtitles for clip {i} (not critical)")

        except Exception as e:
            print(f"⚠️  Could not add subtitles to clip {i}: {e}")
            print(f"   Generating clip without subtitles...")

        if not os.path.exists('clips'):
            os.makedirs('clips')

        clip_path = os.path.join('clips', f"clip_{i}_{os.path.basename(video_path)}")

        # Write video file (try different API methods)
        try:
            final_clip.write_videofile(clip_path, codec='libx264', logger=None)
        except TypeError:
            # Older versions don't have logger parameter
            try:
                final_clip.write_videofile(clip_path, codec='libx264')
            except AttributeError:
                # Some versions use different method name
                final_clip.write_video_file(clip_path, codec='libx264')

        clip_paths.append(clip_path)
        print(f"✅ Generated clip: {os.path.basename(clip_path)}")

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
