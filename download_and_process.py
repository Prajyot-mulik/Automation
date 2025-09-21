import os
import random
from datetime import datetime
from downloader import get_random_short
from processor import process_video
import pandas as pd
import requests

def check_internet():
    """Check if internet is available by pinging Google."""
    try:
        requests.get("https://www.google.com", timeout=5)
        return True
    except requests.ConnectionError:
        return False

def check_todays_downloads(excel_path):
    """Check if today's videos are already downloaded."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    if os.path.exists(excel_path):
        df = pd.read_excel(excel_path)
        todays_videos = df[df['download_date'] == today_str]
        return len(todays_videos) >= 7
    return False

def download_and_process():
    """Download and process 7 unique videos, save data for uploads."""
    # Check internet
    if not check_internet():
        print("❌ No internet connection. Exiting.")
        return False

    # Check if today's downloads are already done
    excel_path = "video_tracker.xlsx"
    if check_todays_downloads(excel_path):
        print(f"✅ Today's videos already downloaded/processed. Skipping to avoid duplicates.")
        return True

    channels = [
        "https://www.youtube.com/@Chhota_Blast_09",
        "https://www.youtube.com/@FlixIQ",
        "https://www.youtube.com/@Zynfo01",
        "https://www.youtube.com/@Factrin25",
        "https://www.youtube.com/@AnuFacto-k9s"
    ]

    video_data_file = "video_data.txt"
    video_data = []
    max_videos = 7
    tried_channels = set()
    attempts_per_channel = 10

    # Create output folder
    today_str = datetime.now().strftime("%Y-%m-%d")
    output_folder = os.path.join("output_videos", today_str)
    os.makedirs(output_folder, exist_ok=True)

    # Download 7 unique videos
    while len(video_data) < max_videos and len(tried_channels) < len(channels):
        channel_url = random.choice([c for c in channels if c not in tried_channels])
        tried_channels.add(channel_url)
        channel_name = channel_url.split("@")[-1]
        print(f"📺 Trying channel: {channel_url}")

        for _ in range(attempts_per_channel):
            try:
                input_path, video_id, title, description = get_random_short(channel_url, excel_path)
                output_path = os.path.join(output_folder, f"{len(video_data)+1}.mp4")
                process_video(
                    input_path,
                    output_path,
                    semitones=-0.5,
                    bass_gain=4.9,
                    volume_boost=1.3,
                    credit_text=channel_name
                )
                video_data.append((input_path, output_path, video_id, title, description))
                print(f"✅ Processed video {len(video_data)}/{max_videos}")
                break
            except Exception as e:
                print(f"⚠️ Failed to fetch/process from {channel_url}: {e}")
                continue

    if len(video_data) < max_videos:
        print(f"❌ Could not download {max_videos} unique videos. Only got {len(video_data)}.")
        return False

    # Save video data for uploads
    with open(video_data_file, 'w') as f:
        for data in video_data:
            f.write(f"{data[0]}|{data[1]}|{data[2]}|{data[3]}|{data[4]}\n")
    print(f"✅ Saved video data to {video_data_file}")
    return True

if __name__ == "__main__":
    success = download_and_process()
    exit(0 if success else 1)