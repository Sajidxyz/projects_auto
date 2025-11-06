from yt_dlp import YoutubeDL
import os
import json
from datetime import datetime, timedelta
import pytz

def get_yt(url, save_path='.'):
    """
    Download YouTube video, transcript, and save metadata to JSON.
    Automatically schedules one video per day at 6:30 AM IST.
    Handles missing files safely.
    """
    result = {
        'title': None,
        'description': None,
        'tags': None,
        'url': url,
        'video_file': None,
        'transcript_file': None
    }

    # ✅ Ensure save directory exists
    try:
        os.makedirs(save_path, exist_ok=True)
    except Exception as e:
        print(f"❌ Cannot create save folder: {e}")
        return result

    # File paths
    video_file = os.path.join(save_path, "yt_video.mp4")
    json_file = os.path.join(save_path, "yt_metadata.json")
    transcript_file = os.path.join(save_path, "yt_transcript.txt")
    track_file = os.path.join(save_path, "process_track.json")

    ist = pytz.timezone('Asia/Kolkata')
    now_ist = datetime.now(ist)

    # ✅ Load or create tracking file safely
    if os.path.exists(track_file):
        try:
            with open(track_file, 'r', encoding='utf-8') as f:
                processed = json.load(f)
        except json.JSONDecodeError:
            print("⚠️ Corrupted process_track.json detected — resetting it.")
            processed = []
        except Exception as e:
            print(f"⚠️ Could not read process_track.json: {e}")
            processed = []
    else:
        processed = []

    # ✅ Determine next schedule date
    if processed:
        last_item = processed[-1]
        last_schedule_str = last_item.get('schedule_date', '')
        try:
            last_date = datetime.strptime(last_schedule_str, "%d-%m-%Y")
            next_date = last_date + timedelta(days=1)
        except Exception:
            next_date = now_ist.replace(hour=6, minute=30, second=0, microsecond=0)
            if next_date <= now_ist:
                next_date += timedelta(days=1)
    else:
        next_date = now_ist.replace(hour=6, minute=30, second=0, microsecond=0)
        if next_date <= now_ist:
            next_date += timedelta(days=1)

    schedule_time = next_date.replace(hour=6, minute=30, second=0, microsecond=0)
    schedule_date = schedule_time.strftime("%d-%m-%Y")
    schedule_datetime = schedule_time.strftime("%d-%m-%Y %I:%M %p IST")

    print(f"\n📅 This video will be scheduled for: {schedule_datetime}")

    # ✅ Skip if already processed
    for item in processed:
        if item.get('url') == url:
            print(f"⚠️ This video URL was already processed. Skipping download.")
            return result

    # ✅ Clean old files safely
    for fpath in [video_file, json_file, transcript_file]:
        try:
            if os.path.exists(fpath):
                os.remove(fpath)
                print(f"🧹 Deleted old file: {os.path.basename(fpath)}")
        except Exception as e:
            print(f"⚠️ Failed to delete {os.path.basename(fpath)}: {e}")

    try:
        # ✅ yt-dlp settings
        ydl_opts = {
            'outtmpl': os.path.join(save_path, 'yt_video.%(ext)s'),
            'format': 'best',
            'quiet': False,
            'noplaylist': True,
            'overwrites': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['en'],
            'skip_download': False
        }

        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            result['title'] = info_dict.get('title')
            result['description'] = info_dict.get('description')
            result['tags'] = info_dict.get('tags', [])
            result['video_file'] = video_file

            # ✅ Try to extract transcript
            transcript_text = ""
            try:
                subtitles = info_dict.get('subtitles', {})
                automatic_captions = info_dict.get('automatic_captions', {})
                all_subs = subtitles if subtitles else automatic_captions

                if all_subs and 'en' in all_subs:
                    sub_list = all_subs['en']
                    for sub in sub_list:
                        if 'url' in sub:
                            try:
                                sub_data = ydl.urlopen(sub['url']).read().decode('utf-8')
                                lines = sub_data.split('\n')
                                for line in lines:
                                    if '-->' not in line and line.strip() and not line.strip().isdigit():
                                        transcript_text += line.strip() + " "
                                break
                            except Exception as e:
                                print(f"⚠️ Failed to read subtitles: {e}")
                                continue
                else:
                    print("⚠️ No subtitles available in English.")
            except Exception as e:
                print(f"⚠️ Error while processing subtitles: {e}")

            # ✅ Save transcript safely
            if transcript_text:
                try:
                    with open(transcript_file, 'w', encoding='utf-8') as f:
                        f.write(transcript_text.strip())
                    result['transcript_file'] = transcript_file
                    print("✅ Transcript saved as: yt_transcript.txt")
                except Exception as e:
                    print(f"⚠️ Could not save transcript: {e}")
            else:
                print("⚠️ No transcript found for this video.")

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

            try:
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=4, ensure_ascii=False)
            except Exception as e:
                print(f"⚠️ Could not save metadata: {e}")

            # ✅ Save schedule tracking safely
            try:
                processed.append(metadata)
                with open(track_file, 'w', encoding='utf-8') as f:
                    json.dump(processed, f, indent=4, ensure_ascii=False)
                print(f"✅ Added to process_track.json")
            except Exception as e:
                print(f"⚠️ Could not update process_track.json: {e}")

            print(f"\n✅ Video downloaded as: yt_video.mp4")
            print(f"✅ Metadata saved as: yt_metadata.json")
            print(f"📅 Schedule: {schedule_datetime}")
            print(f"💡 Next slot: {(schedule_time + timedelta(days=1)).strftime('%d-%m-%Y %I:%M %p IST')}")

    except Exception as e:
        print("❌ Error during download process:", e)

    return result
