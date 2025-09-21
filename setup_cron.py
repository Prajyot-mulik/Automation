import os
from crontab import CronTab

def setup_cron_jobs():
    """Set up cron jobs for downloads and uploads."""
    # Get absolute path to the script directory
    script_dir = os.path.abspath(os.path.dirname(__file__))
    python_path = "/usr/bin/python3"  # Adjust if your Python is elsewhere
    wrapper_script = os.path.join(script_dir, "download_wrapper.sh")

    # Make wrapper script executable
    os.chmod(wrapper_script, 0o755)

    # Initialize cron for the current user
    cron = CronTab(user=True)

    # Remove existing jobs to avoid duplicates
    cron.remove_all(comment="video_automation_download")
    for i in range(7):
        cron.remove_all(comment=f"video_automation_upload_{i}")

    # Schedule download wrapper at 5 AM IST
    download_job = cron.new(
        command=f"/bin/bash {wrapper_script} >> {os.path.join(script_dir, 'logs', 'download_wrapper.log')} 2>&1",
        comment="video_automation_download"
    )
    download_job.setall("0 5 * * *")  # 5 AM daily

    # Schedule uploads at 8 AM, 9 AM, 3 PM, 4 PM, 5 PM, 6 PM, 7 PM IST
    upload_times = ["8:00", "9:00", "15:00", "16:00", "17:00", "18:00", "19:00"]
    for i, upload_time in enumerate(upload_times):
        hour, minute = upload_time.split(":")
        upload_job = cron.new(
            command=f"{python_path} {os.path.join(script_dir, 'upload_single.py')} {i} >> {os.path.join(script_dir, 'logs', 'upload_{i}.log')} 2>&1",
            comment=f"video_automation_upload_{i}"
        )
        upload_job.setall(f"{minute} {hour} * * *")

    # Write cron jobs
    cron.write()
    print("✅ Cron jobs scheduled:")
    print("- Download attempts starting at 5 AM daily (with retries until 8 AM)")
    for i, time in enumerate(upload_times):
        print(f"- Upload {i+1} at {time} daily")

if __name__ == "__main__":
    # Create logs directory
    os.makedirs("logs", exist_ok=True)
    setup_cron_jobs()