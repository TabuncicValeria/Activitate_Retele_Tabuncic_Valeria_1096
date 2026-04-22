import socket

HOST = "127.0.0.1"
PORT = 3333
BUFFER_SIZE = 1024

def receive_full_message(sock):
    try:
        data = sock.recv(BUFFER_SIZE)
        if not data:
            return None

        string_data = data.decode('utf-8').strip()
        first_space = string_data.find(' ')

        if first_space == -1 or not string_data[:first_space].isdigit():
            return "Invalid response format from server"

        message_length = int(string_data[:first_space])
        full_data = string_data[first_space + 1:]
        remaining = message_length - len(full_data)

        while remaining > 0:
            data = sock.recv(BUFFER_SIZE)
            if not data:
                return None
            full_data += data.decode('utf-8')
            remaining -= len(data)

        return full_data
    except Exception as e:
        return f"Error: {e}"

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        print("Connected to server. Commands: ADD GET REMOVE LIST COUNT CLEAR UPDATE POP QUIT or 'exit' to quit.")

        while True:
            command = input('client> ').strip()
            if command.lower() == 'exit':
                break

            s.sendall(command.encode('utf-8'))
            response = receive_full_message(s)
            print(f"Server response: {response}")

            if command.upper()=="QUIT":
                break

if __name__ == "__main__":
    main()
