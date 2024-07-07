import socket
import threading
import select
from utils import *
from Game import *

class ClientHandler:
    def __init__(self, client_socket, addr, idle_timeout, disconnect_event, game):
        self.client_socket = client_socket
        self.addr = addr
        self.idle_timeout = idle_timeout
        self.disconnect_event = disconnect_event
        self.game = game
        self.cid = None

    def handle(self):
        stdio_print(f"Handling client {self.addr}")

        try:
            self.client_socket.sendall("Welcome! Please Enter your ID".encode())
            flag = False
            while not flag:
                data = self.client_socket.recv(1024)
                if not data:
                    raise ConnectionResetError() 
                self.cid = data.decode()
                flag = self.game.add_snake(self.cid)
                if not flag:
                    self.client_socket.sendall("This ID exists, peak another one".encode())
        except Exception:
            self.cleanup()
            return
        self.client_socket.sendall("Ok".encode())
        stdio_print(f"Client {self.addr} ID is {self.cid}")

        self.client_socket.setblocking(False)
        timeout = 0
        try:
            while self.game.is_alive(self.cid):
                try:
                    readable, _, _ = select.select([self.client_socket], [], [], 0.5)
                    if self.disconnect_event.is_set():
                        break
                    if not readable:
                        timeout += 0.5
                    if readable:
                        timeout = 0
                        request = self.client_socket.recv(1024)
                        if not request:
                            raise ConnectionResetError()

                        char = request.decode()
                        stdio_print(f"Received from {self.cid}: {char}")
                        if char == 'q' or ord(char) == 3:
                            stdio_print(f"Client {self.addr} disconnected")
                            self.client_socket.sendall("Connection closed by client".encode())
                            break
                        char = char.lower()
                        if char in ['a', 's', 'd', 'w']:
                            self.game.set_input(self.cid, char)

                    elif timeout >= self.idle_timeout:
                        stdio_print(f"Client {self.addr} disconnected due to inactivity")
                        self.client_socket.sendall("Disconnected due to inactivity".encode())
                        break

                    state_list = self.game.get_state() 
                    state_data = "\r\n".join(state_list)
                    state_data = 'state data' + state_data
                    self.client_socket.sendall(state_data.encode())

                except Exception:
                    stdio_print(f"Client {self.addr} error connection")
                    break
        except KeyError:
            pass
        self.cleanup()

    def cleanup(self):
        try:
            self.client_socket.close()
        except Exception as e:
            stdio_print(f"Error closing client socket for {self.addr}: {e}")
        if self.cid:
            self.game.remove(self.cid)
        ServerState.remove_client(self.client_socket)

class ServerState:
    client_events = {}

    @classmethod
    def add_client(cls, client_socket, event):
        cls.client_events[client_socket] = event

    @classmethod
    def remove_client(cls, client_socket):
        if client_socket in cls.client_events:
            del cls.client_events[client_socket]

    @classmethod
    def disconnect_all(cls):
        for event in cls.client_events.values():
            event.set()

class Server:
    def __init__(self, host, port, max_clients, idle_timeout):
        self.host = host
        self.port = port
        self.max_clients = max_clients
        self.idle_timeout = idle_timeout
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self):
        game_event = threading.Event()
        game = Game(height=24, width=40, winner_length=15, game_event=game_event)
        threading.Thread(target=game.update).start()
        stdio_print(f"Game interval update setup done")

        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(self.max_clients)
        stdio_print(f"Listening on {self.host}:{self.port}")

        try:
            while True:
                client_socket, addr = self.server_socket.accept()
                stdio_print(f"Accepted connection from {addr}")
                client_event = threading.Event()
                ServerState.add_client(client_socket, client_event)
                client_handler = ClientHandler(client_socket, addr, self.idle_timeout, client_event, game)
                threading.Thread(target=client_handler.handle).start()
        except KeyboardInterrupt:
            stdio_print("\nShutting down...")
            ServerState.disconnect_all()
            self.server_socket.close()
            game_event.set()

if __name__ == "__main__":
    server = Server(host='0.0.0.0', port=8085, max_clients=5, idle_timeout=30)
    server.start()
