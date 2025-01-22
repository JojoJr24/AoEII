import whisper
import tempfile
import os
import curses

def record_and_transcribe(stdscr):
    """Records audio from the microphone and transcribes it using Whisper."""
    try:
        stdscr.addstr(stdscr.getmaxyx()[0] - 4, 1, "Recording... Press Enter to stop.")
        stdscr.refresh()
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            temp_audio_file = tmp_file.name
        
        # Use arecord to record audio
        os.system(f"arecord -d 5 -f S16_LE -r 16000 {temp_audio_file}")
        
        stdscr.addstr(stdscr.getmaxyx()[0] - 4, 1, "Transcribing...")
        stdscr.refresh()
        
        model = whisper.load_model("base")
        result = model.transcribe(temp_audio_file)
        transcription = result["text"]
        
        os.remove(temp_audio_file)
        
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
