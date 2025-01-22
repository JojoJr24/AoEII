import os
import pyaudio
import wave
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

# PyAudio configuration for recording audio after keyword detection
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME = "detected_audio.wav"

# Whisper configuration
MODEL_NAME = "tiny"  # Available models: tiny, base, small, medium, large
whisper_model = whisper.load_model(MODEL_NAME)

def record_audio(filename, duration):
    """
    Records audio from the microphone for a defined time.
    """
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True, frames_per_buffer=CHUNK)
    frames = []

    for _ in range(0, int(RATE / CHUNK * duration)):
        data = stream.read(CHUNK)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    audio.terminate()

    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

def transcribe_audio(filename):
    """
    Uses Whisper to transcribe an audio file.
    """
    result = whisper_model.transcribe(filename, fp16=False)  # Use CPU
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
            record_audio(WAVE_OUTPUT_FILENAME, RECORD_SECONDS)
            
            stdscr.addstr(stdscr.getmaxyx()[0] - 4, 1, "Transcribing...")
            stdscr.refresh()
            
            # Transcribe the recorded audio
            transcription = transcribe_audio(WAVE_OUTPUT_FILENAME)
            os.remove(WAVE_OUTPUT_FILENAME)
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
