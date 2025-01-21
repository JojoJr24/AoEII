import socket
import sys
import os
import time
import threading
import sounddevice as sd
import numpy as np

SOCKET_PATH = '/tmp/tone.sock'

class ToneGenerator:
    def __init__(self, frequency):
        self.frequency = frequency
        self.running = True
        self.sample_rate = 44100
        self.duration = 0.1

    def start(self):
        """Inicia el generador de tono en un hilo separado."""
        threading.Thread(target=self.run, daemon=True).start()

    def run(self):
        """Lógica principal del generador de tono."""
        while self.running:
            if not self.running:
                break
            print(f"Playing tone at {self.frequency} Hz")
            self.play_sound()
            time.sleep(self.duration)

    def update(self, frequency):
        """Actualiza la frecuencia del tono."""
        print(f"Actualizando tono: Frequency={frequency}")
        self.frequency = frequency

    def stop(self):
        """Detiene el generador de tono."""
        self.running = False

    def play_sound(self):
        """Genera y reproduce el sonido del tono."""
        t = np.linspace(0, self.duration, int(self.sample_rate * self.duration), endpoint=False)
        tone = 0.5 * np.sin(2 * np.pi * self.frequency * t)
        sd.play(tone, samplerate=self.sample_rate)
        sd.wait()


def start_server(initial_frequency):
    """Inicia el servidor para controlar el generador de tono."""
    if os.path.exists(SOCKET_PATH):
        os.remove(SOCKET_PATH)

    server_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server_sock.bind(SOCKET_PATH)
    server_sock.listen(1)

    print(f"[Servidor] Generador de tono iniciado con Frequency={initial_frequency}")
    tone_generator = ToneGenerator(initial_frequency)
    tone_generator.start()

    while True:
        conn, _ = server_sock.accept()
        try:
            data = conn.recv(1024).decode('utf-8').strip()
            if data.upper() == 'CERRAR':
                print("[Servidor] Recibido comando de cierre. Terminando servidor.")
                tone_generator.stop()
                conn.close()
                break
            else:
                # Parseamos los parámetros del comando
                try:
                    frequency = int(data)
                    tone_generator.update(frequency)
                    conn.sendall(f"Tono actualizado: Frequency={frequency}\n".encode('utf-8'))
                except ValueError:
                    conn.sendall(b"Error: Formato de comando no valido. Use '<frequency>'.\n")
        except Exception as e:
            print(f"[Servidor] Error procesando la conexión: {e}")
            conn.close()

    server_sock.close()
    if os.path.exists(SOCKET_PATH):
        os.remove(SOCKET_PATH)
    print("[Servidor] Cerrado por completo.")


def send_to_server(command):
    """Envía un comando al servidor."""
    client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client_sock.connect(SOCKET_PATH)
    client_sock.sendall(command.encode('utf-8'))
    response = client_sock.recv(1024).decode('utf-8')
    print("[Cliente] Respuesta del servidor:", response.strip())
    client_sock.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python tone_micro_app.py <frequency> | CERRAR")
        sys.exit(1)

    command = sys.argv[1]

    # Verificamos si el servidor ya existe
    server_running = False
    try:
        client_test = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client_test.connect(SOCKET_PATH)
        server_running = True
        client_test.close()
    except socket.error:
        server_running = False

    if not server_running:
        # No hay servidor, iniciamos uno
        try:
            if command.upper() == 'CERRAR':
                print("No hay servidor en ejecución para cerrar.")
                sys.exit(1)

            frequency = int(command)
            start_server(frequency)
        except ValueError:
            print("Error: Formato de comando no válido. Use '<frequency>'.")
            sys.exit(1)
    else:
        # Ya existe un servidor, enviamos el comando
        if command.upper() == 'CERRAR':
            send_to_server(command)
        else:
            try:
                send_to_server(command)
            except socket.error as e:
                print(f"Error: No se pudo conectar al servidor. Asegúrese de que el servidor esté en ejecución. {e}")
