from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip, vfx
from pydub import AudioSegment
import os

# ----------------------------------
# ⚙️ Utility: Change audio speed
# ----------------------------------
def change_audio_speed(input_audio_path, speed_factor, output_path):
    """
    Change audio speed while roughly preserving pitch.
    """
    try:
        audio = AudioSegment.from_file(input_audio_path)
        new_frame_rate = int(audio.frame_rate * speed_factor)
        adjusted = audio._spawn(audio.raw_data, overrides={"frame_rate": new_frame_rate})
        adjusted = adjusted.set_frame_rate(audio.frame_rate)
        adjusted.export(output_path, format="mp3")
        return output_path
    except Exception as e:
        raise RuntimeError(f"change_audio_speed error: {e}")


# ----------------------------------
# 🎬 Main Function: Video Editor
# ----------------------------------
def video_edit(choose_bg=None, voice_volume=1.8, bg_volume=0.08):
    """
    Combine video, voice, and optional background music.

    Args:
        choose_bg: Path to custom background music file.
                   If None or missing, default = 'blade runner 2055.m4a'
        voice_volume: Volume multiplier for voice (1.0 = normal)
        bg_volume: Volume multiplier for background (1.0 = same as source)
    """
    try:
        video_path = "yt_video.mp4"
        voice_path = "hindi_dub_tone.mp3"
        default_bg = "blade runner.mp3"
        output_path = "output_video.mp4"

        # ✅ Automatically use default background if not provided
        if not choose_bg or not os.path.exists(choose_bg):
            print("⚠️ Background not provided or missing, using default:", default_bg)
            choose_bg = default_bg

        # ✅ Check required files
        if not os.path.exists(video_path):
            return f"❌ Error: video file not found: {video_path}"
        if not os.path.exists(voice_path):
            return f"❌ Error: voice file not found: {voice_path}"
        if not os.path.exists(choose_bg):
            return f"❌ Error: background file not found: {choose_bg}"

        # 🎞️ Load clips
        video = VideoFileClip(video_path)
        voice = AudioFileClip(voice_path)

        video_duration = video.duration
        voice_duration = voice.duration
        print(f"🎬 Video: {video_duration:.2f}s | 🎙 Voice: {voice_duration:.2f}s")

        # ⏱ Match durations via average
        target_duration = (video_duration + voice_duration) / 2.0
        print(f"⏰ Target duration: {target_duration:.2f}s")

        video_speed_factor = video_duration / target_duration
        voice_speed_factor = voice_duration / target_duration
        print(f"⚡ Speed factors → Video: {video_speed_factor:.3f}, Voice: {voice_speed_factor:.3f}")

        # 🌀 Adjust video speed
        adjusted_video = video.fx(vfx.speedx, factor=video_speed_factor)

        # 🎧 Adjust voice speed
        temp_voice_path = "temp_voice.mp3"
        change_audio_speed(voice_path, voice_speed_factor, temp_voice_path)
        adjusted_voice = AudioFileClip(temp_voice_path).volumex(voice_volume)
        print(f"🎚️ Voice volume set to {voice_volume}x")

        # 🎵 Background music
        bg_clip = AudioFileClip(choose_bg)
        if bg_clip.duration > target_duration:
            bg_clip = bg_clip.subclip(0, target_duration)
        else:
            bg_clip = bg_clip.fx(vfx.loop, duration=target_duration)
        bg_clip = bg_clip.volumex(bg_volume)
        print(f"🎶 Background: {os.path.basename(choose_bg)} | Volume: {bg_volume}x")

        # 🎛️ Mix voice + background
        final_audio = CompositeAudioClip([adjusted_voice, bg_clip])

        # 🧩 Combine with video
        final_video = adjusted_video.set_audio(final_audio).subclip(0, target_duration)

        # 💾 Export final
        print("📦 Rendering final video...")
        final_video.write_videofile(output_path, codec="libx264", audio_codec="aac")
        print(f"✅ Video editing completed: {output_path}")

        # 🧹 Cleanup
        for clip in [video, voice, adjusted_voice, adjusted_video, bg_clip, final_audio, final_video]:
            try:
                clip.close()
            except:
                pass

        if os.path.exists(temp_voice_path):
            os.remove(temp_voice_path)

        return f"✅ Output saved as '{output_path}'"

    except Exception as e:
        if os.path.exists("temp_voice.mp3"):
            try:
                os.remove("temp_voice.mp3")
            except:
                pass
        return f"❌ Error during video editing: {e}"


# ----------------------------------
# 🧪 Example Usage
# ----------------------------------
