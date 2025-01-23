import os
import numpy as np
import sounddevice as sd
import soundfile as sf
import torch
from faster_whisper import WhisperModel
import curses

RATE = 16000
CHANNELS = 1
BLOCK_SIZE = 512  # Changed to match Silero VAD requirements

def record_and_transcribe(stdscr):
    try:
        vad_model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                                        model='silero_vad',
                                        force_reload=False)
        vad_model.eval()
        
        audio_buffer = []
        silent_blocks = 0
        max_silence_duration = int(RATE * 3 / BLOCK_SIZE)  # 3 seconds of silence
        min_speech_duration = int(RATE * 0.1 / BLOCK_SIZE)  # 0.1 seconds of speech
        
        with sd.InputStream(samplerate=RATE, channels=CHANNELS, dtype=np.float32) as stream:
            while True:
                audio_chunk, _ = stream.read(BLOCK_SIZE)
                audio_chunk = audio_chunk.flatten()
                
                # Convert to torch tensor
                tensor_chunk = torch.from_numpy(audio_chunk).unsqueeze(0)
                
                speech_prob = vad_model(tensor_chunk, RATE).item()
                stdscr.addstr(stdscr.getmaxyx()[0] - 1, 1, f"Speech probability: {speech_prob:.2f}")
                stdscr.refresh()
                is_speech = speech_prob > 0.5
                
                if is_speech:
                    audio_buffer.append(audio_chunk)
                    silent_blocks = 0
                else:
                    silent_blocks += 1
                    if len(audio_buffer) > 0:
                        audio_buffer.append(audio_chunk)
                
                if silent_blocks >= max_silence_duration:
                    stdscr.addstr(stdscr.getmaxyx()[0] - 1, 1, "Silencio detectado, terminando grabación...")
                    stdscr.refresh()
                    break
                    
        audio_data = np.concatenate(audio_buffer) if audio_buffer else None
        if audio_data is not None:
            temp_audio_path = "temp_audio.wav"
            sf.write(temp_audio_path, audio_data, RATE)
            
            model = WhisperModel("tiny", device="cpu")
            segments, _ = model.transcribe(temp_audio_path, language="es")
            transcription = " ".join([segment.text for segment in segments])
            
            os.remove(temp_audio_path)
            stdscr.addstr(stdscr.getmaxyx()[0] - 1, 1, f"Transcripción: {transcription}")
            stdscr.refresh()
            return transcription
        else:
            stdscr.addstr(stdscr.getmaxyx()[0] - 1, 1, "No se pudo grabar audio.")
            stdscr.refresh()
            return "Error during recording"
    except Exception as e:
        error_message = f"Error durante la grabación con VAD: {e}"
        max_length = stdscr.getmaxyx()[1] - 2
        if len(error_message) > max_length:
            error_message = error_message[:max_length] + "..."
        stdscr.addstr(stdscr.getmaxyx()[0] - 1, 1, error_message)
        stdscr.refresh()
        return "Error during recording"
