from yt_dlp import YoutubeDL
import os
import json
from datetime import datetime, timedelta
import pytz

def get_yt(url, save_path='.'):
    """
    Download YouTube video, transcript, and save metadata to JSON.
    Automatically schedules one video per day at 6:30 AM IST.
    Tracks the last schedule date and increments by 1 day for each new video.
    """
    result = {
        'title': None,
        'description': None,
        'tags': None,
        'url': url,
        'video_file': None,
        'transcript_file': None
    }

    # File paths
    video_file = os.path.join(save_path, "yt_video.mp4")
    json_file = os.path.join(save_path, "yt_metadata.json")
    transcript_file = os.path.join(save_path, "yt_transcript.txt")
    track_file = os.path.join(save_path, "process_track.json")

    # ✅ Get IST timezone
    ist = pytz.timezone('Asia/Kolkata')
    now_ist = datetime.now(ist)

    # ✅ Load or create tracking file
    if os.path.exists(track_file):
        with open(track_file, 'r', encoding='utf-8') as f:
            processed = json.load(f)
    else:
        processed = []

    # ✅ Determine next schedule date (one video per day)
    if processed:
        # Get the last scheduled date and add 1 day
        last_item = processed[-1]
        last_schedule_str = last_item.get('schedule_date', '')
        
        try:
            # Parse last schedule date: "07-11-2025"
            last_date = datetime.strptime(last_schedule_str, "%d-%m-%Y")
            next_date = last_date + timedelta(days=1)
        except:
            # If parsing fails, start from today
            next_date = now_ist.replace(hour=6, minute=30, second=0, microsecond=0)
            if next_date <= now_ist:
                next_date += timedelta(days=1)
    else:
        # First video: schedule for today 6:30 AM or tomorrow if time passed
        next_date = now_ist.replace(hour=6, minute=30, second=0, microsecond=0)
        if next_date <= now_ist:
            next_date += timedelta(days=1)

    # Set schedule time to 6:30 AM IST
    schedule_time = next_date.replace(hour=6, minute=30, second=0, microsecond=0)
    
    # Format date as 7-11-2025 style (day-month-year)
    schedule_date = schedule_time.strftime("%d-%m-%Y")
    schedule_datetime = schedule_time.strftime("%d-%m-%Y %I:%M %p IST")

    print(f"\n📅 This video will be scheduled for: {schedule_datetime}")

    # ✅ Check if this URL was already processed
    for item in processed:
        if item.get('url') == url:
            print(f"⚠️ This video URL is already processed. Skipping download.")
            return result  # ⛔ Stop function early

    # ✅ Delete old files if they exist
    for fpath in [video_file, json_file, transcript_file]:
        if os.path.exists(fpath):
            os.remove(fpath)
            print(f"🧹 Old {os.path.basename(fpath)} deleted")

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

            # ✅ Extract transcript from subtitles
            transcript_text = ""
            subtitles = info_dict.get('subtitles', {})
            automatic_captions = info_dict.get('automatic_captions', {})
            
            # Try manual subtitles first, then automatic
            all_subs = subtitles if subtitles else automatic_captions
            
            if all_subs and 'en' in all_subs:
                # Get the subtitle data
                sub_list = all_subs['en']
                for sub in sub_list:
                    if 'url' in sub:
                        # Download and parse subtitle
                        try:
                            sub_data = ydl.urlopen(sub['url']).read().decode('utf-8')
                            # Basic cleanup for common subtitle formats
                            lines = sub_data.split('\n')
                            for line in lines:
                                # Skip timestamp lines and empty lines
                                if '-->' not in line and line.strip() and not line.strip().isdigit():
                                    transcript_text += line.strip() + " "
                            break
                        except:
                            continue
            
            # ✅ Save transcript to file
            if transcript_text:
                with open(transcript_file, 'w', encoding='utf-8') as f:
                    f.write(transcript_text.strip())
                result['transcript_file'] = transcript_file
                print("✅ Transcript saved as: yt_transcript.txt")
            else:
                print("⚠️ No transcript available for this video")

            # ✅ Save metadata with schedule info
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

            # ✅ Save to process_track.json
            processed.append(metadata)
            with open(track_file, 'w', encoding='utf-8') as f:
                json.dump(processed, f, indent=4, ensure_ascii=False)

            print(f"\n✅ Video downloaded as: yt_video.mp4")
            print(f"✅ Metadata saved as: yt_metadata.json")
            print(f"📅 Schedule: {schedule_datetime}")
            print(f"✅ Added to process_track.json")
            
            # Show next available slot
            next_available = schedule_time + timedelta(days=1)
            print(f"\n💡 Next video will be scheduled for: {next_available.strftime('%d-%m-%Y %I:%M %p IST')}")

    except Exception as e:
        print("❌ Error while downloading:", e)

    return result


# # Example usage:
# if __name__ == "__main__":
#     # Example: Download a video
#     url = "YOUR_YOUTUBE_URL_HERE"
#     get_yt(url)