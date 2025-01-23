import os
import numpy as np
import sounddevice as sd
import soundfile as sf
import io
import torch
from faster_whisper import WhisperModel
import curses
import threading
import queue

RATE = 16000
CHANNELS = 1
BLOCK_SIZE = 512

def transcribe_audio(audio_queue, transcription_queue, model_size="tiny", language="es"):
    model = WhisperModel(model_size, device="cpu")
    while True:
        audio_data = audio_queue.get()
        if audio_data is None:
            break
        
        # Use BytesIO to store audio data in memory
        audio_buffer = io.BytesIO()
        sf.write(audio_buffer, audio_data, RATE, format='WAV')
        audio_buffer.seek(0)  # Rewind to the beginning of the buffer
        
        segments, _ = model.transcribe(audio_buffer, language=language)
        transcription = " ".join([segment.text for segment in segments])
        transcription_queue.put(transcription)

def record_and_transcribe(stdscr):
    vad_model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                                    model='silero_vad',
                                    force_reload=False)
    vad_model.eval()
    
    audio_queue = queue.Queue()
    transcription_queue = queue.Queue()
    transcription_thread = threading.Thread(target=transcribe_audio, args=(audio_queue, transcription_queue))
    transcription_thread.daemon = True
    transcription_thread.start()
    
    audio_buffer = []
    silent_blocks = 0
    max_silence_duration = int(RATE * 3 / BLOCK_SIZE)
    min_speech_duration = int(RATE * 0.1 / BLOCK_SIZE)
    
    full_transcription = ""
    
    try:
        with sd.InputStream(samplerate=RATE, channels=CHANNELS, dtype=np.float32) as stream:
            while True:
                audio_chunk, _ = stream.read(BLOCK_SIZE)
                audio_chunk = audio_chunk.flatten()
                tensor_chunk = torch.from_numpy(audio_chunk).unsqueeze(0)
                speech_prob = vad_model(tensor_chunk, RATE).item()
                
                is_speech = speech_prob > 0.5
                
                if is_speech:
                    audio_buffer.append(audio_chunk)
                    silent_blocks = 0
                else:
                    silent_blocks += 1
                    if len(audio_buffer) > 0:
                        audio_queue.put(np.concatenate(audio_buffer))
                        audio_buffer = []
                    
                if silent_blocks >= max_silence_duration:
                    break
                
                # Check for new transcriptions
                while not transcription_queue.empty():
                    transcription = transcription_queue.get()
                    full_transcription += transcription + " "
                    stdscr.addstr(stdscr.getmaxyx()[0] - 1, 1, f"Transcripción: {full_transcription}")
                    stdscr.refresh()
                    
        # Process any remaining audio
        if len(audio_buffer) > 0:
            audio_queue.put(np.concatenate(audio_buffer))
        
        audio_queue.put(None)  # Signal the transcription thread to stop
        transcription_thread.join()
        
        return full_transcription.strip()
    except Exception as e:
        error_message = f"Error durante la grabación con VAD: {e}"
        max_length = stdscr.getmaxyx()[1] - 2
        if len(error_message) > max_length:
            error_message = error_message[:max_length] + "..."
        stdscr.addstr(stdscr.getmaxyx()[0] - 1, 1, error_message)
        stdscr.refresh()
        return "Error during recording"
