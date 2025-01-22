import os
import wave
import tempfile
import numpy as np
import sounddevice as sd
import curses
import json
from vosk import Model, KaldiRecognizer

# Vosk configuration
MODEL_PATH = "vosk-model-small-es-0.42"  # Path to the Vosk model
KEYWORDS = ["hola", "adiós", "gracias", "hey google"]  # Keywords to detect

# Audio recording configuration
RATE = 16000
RECORD_SECONDS = 5

# Initialize Vosk model
if not MODEL_PATH:
    raise ValueError("You must specify the path to the Vosk model.")
model = Model(MODEL_PATH)

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

def transcribe_audio(audio_data, keywords):
    """
    Transcribes audio data using Vosk and detects specific keywords.
    """
    print("Transcribing audio with Vosk...")
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
        temp_audio_file = tmp_file.name
        with wave.open(temp_audio_file, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(RATE)
            wf.writeframes(audio_data.tobytes())
        
        # Open the audio file
        wf = wave.open(temp_audio_file, "rb")
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 16000:
            raise ValueError("Audio file must be mono, 16-bit, 16kHz.")

        # Configure the recognizer with keywords
        recognizer = KaldiRecognizer(model, wf.getframerate(), f'["{" ".join(keywords)}", "[unk]"]')

        # Process the audio
        detected_keywords = []
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "")
                for keyword in keywords:
                    if keyword in text:
                        detected_keywords.append(keyword)

        # Close the audio file
        wf.close()
        os.remove(temp_audio_file)

        # Results
        final_result = recognizer.FinalResult()
        return {
            "transcription": final_result,
            "detected_keywords": list(set(detected_keywords)),
        }

def record_and_transcribe(stdscr):
    """
    Listens for the wake word, records audio, and transcribes it using Vosk.
    """
    try:
        stdscr.addstr(stdscr.getmaxyx()[0] - 4, 1, f"Listening for keywords: '{', '.join(KEYWORDS)}'...")
        stdscr.refresh()
        
        # Record audio
        audio_data = record_audio(RECORD_SECONDS)
        if audio_data is None:
            return "Error during recording"
        
        stdscr.addstr(stdscr.getmaxyx()[0] - 4, 1, "Transcribing...")
        stdscr.refresh()
        
        # Transcribe the recorded audio
        result = transcribe_audio(audio_data, KEYWORDS)
        if result and result["detected_keywords"]:
            return result["transcription"].get("text", "")
        else:
            return ""
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
