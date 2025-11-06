from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
import pickle
import os
import json
import time
import traceback
from datetime import datetime, timedelta, time as dtime

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']


def authenticate_youtube():
    """Authenticate once and reuse token automatically (no manual re-verify)."""
    creds = None
    token_file = 'token.pickle'

    # Load existing credentials if available
    if os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)

    # If no credentials or expired
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing YouTube token silently...")
            creds.refresh(Request())
        else:
            print("🌐 First-time authentication — only once.")
            flow = InstalledAppFlow.from_client_secrets_file('secrect_code.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save for next runs
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)

    return build('youtube', 'v3', credentials=creds)


def get_next_upload_time():
    """Return next 7:35 AM — today if not passed, else tomorrow."""
    now = datetime.now()
    scheduled_time = datetime.combine(now.date(), dtime(7, 35))
    if now >= scheduled_time:
        scheduled_time += timedelta(days=1)
    print(f"📅 Next upload: {scheduled_time.strftime('%Y-%m-%d %I:%M %p')}")
    return scheduled_time


def load_metadata(file):
    try:
        with open(file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def prepare_video_details(metadata=None):
    # Hashtags in description are what show up visibly on YouTube
    default_hashtags = "#sciencefacts #amazingfacts #subscribe #shorts"
    
    if not metadata:
        print("ℹ️ Using default video details with custom hashtags.")
        return {
            'title': 'Amazing Short Video',
            'description': f'Check out this awesome short video! 🔥\n\n{default_hashtags}',
            'tags': ['shorts', 'sciencefacts', 'amazingfacts', 'subscribe', 'viral', 'trending']
        }
    
    title = metadata.get('title', 'Untitled Video')
    # Keep title clean - YouTube shows hashtags from description, not title
    # Title has 100 char limit, so keep it simple
    if len(title) > 90:
        title = title[:90]
    
    description = metadata.get('description', '')
    # Add hashtags at the END of description - this is where YouTube displays them
    if description:
        description = f'{description}\n\n{default_hashtags}'
    else:
        description = default_hashtags
    
    # Combine metadata tags with default tags
    tags = metadata.get('tags', [])
    default_tags = ['shorts', 'sciencefacts', 'amazingfacts', 'subscribe']
    # Add default tags if not already present
    for tag in default_tags:
        if tag not in tags:
            tags.append(tag)
    
    return {
        'title': title,
        'description': description,
        'tags': tags
    }


def upload_video(video_file='output_video.mp4', info_file='yt_metadata.json'):
    """Upload one video, scheduled for next 7:35 AM."""
    try:
        if not os.path.exists(video_file):
            return {'error': f'File not found: {video_file}'}

        metadata = load_metadata(info_file)
        details = prepare_video_details(metadata)
        schedule_time = get_next_upload_time().isoformat() + 'Z'

        youtube = authenticate_youtube()

        body = {
            'snippet': {
                'title': details['title'],
                'description': details['description'],
                'tags': details['tags'],
                'categoryId': '22',
                'defaultLanguage': 'hi',  # Hindi language code
                'defaultAudioLanguage': 'hi'  # Audio is in Hindi
            },
            'status': {
                'privacyStatus': 'private',
                'publishAt': schedule_time,
                'selfDeclaredMadeForKids': False,
                'madeForKids': False
            }
        }
        
        # Add altered content disclosure if needed
        # Set to True if your content is AI-generated or synthetically altered
        # Set to False if it's original unaltered content
        altered_content = False  # Change to True if your videos are AI-generated/altered
        
        if altered_content:
            body['status']['containsSyntheticMedia'] = True

        print(f"🚀 Uploading: {details['title']}")
        media = MediaFileUpload(video_file, chunksize=5 * 1024 * 1024, resumable=True)
        request = youtube.videos().insert(part='snippet,status', body=body, media_body=media)

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"📤 Progress: {int(status.progress() * 100)}%")
            else:
                time.sleep(2)

        vid = response.get('id')
        print(f"\n✅ Upload done!")
        print(f"🔗 https://www.youtube.com/watch?v={vid}")
        return {'success': True, 'video_id': vid}

    except Exception as e:
        print("❌ Upload error:", e)
        traceback.print_exc()
        return {'error': str(e)}
    

