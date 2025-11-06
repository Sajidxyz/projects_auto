from pydub import AudioSegment
from pydub.effects import speedup
import os

# ---------------------------
# 🎛️ Tone Settings
# ---------------------------
TONE_SETTINGS = {
    "speed": 1.40,         # 1.0 = normal, 1.25 = 25% faster
    "volume_change": 2,    # +dB louder, -dB softer
    "normalize": True,     # Auto normalize volume
    "fade_in": 500,        # in milliseconds
    "fade_out": 500        # in milliseconds
}

# ---------------------------
# Audio Editing Functions
# ---------------------------

def adjust_audio_tone(input_file, output_file=None, settings=None):
    """Apply the tone adjustments in two stages for smoother sound."""
    if settings is None:
        settings = TONE_SETTINGS
    
    try:
        if not output_file:
            name, ext = os.path.splitext(input_file)
            output_file = f"{name}_tone{ext}"
        
        print(f"🎵 Loading: {input_file}")
        audio = AudioSegment.from_file(input_file)

        # --- Step 1: Half speed adjustment ---
        if settings["speed"] != 1.0:
            half_speed = 1 + ((settings["speed"] - 1) / 2)
            print(f"⚡ Step 1 Speed: {half_speed}x")
            audio = speedup(audio, playback_speed=half_speed)

        # --- Step 2: Final adjustment ---
        if settings["speed"] != 1.0:
            print(f"⚡ Step 2 Speed: {settings['speed']}x")
            audio = speedup(audio, playback_speed=settings["speed"] / half_speed)
        
        # Volume
        if settings["volume_change"] != 0:
            print(f"🔊 Volume: {settings['volume_change']}dB")
            audio += settings["volume_change"]
        
        # Normalize
        if settings["normalize"]:
            print(f"📊 Normalizing...")
            audio = audio.normalize()
        
        # Fades
        if settings["fade_in"] > 0:
            print(f"🎚️ Fade In: {settings['fade_in']}ms")
            audio = audio.fade_in(settings["fade_in"])
        
        if settings["fade_out"] > 0:
            print(f"🎚️ Fade Out: {settings['fade_out']}ms")
            audio = audio.fade_out(settings["fade_out"])
        
        # Save
        print(f"💾 Saving to: {output_file}")
        audio.export(output_file, format=output_file.split('.')[-1])
        
        print(f"✅ Done! → {output_file}")
        return output_file
    
    except Exception as e:
        print(f"❌ Error adjusting tone: {e}")
        return None


