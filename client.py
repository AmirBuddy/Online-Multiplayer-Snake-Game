import socket
import threading
import select
import queue
from utils import *
from getch import getch

class ClientState:
    def __init__(self):
        self.exit_event = threading.Event()
        self.input_queue = queue.Queue()

class InputHandler:
    def __init__(self, state):
        self.state = state

    def run(self):
        try:
            while not self.state.exit_event.is_set():
                char = getch()
                if char:
                    if ord(char) == 3:
                        char = 'q'
                    self.state.input_queue.put(char)
                    if char == 'q':
                        break
        except Exception as e:
            stdio_print(f"Error in InputHandler: {e}")

class SocketHandler:
    def __init__(self, client_socket, state):
        self.client_socket = client_socket
        self.state = state

    def run(self):
        try:
            while not self.state.exit_event.is_set():
                readable, writable, _ = select.select([self.client_socket], [self.client_socket], [self.client_socket], 0.5)
                
                if readable:
                    response = self.client_socket.recv(1024)
                    if not response:
                        self.state.exit_event.set()
                        raise ConnectionResetError()
                    data = response.decode()
                    if data.startswith("state data"):
                        game_state = data[10:]
                        print(game_state)
                        print('', end='\r\n')
                    else:
                        stdio_print(f"Server: {data}")
                
                if writable and not self.state.input_queue.empty():
                    char = self.state.input_queue.get()
                    self.client_socket.sendall(char.encode())
                    if char == 'q':
                        self.state.exit_event.set()
                        break
        except ConnectionResetError:
            stdio_print("Server disconnected you")

class Client:
    def __init__(self, server_address, server_port):
        self.server_address = server_address
        self.server_port = server_port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.state = ClientState()

    def start(self):
        self.client_socket.connect((self.server_address, self.server_port))
        stdio_print(f"Connected to {self.server_address}:{self.server_port}")

        res = self.client_socket.recv(1024).decode()
        stdio_print(f"Server says: {res}")
        while True:
            inp = input("Enter your ID: ")
            self.client_socket.sendall(inp.encode())
            res = self.client_socket.recv(1024).decode()
            stdio_print(f"Server says: {res}")
            if res == "Ok":
                break
            else:
                stdio_print("Invalid ID, try again.")

        input_handler = InputHandler(self.state)
        socket_handler = SocketHandler(self.client_socket, self.state)

        input_thread = threading.Thread(target=input_handler.run)
        socket_thread = threading.Thread(target=socket_handler.run)
        
        input_thread.start()
        socket_thread.start()
        
        input_thread.join()
        socket_thread.join()

        self.client_socket.close()
        stdio_print("Client socket closed")


if __name__ == "__main__":
    client = Client(server_address='127.0.0.1', server_port=8085)
    client.start()
