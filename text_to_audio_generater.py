import re
import asyncio
import edge_tts
import json
from deep_translator import GoogleTranslator

# ---------------------------
# Helper functions
# ---------------------------

def clean_transcript(text):
    """
    Clean transcript from multiple formats:
    - WEBVTT format
    - YouTube JSON3 format
    - Plain text with timestamps
    """
    
    # Try to parse as JSON first (YouTube JSON3 format)
    try:
        data = json.loads(text)
        if 'events' in data:
            return parse_youtube_json3(data)
    except (json.JSONDecodeError, KeyError):
        pass
    
    # Otherwise treat as WEBVTT or plain text
    return parse_webvtt(text)


def parse_youtube_json3(data):
    """Parse YouTube JSON3 subtitle format."""
    transcript_parts = []
    
    for event in data.get('events', []):
        if 'segs' in event:
            for seg in event['segs']:
                text = seg.get('utf8', '').strip()
                # Skip newlines and empty segments
                if text and text != '\n':
                    transcript_parts.append(text)
    
    # Join all parts and clean up
    full_text = ' '.join(transcript_parts)
    # Remove extra spaces
    full_text = ' '.join(full_text.split())
    
    return full_text


def parse_webvtt(text):
    """Parse WEBVTT format or plain text with timestamps."""
    # Remove WEBVTT header and metadata
    text = re.sub(r'WEBVTT.*?\n', '', text)
    text = re.sub(r'Kind:.*?\n', '', text)
    text = re.sub(r'Language:.*?\n', '', text)
    
    # Remove timestamp lines (00:00:00.080 --> 00:00:01.750)
    text = re.sub(r'\d{2}:\d{2}:\d{2}\.\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}\.\d{3}.*?\n', '', text)
    
    # Remove simple timestamps [00:00:27]
    text = re.sub(r'\[\d{2}:\d{2}:\d{2}\]', '', text)
    
    # Remove alignment and position tags
    text = re.sub(r'align:\w+\s+position:\d+%', '', text)
    
    # Remove XML-like tags <00:00:00.320><c> text </c>
    text = re.sub(r'<[\d:.]+>', '', text)
    text = re.sub(r'</?c>', '', text)
    
    # Split into lines and remove duplicates while preserving order
    lines = text.split('\n')
    seen = set()
    unique_lines = []
    
    for line in lines:
        line = line.strip()
        if line and line not in seen:
            seen.add(line)
            unique_lines.append(line)
    
    # Join into single text
    cleaned = ' '.join(unique_lines)
    
    # Remove extra spaces
    cleaned = ' '.join(cleaned.split())
    
    return cleaned


