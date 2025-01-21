import socket
import sys
import os
import time
import threading
from playsound import playsound

SOCKET_PATH = '/tmp/metronomo.sock'

class Metronomo:
    def __init__(self, tempo, compas):
        self.tempo = tempo  # en BPM
        self.compas = compas  # Número de pulsos por compás
        self.running = True

    def start(self):
        """Inicia el metrónomo en un hilo separado."""
        threading.Thread(target=self.run, daemon=True).start()

    def run(self):
        """Lógica principal del metrónomo."""
        while self.running:
            interval = 60 / self.tempo  # Duración de cada pulso en segundos
            for beat in range(1, self.compas + 1):
                if not self.running:
                    break
                print(f"Pulso {beat}/{self.compas}")
                playsound(os.path.join(os.path.dirname(__file__), 'tick.wav'), block=False)
                time.sleep(interval)

    def update(self, tempo, compas):
        """Actualiza los parámetros del metrónomo."""
        print(f"Actualizando metrónomo: Tempo={tempo}, Compás={compas}")
        self.tempo = tempo
        self.compas = compas

    def stop(self):
        """Detiene el metrónomo."""
        self.running = False


def start_server(initial_tempo, initial_compas):
    """Inicia el servidor para controlar el metrónomo."""
    if os.path.exists(SOCKET_PATH):
        os.remove(SOCKET_PATH)

    server_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server_sock.bind(SOCKET_PATH)
    server_sock.listen(1)

    print(f"[Servidor] Metrónomo iniciado con Tempo={initial_tempo}, Compás={initial_compas}")
    metronomo = Metronomo(initial_tempo, initial_compas)
    metronomo.start()

    while True:
        conn, _ = server_sock.accept()
        try:
            data = conn.recv(1024).decode('utf-8').strip()
            if data:
                if data.upper() == 'CERRAR':
                    print("[Servidor] Recibido comando de cierre. Terminando servidor.")
                    metronomo.stop()
                    conn.close()
                    break
                else:
                    # Parseamos los parámetros del comando
                    try:
                        tempo, compas = map(int, data.split(','))
                        metronomo.update(tempo, compas)
                        conn.sendall(f"Metrónomo actualizado: Tempo={tempo}, Compás={compas}\n".encode('utf-8'))
                    except ValueError:
                        conn.sendall(b"Error: Formato de comando no valido. Use '<tempo>,<compas>'.\n")
            else:
                conn.close()
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
        print("Uso: python metronomo.py <tempo>,<compas> | CERRAR")
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

            tempo, compas = map(int, command.split(','))
            if compas not in [2, 3, 4, 5, 6, 7, 8]:
                raise ValueError("El compás debe ser un número entre 2 y 8.")

            start_server(tempo, compas)
        except ValueError:
            print("Error: Formato de comando no válido. Use '<tempo>,<compas>'.")
            sys.exit(1)
    else:
        # Ya existe un servidor, enviamos el comando
        send_to_server(command)
