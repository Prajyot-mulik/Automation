import sys
from uploader import upload_video

def upload_single(index):
    """Upload a single video based on index from video_data.txt."""
    video_data_file = "video_data.txt"
    excel_path = "video_tracker.xlsx"

    if not os.path.exists(video_data_file):
        print(f"❌ No video data file found at {video_data_file}")
        return

    with open(video_data_file, 'r') as f:
        video_data = [line.strip().split('|') for line in f.readlines()]

    if index >= len(video_data):
        print(f"❌ Invalid index {index}. Only {len(video_data)} videos available.")
        return

    input_path, output_path, video_id, title, description = video_data[index]
    print(f"⬆️ Starting upload for {output_path}")
    upload_video(
        output_path,
        title=f"{title} - Automated Upload #{index+1}",
        description=description,
        tags=["automation", "shorts", title, "youtubeshort", "facts", "config"],
        excel_path=excel_path,
        video_id=video_id
    )

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python upload_single.py <index>")
        sys.exit(1)
    upload_single(int(sys.argv[1]))