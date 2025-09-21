import os
import pickle
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from googleapiclient.http import MediaFileUpload
import pandas as pd

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_SECRETS_FILE = "client_secret.json"  # Save your JSON here

def load_excel(excel_path):
    """Load Excel sheet for updating status."""
    if os.path.exists(excel_path):
        try:
            df = pd.read_excel(excel_path)
            return df
        except Exception as e:
            print(f"Error loading Excel: {e}. Creating new Excel sheet.")
    return pd.DataFrame(columns=['video_id', 'title', 'description', 'download_date', 'status'])

def update_status(excel_path, video_id, status):
    """Update status in Excel sheet for a given video ID."""
    df = load_excel(excel_path)
    df.loc[df['video_id'] == video_id, 'status'] = status
    df.to_excel(excel_path, index=False)
    print(f"✅ Updated status for video {video_id} to {status} in {excel_path}")

def get_authenticated_service():
    """Authenticate with YouTube API."""
    creds = None
    token_file = "token.pickle"

    if os.path.exists(token_file):
        with open(token_file, "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            CLIENT_SECRETS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(token_file, "wb") as token:
            pickle.dump(creds, token)

    return googleapiclient.discovery.build("youtube", "v3", credentials=creds)

def upload_video(file_path, title, description="", tags=None, category_id="22", privacy_status="public", excel_path=None, video_id=None):
    """Upload video to YouTube and update Excel status."""
    youtube = get_authenticated_service()

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags or [],
            "categoryId": category_id
        },
        "status": {
            "privacyStatus": privacy_status
        }
    }

    media = MediaFileUpload(file_path, chunksize=-1, resumable=True)

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"⬆️ Upload progress: {int(status.progress() * 100)}%")

    print("✅ Upload complete!")
    print("📺 Video URL:", f"https://youtu.be/{response['id']}")

    # Update Excel status to "Uploaded"
    if excel_path and video_id:
        update_status(excel_path, video_id, "Uploaded")

    return response["id"]