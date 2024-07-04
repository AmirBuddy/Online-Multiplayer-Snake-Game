import socket
import threading
import select
import queue
from getch import getch

exit_event = threading.Event()
input_queue = queue.Queue()

def get_input():
    try:
        while not exit_event.is_set():
            char = getch()
            if char:
                if ord(char) == 3:
                    char = 'q'
                input_queue.put(char)
                if char == 'q':
                    break
    except Exception as e:
        print(f"Error in get_input: {e}")

def handle_socket(client_socket):
    try:
        while not exit_event.is_set():
            readable, writable, exceptional = select.select([client_socket], [client_socket], [client_socket], 0.5)
            
            if readable:
                response = client_socket.recv(1024)
                if not response:
                    exit_event.set()
                    raise ConnectionResetError()
                print(f"Server: {response.decode()}", end="")
            
            if writable and not input_queue.empty():
                char = input_queue.get()
                client_socket.sendall(char.encode())
                if char == 'q':
                    exit_event.set()
                    break
    except ConnectionResetError:
        print(f"Server disconnected you!\r\n", end="")

def main():
    server_address = '127.0.0.1'
    server_port = 8080
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_address, server_port))
    print(f"Connected to {server_address}:{server_port}")

    input_thread = threading.Thread(target=get_input)
    socket_thread = threading.Thread(target=handle_socket, args=(client_socket,))
    
    input_thread.start()
    socket_thread.start()
    
    input_thread.join()
    socket_thread.join()

    client_socket.close()
    print("Client socket closed.")

if __name__ == "__main__":
    main()