def save_cleaned_transcript(text, filename="transcript_shorts.txt"):
    """Save cleaned transcript to file."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"✅ Cleaned transcript saved as: {filename}")
        return filename
    except Exception as e:
        print(f"❌ Error saving transcript: {e}")
        return None


def translate_text(text, target_language="hi"):
    """
    Translate text using Google Translate (FREE).
    
    Args:
        text: Text to translate
        target_language: Language code (hi=Hindi, es=Spanish, fr=French, etc.)
    
    Returns:
        Translated text
    """
    try:
        max_length = 4500
        
        if len(text) > max_length:
            sentences = re.split(r'(?<=[.!?])\s+', text)
            chunks = []
            current_chunk = ""
            
            for sentence in sentences:
                if len(current_chunk) + len(sentence) < max_length:
                    current_chunk += " " + sentence
                else:
                    chunks.append(current_chunk.strip())
                    current_chunk = sentence
            
            if current_chunk:
                chunks.append(current_chunk.strip())
            
            translated_chunks = []
            for i, chunk in enumerate(chunks):
                print(f"  Translating chunk {i+1}/{len(chunks)}...")
                translator = GoogleTranslator(source='auto', target=target_language)
                translated = translator.translate(chunk)
                translated_chunks.append(translated)
            
            translated_text = " ".join(translated_chunks)
        else:
            translator = GoogleTranslator(source='auto', target=target_language)
            translated_text = translator.translate(text)
        
        print(f"✅ Translation to {target_language} completed!")
        return translated_text
        
    except Exception as e:
        print(f"❌ Translation error: {e}")
        return None


async def generate_voice(text, output_file="ai_dub.mp3", voice="hi-IN-SwaraNeural"):
    """
    Generate realistic AI voice using edge_tts.
    
    Voices examples:
        hi-IN-SwaraNeural  → Hindi Female
        hi-IN-MadhurNeural → Hindi Male
        es-ES-ElviraNeural → Spanish Female
        fr-FR-DeniseNeural → French Female
    """
    try:
        communicate = edge_tts.Communicate(text, voice=voice)
        await communicate.save(output_file)
        print(f"✅ Voice generated successfully: {output_file}")
        return output_file
    except Exception as e:
        print("❌ Voice generation error:", e)
        return None


def create_dubbed_audio(
    transcript_text, 
    translate_to="hi",
    output_audio="ai_dub.mp3", 
    voice="hi-IN-SwaraNeural",
    save_transcript=True
):
    """
    Complete workflow: Clean transcript, translate, and generate audio.
    
    Args:
        transcript_text: Raw transcript text
        translate_to: Language code ("hi" for Hindi, "es" for Spanish, etc.)
        output_audio: Output audio filename
        voice: TTS voice name
        save_transcript: Whether to save cleaned transcript
    
    Returns:
        Dictionary with audio file path and transcript info
    """
    result = {
        'audio_file': None,
        'transcript_file': None,
        'translated': False
    }
    
    # Step 1: Clean transcript
    print("🧹 Cleaning transcript...")
    cleaned_text = clean_transcript(transcript_text)
    
    if not cleaned_text:
        print("❌ No text found after cleaning!")
        return result
    
    print(f"\n📝 Cleaned text preview:")
    print("="*60)
    print(cleaned_text[:200] + "...")
    print("="*60)
    print(f"\nText length: {len(cleaned_text)} characters")
    print(f"Word count: {len(cleaned_text.split())} words\n")
    
    # Step 2: Save cleaned transcript
    if save_transcript:
        result['transcript_file'] = save_cleaned_transcript(cleaned_text)
    
    # Step 3: Translate
    print(f"\n🌍 Translating to {translate_to}...")
    translated_text = translate_text(cleaned_text, translate_to)
    
    if not translated_text:
        print("⚠️ Translation failed, cannot proceed")
        return result
    
    result['translated'] = True
    
    # Save translated version
    if save_transcript:
        trans_filename = f"transcript_shorts_{translate_to}.txt"
        save_cleaned_transcript(translated_text, trans_filename)
    
    print(f"\n📝 Translated text preview:")
    print("="*60)
    print(translated_text[:200] + "...")
    print("="*60 + "\n")
    
    # Step 4: Generate audio
    print("🎙 Generating voice audio...")
    result['audio_file'] = asyncio.run(generate_voice(translated_text, output_audio, voice=voice))
    
    return result


# ---------------------------
# Example Usage
# ---------------------------
def dub_audio():
    with open('yt_transcript.txt', 'r', encoding='utf-8') as f:
        transcript = f.read()
    
    # Hindi audio with translation
    print("=" * 70)
    print("Creating Hindi Dubbed Audio")
    print("=" * 70)
    result = create_dubbed_audio(
        transcript,
        translate_to="hi",
        output_audio="hindi_dub.mp3",
        voice="hi-IN-SwaraNeural"
    )
    
    if result['audio_file']:
        print(f"\n🎉 Complete!")
        print(f"Audio: {result['audio_file']}")
        print(f"Transcript: {result['transcript_file']}")
        print(f"Translated: {result['translated']}")

