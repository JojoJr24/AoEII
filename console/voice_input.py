import os
import wave
import tempfile
import numpy as np
import sounddevice as sd
from pocketsphinx import LiveSpeech
import whisper
import curses

# Pocketsphinx configuration for keyword detection
KEYWORD = "hey google"  # Keyword to detect
THRESHOLD = 1e-20       # Adjust threshold for detection (smaller = more sensitive)

speech = LiveSpeech(
    lm=False,                # Don't use full language model
    keyphrase=KEYWORD,       # Define the keyword
    kws_threshold=THRESHOLD, # Sensitivity
    dic=os.path.join("/usr/share/pocketsphinx/model/en-us/cmudict-en-us.dict")  # Path to dictionary
)

# Audio recording configuration
RATE = 16000
RECORD_SECONDS = 5

# Whisper configuration
MODEL_NAME = "tiny"  # Available models: tiny, base, small, medium, large
whisper_model = whisper.load_model(MODEL_NAME)

def record_audio(duration):
    """
    Records audio from the microphone for a defined time using sounddevice.
    """
    print("Recording...")
    try:
        audio_data = sd.rec(int(duration * RATE), samplerate=RATE, channels=1, dtype='int16')
        sd.wait()
        return audio_data.flatten()
    except Exception as e:
        print(f"Error during recording: {e}")
        return None

def transcribe_audio(audio_data):
    """
    Uses Whisper to transcribe audio data.
    """
    print("Transcribing audio with Whisper...")
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
        temp_audio_file = tmp_file.name
        with wave.open(temp_audio_file, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(RATE)
            wf.writeframes(audio_data.tobytes())
        result = whisper_model.transcribe(temp_audio_file, fp16=False)  # Use CPU
        os.remove(temp_audio_file)
        return result['text']

def record_and_transcribe(stdscr):
    """
    Listens for the wake word, records audio, and transcribes it using Whisper.
    """
    try:
        stdscr.addstr(stdscr.getmaxyx()[0] - 4, 1, f"Listening for keyword: '{KEYWORD}'...")
        stdscr.refresh()
        for phrase in speech:
            stdscr.addstr(stdscr.getmaxyx()[0] - 4, 1, "Keyword detected. Recording...")
            stdscr.refresh()
            
            # Record audio after detecting the keyword
            audio_data = record_audio(RECORD_SECONDS)
            if audio_data is None:
                return "Error during recording"
            
            stdscr.addstr(stdscr.getmaxyx()[0] - 4, 1, "Transcribing...")
            stdscr.refresh()
            
            # Transcribe the recorded audio
            transcription = transcribe_audio(audio_data)
            return transcription
    except Exception as e:
        return f"Error during recording or transcription: {e}"
    finally:
        stdscr.addstr(stdscr.getmaxyx()[0] - 4, 1, "                                            ")
        stdscr.refresh()

if __name__ == '__main__':
    def test_voice_input(stdscr):
        curses.curs_set(0)
        transcription = record_and_transcribe(stdscr)
        stdscr.addstr(1, 1, f"Transcription: {transcription}")
        stdscr.refresh()
        stdscr.getch()
    curses.wrapper(test_voice_input)
