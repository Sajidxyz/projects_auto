# automation.py
import json
import time
from download_yt_v import get_yt
from text_to_audio_generater import dub_audio
from edit_video import video_edit
from speed import adjust_audio_tone
from yt_uploader import upload_video

URL_LINKS = 'shorts_links.json'
PROCESS_TRACK = 'process_track.json'


def get_single_new_url() -> str | None:
    """Return the first un-processed YouTube Shorts URL, or None."""
    # ---- load shorts -------------------------------------------------
    try:
        with open(URL_LINKS, 'r', encoding='utf-8') as f:
            shorts_data = json.load(f)
    except Exception as e:
        print(f"[ERROR] loading {URL_LINKS}: {e}")
        return None

    # ---- load already processed --------------------------------------
    try:
        with open(PROCESS_TRACK, 'r', encoding='utf-8') as f:
            processed_data = json.load(f)
    except FileNotFoundError:
        processed_data = []
    except Exception as e:
        print(f"[ERROR] loading {PROCESS_TRACK}: {e}")
        processed_data = []

    shorts_urls = [
        item.get('orig_url') or item.get('shorts_url')
        for item in shorts_data
        if item.get('orig_url') or item.get('shorts_url')
    ]
    processed_urls = {item.get('url') for item in processed_data if item.get('url')}

    for url in shorts_urls:
        if url and url not in processed_urls and "youtube.com/shorts/" in url:
            return url

    print("No new Shorts URLs found.")
    return None


def run_automation() -> str:
    """Execute the full pipeline for ONE short."""
    print("\n=== Automation START ===")
    url = get_single_new_url()
    if not url:
        msg = "No new URL to process."
        print(msg)
        return msg

    try:
        get_yt(url)
        time.sleep(1)
        dub_audio()
        time.sleep(1)
        adjust_audio_tone("hindi_dub.mp3")
        time.sleep(1)
        video_edit(choose_bg='')
        result = upload_video()

        # ---- remember this URL as processed -------------------------
        try:
            with open(PROCESS_TRACK, 'r', encoding='utf-8') as f:
                track = json.load(f)
        except FileNotFoundError:
            track = []

        track.append({"url": url, "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")})
        with open(PROCESS_TRACK, 'w', encoding='utf-8') as f:
            json.dump(track, f, indent=2, ensure_ascii=False)

        print("=== Automation SUCCESS ===")
        return f"SUCCESS – {result}"
    except Exception as e:
        err = f"Automation FAILED: {e}"
        print(err)
        return err