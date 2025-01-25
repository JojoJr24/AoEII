import pyttsx3

engine = pyttsx3.init()
voices = engine.getProperty('voices')

for voice in voices:
    print(f"ID: {voice.id}")
    print(f"Nombre: {voice.name}")
    print(f"Idioma: {voice.languages}")
    print("-" * 30)