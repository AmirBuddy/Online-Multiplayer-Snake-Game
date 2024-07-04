import socket
import threading
import select

HOST = '0.0.0.0'
PORT = 8080
MAX_CLIENT = 5
IDLE_TIMEOUT = 10
CLIENT_SOCKETS = []
CLIENT_EVENTS = {}

def handle_client(client_socket, addr):
    print(f"[*] Handling client {addr}")
    client_socket.setblocking(False)
    timeout = 0
    while True:
        try:
            readable, writable, exceptional = select.select([client_socket], [], [], 0.5)
            timeout += 0.5
            if CLIENT_EVENTS[client_socket].is_set():
                break
            if readable:
                timeout = 0
                request = client_socket.recv(1024)
                if not request:
                    raise ConnectionResetError()

                char = request.decode()
                print(f"[*] Received from {addr}: {char}")

                if char == 'q':
                    print(f"[*] Client {addr} disconnected")
                    client_socket.sendall("Connection closed by client\r\n".encode())
                    break

                message = f"Received {char}\r\n"
                client_socket.sendall(message.encode())
            elif timeout >= IDLE_TIMEOUT:
                print(f"[*] Client {addr} disconnected due to inactivity")
                client_socket.sendall("Disconnected due to inactivity\r\n".encode())
                break
        except ConnectionResetError:
            print(f"[*] Client {addr} error connection")
            break

    client_socket.close()
    CLIENT_SOCKETS.remove(client_socket)
    del CLIENT_EVENTS[client_socket]

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(MAX_CLIENT)
    print(f"[*] Listening on {HOST}:{PORT}")

    try:
        while True:
            client_socket, addr = server.accept()
            print(f"[*] Accepted connection from {addr}")
            CLIENT_SOCKETS.append(client_socket)
            client_event = threading.Event()
            CLIENT_EVENTS[client_socket] = client_event
            client_handler = threading.Thread(target=handle_client, args=(client_socket, addr))
            client_handler.start()
    except KeyboardInterrupt:
        print("\n[*] Shutting down...")
        for cs in CLIENT_SOCKETS:
            CLIENT_EVENTS[cs].set()
        server.close()

if __name__ == "__main__":
    main()
