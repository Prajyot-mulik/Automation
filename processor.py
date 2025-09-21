import os
import subprocess
import math
import json
import random
import tempfile
from PIL import Image, ImageDraw, ImageFont

def get_media_duration(path):
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    info = json.loads(result.stdout)
    return float(info["format"]["duration"])

def pick_random_reaction(reaction_folder):
    files = [f for f in os.listdir(reaction_folder) if f.lower().endswith((".mp4", ".mov", ".mkv", ".avi"))]
    if not files:
        return None
    return os.path.join(reaction_folder, random.choice(files))

def generate_credit_png(text, bar_height):
    video_width = 1080
    try:
        font = ImageFont.truetype("arial.ttf", 36)  # 36pt Arial
    except IOError:
        font = ImageFont.load_default()  # Fallback to default if Arial not found
    dummy_img = Image.new("RGBA", (1, 1), (255, 255, 255, 255))
    draw = ImageDraw.Draw(dummy_img)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    img = Image.new("RGBA", (video_width, bar_height), (255, 255, 255, 255))  # White background, full width
    draw = ImageDraw.Draw(img)
    x_pos = (video_width - text_width) // 2
    y_pos = (bar_height - text_height) // 2
    draw.text((x_pos, y_pos), text, font=font, fill=(0, 0, 0, 255))  # Black text

    temp_path = os.path.join(tempfile.gettempdir(), "credit_overlay.png")
    img.save(temp_path, "PNG")
    return temp_path

