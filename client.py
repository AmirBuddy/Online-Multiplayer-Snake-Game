import socket
import threading
import select
import queue
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
            print(f"Error in InputHandler: {e}")

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
                    print(f"Server: {response.decode()}", end="")
                
                if writable and not self.state.input_queue.empty():
                    char = self.state.input_queue.get()
                    self.client_socket.sendall(char.encode())
                    if char == 'q':
                        self.state.exit_event.set()
                        break
        except ConnectionResetError:
            print("Server disconnected you!\r\n", end="")

class Client:
    def __init__(self, server_address, server_port):
        self.server_address = server_address
        self.server_port = server_port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.state = ClientState()

    def start(self):
        self.client_socket.connect((self.server_address, self.server_port))
        print(f"Connected to {self.server_address}:{self.server_port}")

        input_handler = InputHandler(self.state)
        socket_handler = SocketHandler(self.client_socket, self.state)

        input_thread = threading.Thread(target=input_handler.run)
        socket_thread = threading.Thread(target=socket_handler.run)
        
        input_thread.start()
        socket_thread.start()
        
        input_thread.join()
        socket_thread.join()

        self.client_socket.close()
        print("Client socket closed.")

if __name__ == "__main__":
    client = Client(server_address='127.0.0.1', server_port=8080)
    client.start()
