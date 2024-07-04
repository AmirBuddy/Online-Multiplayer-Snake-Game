import socket
import threading
import select

class ClientHandler:
    def __init__(self, client_socket, addr, idle_timeout, disconnect_event):
        self.client_socket = client_socket
        self.addr = addr
        self.idle_timeout = idle_timeout
        self.disconnect_event = disconnect_event

    def handle(self):
        print(f"Handling client {self.addr}")
        self.client_socket.setblocking(False)
        timeout = 0

        while True:
            try:
                readable, _, _ = select.select([self.client_socket], [], [], 0.5)
                timeout += 0.5
                if self.disconnect_event.is_set():
                    break
                if readable:
                    timeout = 0
                    request = self.client_socket.recv(1024)
                    if not request:
                        raise ConnectionResetError()

                    char = request.decode()
                    print(f"Received from {self.addr}: {char}")

                    if char == 'q':
                        print(f"Client {self.addr} disconnected")
                        self.client_socket.sendall("Connection closed by client\r\n".encode())
                        break

                    message = f"Received {char}\r\n"
                    self.client_socket.sendall(message.encode())
                elif timeout >= self.idle_timeout:
                    print(f"Client {self.addr} disconnected due to inactivity")
                    self.client_socket.sendall("Disconnected due to inactivity\r\n".encode())
                    break
            except ConnectionResetError:
                print(f"Client {self.addr} error connection")
                break

        self.cleanup()

    def cleanup(self):
        self.client_socket.close()
        ServerState.remove_client(self.client_socket)

class ServerState:
    client_events = {}

    @classmethod
    def add_client(cls, client_socket, event):
        cls.client_events[client_socket] = event

    @classmethod
    def remove_client(cls, client_socket):
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
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(self.max_clients)
        print(f"Listening on {self.host}:{self.port}")

        try:
            while True:
                client_socket, addr = self.server_socket.accept()
                print(f"Accepted connection from {addr}")
                client_event = threading.Event()
                ServerState.add_client(client_socket, client_event)
                client_handler = ClientHandler(client_socket, addr, self.idle_timeout, client_event)
                threading.Thread(target=client_handler.handle).start()
        except KeyboardInterrupt:
            print("\nShutting down...")
            ServerState.disconnect_all()
            self.server_socket.close()

if __name__ == "__main__":
    server = Server(host='0.0.0.0', port=8080, max_clients=5, idle_timeout=10)
    server.start()
