import os
import random
from datetime import datetime, timedelta
import time
from downloader import get_random_short
from processor import process_video
from uploader import upload_video

def schedule_uploads(video_data, excel_path):
    """Schedule uploads at specified times."""
    upload_times = [
        "08:00",  # 8 AM
        "09:00",  # 9 AM
        "15:00",  # 3 PM
        "16:00",  # 4 PM
        "17:00",  # 5 PM
        "18:00",  # 6 PM
        "19:00"   # 7 PM
    ]

    today = datetime.now().date()
    for i, (input_path, output_path, video_id, title, description) in enumerate(video_data):
        upload_time_str = upload_times[i]
        upload_time = datetime.strptime(f"{today} {upload_time_str}", "%Y-%m-%d %H:%M")
        
        # If upload time has passed for today, schedule for tomorrow
        if upload_time < datetime.now():
            upload_time += timedelta(days=1)
        
        # Calculate delay in seconds
        delay = (upload_time - datetime.now()).total_seconds()
        if delay > 0:
            print(f"📅 Scheduling upload for {output_path} at {upload_time_str} (in {delay:.2f} seconds)")
            time.sleep(delay)
        
        print(f"⬆️ Starting upload for {output_path}")
        upload_video(
            output_path,
            title=f"{title} - Automated Upload #{i+1}",
            description=description,
            tags=["automation", "shorts", title, "youtubeshort", "facts", "config"],
            excel_path=excel_path,
            video_id=video_id
        )

if __name__ == "__main__":
    # List of channels to choose from
    channels = [
        "https://www.youtube.com/@Chhota_Blast_09",
        "https://www.youtube.com/@FlixIQ",
        "https://www.youtube.com/@Zynfo01",
        "https://www.youtube.com/@Factrin25",
        "https://www.youtube.com/@AnuFacto-k9s"
    ]

    excel_path = "video_tracker.xlsx"
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
        exit()

    # Schedule uploads
    schedule_uploads(video_data, excel_path)