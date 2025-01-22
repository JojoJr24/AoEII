import os
import numpy as np
import sounddevice as sd
import whisper
import torch

RATE = 16000
CHANNELS = 1
BLOCK_SIZE = 512  # Changed to match Silero VAD requirements

def record_audio_with_vad():
    try:
        vad_model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                                        model='silero_vad',
                                        force_reload=True)
        vad_model.eval()
        
        audio_buffer = []
        silent_blocks = 0
        max_silence_duration = int(RATE / BLOCK_SIZE) * 2  # 2 seconds of silence
        min_speech_duration = int(RATE * 0.5 / BLOCK_SIZE)  # 0.5 seconds of speech
        
        with sd.InputStream(samplerate=RATE, channels=CHANNELS, dtype=np.float32) as stream:
            while True:
                audio_chunk, _ = stream.read(BLOCK_SIZE)
                audio_chunk = audio_chunk.flatten()
                
                # Convert to torch tensor
                tensor_chunk = torch.from_numpy(audio_chunk).unsqueeze(0)
                
                speech_prob = vad_model(tensor_chunk, RATE).item()
                is_speech = speech_prob > 0.5
                
                if is_speech:
                    print("Habla detectada, grabando...")
                    audio_buffer.append(audio_chunk)
                    silent_blocks = 0
                else:
                    silent_blocks += 1
                    if len(audio_buffer) > 0:
                        audio_buffer.append(audio_chunk)
                
                if len(audio_buffer) >= min_speech_duration and silent_blocks >= max_silence_duration:
                    print("Silencio detectado, terminando grabación...")
                    break
                    
        return np.concatenate(audio_buffer) if audio_buffer else None
        
    except Exception as e:
        print(f"Error durante la grabación con VAD: {e}")
        return None

def transcribe_audio(audio_data):
    try:
        temp_audio_path = "temp_audio.wav"
        sd.write(temp_audio_path, audio_data, RATE)
        
        model = whisper.load_model("tiny")
        result = model.transcribe(temp_audio_path, fp16=False, language="es")
        
        os.remove(temp_audio_path)
        return result.get("text", "")
    except Exception as e:
        print(f"Error durante la transcripción: {e}")
        return None

if __name__ == '__main__':
    print("Iniciando sistema de grabación y transcripción...")
    audio_data = record_audio_with_vad()
    if audio_data is not None:
        transcription = transcribe_audio(audio_data)
        if transcription:
            print(f"Transcripción: {transcription}")
        else:
            print("No se pudo obtener la transcripción.")
    else:
        print("No se pudo grabar audio.")