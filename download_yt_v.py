from yt_dlp import YoutubeDL
import os
import json
from datetime import datetime, timedelta
import pytz

def get_yt(url, save_path='.'):
    """
    Download YouTube video, transcript, and save metadata to JSON.
    Now includes cookie authentication for Render-safe deployment.
    """

    result = {
        'title': None,
        'description': None,
        'tags': None,
        'url': url,
        'video_file': None,
        'transcript_file': None
    }

    # ✅ Ensure directory exists
    os.makedirs(save_path, exist_ok=True)

    # Paths
    video_file = os.path.join(save_path, "yt_video.mp4")
    json_file = os.path.join(save_path, "yt_metadata.json")
    transcript_file = os.path.join(save_path, "yt_transcript.txt")
    track_file = os.path.join(save_path, "process_track.json")

    ist = pytz.timezone('Asia/Kolkata')
    now_ist = datetime.now(ist)

    # ✅ Load tracking
    processed = []
    if os.path.exists(track_file):
        try:
            with open(track_file, 'r', encoding='utf-8') as f:
                processed = json.load(f)
        except Exception:
            print("⚠️ process_track.json is corrupted, resetting...")

    # ✅ Next schedule logic
    next_date = now_ist.replace(hour=6, minute=30, second=0, microsecond=0)
    if next_date <= now_ist:
        next_date += timedelta(days=1)

    schedule_date = next_date.strftime("%d-%m-%Y")
    schedule_datetime = next_date.strftime("%d-%m-%Y %I:%M %p IST")
    print(f"📅 Scheduled for: {schedule_datetime}")

    # ✅ Skip duplicates
    if any(item.get('url') == url for item in processed):
        print("⚠️ Already processed. Skipping.")
        return result

    # ✅ Clean up
    for f in [video_file, json_file, transcript_file]:
        if os.path.exists(f):
            os.remove(f)
            print(f"🧹 Deleted: {os.path.basename(f)}")

    try:
        # ✅ Use cookies.txt (upload your exported file to project root)
        cookie_path = os.path.join(save_path, "cookies.txt")
        if not os.path.exists(cookie_path):
            print("⚠️ cookies.txt not found — YouTube may block download.")

        ydl_opts = {
            'outtmpl': os.path.join(save_path, 'yt_video.%(ext)s'),
            'format': 'best',
            'quiet': False,
            'noplaylist': True,
            'overwrites': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['en'],
            'cookiefile': cookie_path if os.path.exists(cookie_path) else None,
        }

        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            result['title'] = info_dict.get('title')
            result['description'] = info_dict.get('description')
            result['tags'] = info_dict.get('tags', [])
            result['video_file'] = video_file

        # ✅ Transcript (if captions exist)
        transcript_text = ""
        try:
            subs = info_dict.get('subtitles') or info_dict.get('automatic_captions') or {}
            if 'en' in subs:
                for sub in subs['en']:
                    if 'url' in sub:
                        sub_data = YoutubeDL().urlopen(sub['url']).read().decode('utf-8', errors='ignore')
                        for line in sub_data.split('\n'):
                            if '-->' not in line and line.strip() and not line.strip().isdigit():
                                transcript_text += line.strip() + " "
                        break
            else:
                print("⚠️ No English subtitles available.")
        except Exception as e:
            print(f"⚠️ Subtitle parse failed: {e}")

        # ✅ Save transcript
        if transcript_text:
            with open(transcript_file, 'w', encoding='utf-8') as f:
                f.write(transcript_text.strip())
            result['transcript_file'] = transcript_file
            print("✅ Transcript saved.")
        else:
            print("⚠️ No transcript found.")

        # ✅ Save metadata
        metadata = {
            'title': result['title'],
            'description': result['description'],
            'tags': result['tags'],
            'url': url,
            'has_transcript': bool(transcript_text),
            'schedule_date': schedule_date,
            'schedule_time': schedule_datetime,
            'processed_at': now_ist.strftime("%d-%m-%Y %I:%M:%S %p IST")
        }
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=4, ensure_ascii=False)

        # ✅ Update tracker
        processed.append(metadata)
        with open(track_file, 'w', encoding='utf-8') as f:
            json.dump(processed, f, indent=4, ensure_ascii=False)

        print("✅ Download and save complete.")

    except Exception as e:
        print("❌ Error during download process:", e)

    return result