def process_video(input_path, output_path, semitones=-0.5, bass_gain=4.9, volume_boost=1.3, credit_text=""):
    factor = math.pow(2.0, semitones / 12.0)
    bar_height = 140  # White bar height

    print(f"Processing input: {input_path}")
    print(f"Output path: {output_path}")

    credit_image_path = generate_credit_png(f"Video Credit: {credit_text}", bar_height)

    bg_music_path = os.path.join("background_music", "back.mp3")
    reaction_folder = "Reaction"
    reaction_video = pick_random_reaction(reaction_folder)
    print(f"Reaction video: {reaction_video}")

    middle_screens = "middle_screens"
    first_path = os.path.join(middle_screens, "first.mp4")
    last_path = os.path.join(middle_screens, "last.mp4")
    film_path = os.path.join(middle_screens, "film.mp4")
    click_path = os.path.join(middle_screens, "click.mp3")

    # Ensure middle_screens videos and click sound exist
    if not (os.path.exists(first_path) and os.path.exists(last_path) and os.path.exists(film_path) and os.path.exists(click_path)):
        raise FileNotFoundError("Missing first.mp4, last.mp4, film.mp4, or click.mp3 in middle_screens directory")

    video_duration = get_media_duration(input_path)
    first_duration = get_media_duration(first_path)
    last_duration = get_media_duration(last_path)
    film_duration = get_media_duration(film_path)
    click_duration = get_media_duration(click_path)
    print(f"Input video duration: {video_duration}s")
    print(f"first.mp4 duration: {first_duration}s")
    print(f"last.mp4 duration: {last_duration}s")
    print(f"film.mp4 duration: {film_duration}s")
    print(f"click.mp3 duration: {click_duration}s")

    # Calculate split point (middle of the video)
    split_point = video_duration / 2.0
    print(f"Split point: {split_point}s")

    # Trim last 1 second of original video
    trimmed_duration = video_duration - 1.0
    if trimmed_duration <= 0:
        raise ValueError("Video duration too short to trim 1 second")
    print(f"Trimmed duration (after removing 1s): {trimmed_duration}s")

    # Split main video into two parts, apply audio effects, and ensure consistent video resolution
    first_half_filter = (
        f"[0:v]trim=0:{split_point},setpts=PTS-STARTPTS,scale=1080:1920:force_original_aspect_ratio=decrease,"
        f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1:1[first_half];"
        f"[0:a]atrim=0:{split_point},asetpts=PTS-STARTPTS,asetrate=44100*{factor},"
        f"aresample=44100,atempo={1/factor},bass=g={bass_gain},acompressor,volume={volume_boost}[first_half_a]"
    )

    second_half_filter = (
        f"[0:v]trim={split_point}:{trimmed_duration},setpts=PTS-STARTPTS,scale=1080:1920:force_original_aspect_ratio=decrease,"
        f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1:1[second_half];"
        f"[0:a]atrim={split_point}:{trimmed_duration},asetpts=PTS-STARTPTS,asetrate=44100*{factor},"
        f"aresample=44100,atempo={1/factor},bass=g={bass_gain},acompressor,volume={volume_boost}[second_half_a]"
    )

    # Process middle_screens videos, scaling to match input video resolution (1080x1920) with padding
    first_middle_filter = (
        f"[1:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1:1,setpts=PTS-STARTPTS[middle_first];"
        f"[1:a]atempo=1.0[middle_first_a]"
    )

    last_middle_filter = (
        f"[2:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1:1,setpts=PTS-STARTPTS[middle_last];"
        f"[2:a]atempo=1.0[middle_last_a]"
    )

    # Concatenate video and audio streams
    concat_filter = (
        f"[first_half][first_half_a][middle_first][middle_first_a][second_half][second_half_a]"
        f"[middle_last][middle_last_a]concat=n=4:v=1:a=1[concat_v][concat_a]"
    )

    # Calculate total duration before film_filter
    total_duration = trimmed_duration + first_duration + last_duration
    print(f"Total output duration: {total_duration}s")

    # Process film.mp4 for periodic overlay (every 5 seconds, 1-second duration, 20% opacity)
    film_index = 3
    film_filter = (
        f"[{film_index}:v]loop=loop=-1:size=ceil({total_duration}/{film_duration}):start=0,"
        f"trim=duration={total_duration},setpts=PTS-STARTPTS,scale=1080:1920:force_original_aspect_ratio=decrease,"
        f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1:1,format=yuva420p,colorkey=black:0.3:0.1,"
        f"colorchannelmixer=aa=0.2[film_scaled];"
        f"[vid_with_react][film_scaled]overlay=0:0:enable='lt(mod(t,5),1)':shortest=1[vid_with_film]"
    )
    next_index = film_index + 1  # Start after film_index

    # Process click.mp3 for periodic playback (every 3 seconds)
    click_index = next_index
    click_filter = (
        f"[{click_index}:a]aloop=loop=-1:size=ceil({total_duration}/{click_duration}),"
        f"atrim=duration={total_duration},adelay=0|0,volume=3.0,"
        f"aselect='between(mod(t,3),0,{click_duration})',asetpts=PTS-STARTPTS[click_audio]"
    )
    next_index += 1

    if os.path.exists(bg_music_path):
        bg_music_index = next_index
        bg_music_filter = (
            f"[{bg_music_index}:a]aloop=loop=-1:size=2e+09,volume=0.3,apad,"
            f"atrim=duration={total_duration}[bg_audio];"
            f"[concat_a][bg_audio][click_audio]amix=inputs=3:dropout_transition=0,alimiter[aout]"
        )
        audio_map = "[aout]"
        audio_inputs = ["-i", bg_music_path, "-i", click_path]
        next_index += 1
    else:
        bg_music_filter = (
            f"[concat_a][click_audio]amix=inputs=2:dropout_transition=0,alimiter[aout]"
        )
        audio_map = "[aout]"
        audio_inputs = ["-i", click_path]
    print(f"Background music: {bg_music_path if os.path.exists(bg_music_path) else 'None'}")
    print(f"Click sound: {click_path}")

    hdr_filter = "eq=contrast=1.2:brightness=0.01:saturation=1.25,curves=preset=increase_contrast,unsharp=5:5:0.5:5:5:0.0"

    if reaction_video:
        reaction_index = next_index
        scale_factor = round(random.uniform(0.35, 0.4), 3)  # Reaction video size 35-40%
        reaction_filter = (
            f"[concat_v]{hdr_filter}[main_vid];"
            f"[{reaction_index}:v]scale=iw*{scale_factor}:-1,setsar=1:1,trim=duration={total_duration},setpts=PTS-STARTPTS[react_vid];"
            f"[main_vid][react_vid]overlay=W-w:H-h[vid_with_react]"
        )
        video_input_label = "[vid_with_react]"
        video_inputs = ["-i", reaction_video]
        next_index += 1
    else:
        reaction_filter = f"[concat_v]{hdr_filter}[vid_with_react]"
        video_input_label = "[vid_with_react]"
        video_inputs = []

    credit_input_index = next_index

    # Apply fade animation to the credit bar overlay (full white bar with text)
    credit_filter = (
        f"[{credit_input_index}:v]trim=duration={total_duration},setpts=PTS-STARTPTS,fade=t=in:st=0:d=1,fade=t=out:st={total_duration-1}:d=1[credit_animated];"
        f"[vid_with_film][credit_animated]overlay=0:0:shortest=1[vout]"
    )

    filter_chain = ";".join([first_half_filter, second_half_filter,
                             first_middle_filter, last_middle_filter, concat_filter,
                             click_filter, bg_music_filter, reaction_filter, film_filter, credit_filter])

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-i", first_path,
        "-i", last_path,
        "-i", film_path,
        *audio_inputs,
        *video_inputs,
        "-loop", "1", "-i", credit_image_path,
        "-filter_complex", filter_chain,
        "-map", "[vout]","-map", audio_map,
        "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
        "-c:a", "aac", "-b:a", "192k",
        output_path
    ]

    print(f"Executing FFmpeg command: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    print(f"✅ Processed with pitch change, centered credit text, HDR, reaction video, periodic film.mp4 overlay, periodic click.mp3, middle_screens first.mp4 and last.mp4 — saved to {output_path}")
    # Clean up temporary credit image
    if os.path.exists(credit_image_path):
        os.remove(credit_image_path)