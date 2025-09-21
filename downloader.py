import requests
import random
import yt_dlp
import os
import time
from datetime import datetime
import pandas as pd

API_KEY = "AIzaSyBP0jwYqKk0E--mxVVkxudS63Adl_Y3ldg"  # Replace with your API key

def safe_get(url, retries=3, delay=2):
    """Retry GET requests on SSL/network errors."""
    for attempt in range(retries):
        try:
            return requests.get(url, timeout=10)
        except requests.exceptions.SSLError as e:
            print(f"SSL error: {e} — retrying ({attempt+1}/{retries})...")
            time.sleep(delay)
        except requests.exceptions.RequestException as e:
            print(f"Network error: {e} — retrying ({attempt+1}/{retries})...")
            time.sleep(delay)
    raise RuntimeError("Failed to connect after retries")

def load_excel(excel_path):
    """Load or create Excel sheet for tracking video metadata."""
    if os.path.exists(excel_path):
        try:
            df = pd.read_excel(excel_path)
            required_columns = ['video_id', 'title', 'description', 'download_date', 'status']
            for col in required_columns:
                if col not in df.columns:
                    df[col] = ''
            return df
        except Exception as e:
            print(f"Error loading Excel: {e}. Creating new Excel sheet.")
    return pd.DataFrame(columns=['video_id', 'title', 'description', 'download_date', 'status'])

def save_to_excel(excel_path, video_id, title, description, status="Pending"):
    """Append video metadata to Excel sheet with status."""
    df = load_excel(excel_path)
    new_row = {
        'video_id': video_id,
        'title': title,
        'description': description,
        'download_date': datetime.now().strftime("%Y-%m-%d"),
        'status': status
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_excel(excel_path, index=False)
    print(f"✅ Saved metadata to {excel_path}: {video_id}, {title}, Status: {status}")

def get_random_short(channel_url, excel_path, max_attempts=50):
    """Download a unique random short, checking for duplicates in Excel."""
    df = load_excel(excel_path)
    downloaded_ids = set(df['video_id'].values)

    # Get channel ID from handle
    handle = channel_url.split("/")[-1]
    url = f"https://www.googleapis.com/youtube/v3/channels?part=id&forHandle={handle}&key={API_KEY}"
    res = safe_get(url).json()

    if "items" not in res or not res["items"]:
        raise RuntimeError(f"❌ Could not find channel: {handle}")

    channel_id = res["items"][0]["id"]

    # Get recent videos
    video_url = (
        f"https://www.googleapis.com/youtube/v3/search?"
        f"part=snippet&channelId={channel_id}&maxResults=50&order=date&type=video&key={API_KEY}"
    )
    videos = safe_get(video_url).json()

    if "items" not in videos or not videos["items"]:
        raise RuntimeError(f"❌ No videos found for channel: {handle}")

    shorts = [
        {
            'url': f"https://www.youtube.com/watch?v={item['id']['videoId']}",
            'video_id': item['id']['videoId'],
            'title': item['snippet']['title'],
            'description': item['snippet']['description']
        }
        for item in videos["items"]
    ]

    if not shorts:
        raise RuntimeError(f"❌ No Shorts found for channel: {handle}")

    # Filter out already downloaded videos
    available_shorts = [s for s in shorts if s['video_id'] not in downloaded_ids]
    if not available_shorts:
        raise RuntimeError(f"❌ No unique Shorts available for channel: {handle}")

    # Pick random short
    selected_short = random.choice(available_shorts)
    video_url = selected_short['url']
    video_id = selected_short['video_id']
    title = selected_short['title']
    description = selected_short['description']
    print(f"🎬 Selected short: {video_url} (ID: {video_id})")

    # Prepare folder structure
    today_str = datetime.now().strftime("%Y-%m-%d")
    input_folder = os.path.join("input_videos", today_str)
    os.makedirs(input_folder, exist_ok=True)

    # Determine next file number
    existing_files = [f for f in os.listdir(input_folder) if f.endswith(".mp4")]
    next_number = len(existing_files) + 1
    file_path = os.path.join(input_folder, f"{next_number}.mp4")

    # Download with yt-dlp
    ydl_opts = {
        "outtmpl": file_path,
        "format": "best",
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])

    # Save metadata to Excel
    save_to_excel(excel_path, video_id, title, description, status="Pending")
    print(f"✅ Downloaded to {file_path}")
    return file_path, video_id, title, description