import socket
import json
import platform
import threading
import datetime

# Configuration
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 65432

# Client state
connected_clients = []
clients_lock = threading.Lock()
local_ip_addr = "127.0.0.1"
stop_event = threading.Event()

# UI state
print_lock = threading.Lock()

def safe_print(*args, **kwargs):
    """Thread-safe print helper."""
    if stop_event.is_set() and args and "[INFO] Client stopped" not in str(args[0]):
        return
    with print_lock:
        print(*args, **kwargs)

def listen_to_server(client_socket):
    """
    Background thread to continuously listen for messages from the server.
    """
    global connected_clients
    try:
        buffer = ""
        while not stop_event.is_set():
            try:
                raw_data = client_socket.recv(4096)
                if not raw_data:
                    if not stop_event.is_set():
                        safe_print("\n[INFO] Connection closed by server.")
                    break
                    
                buffer += raw_data.decode('utf-8')
                
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if not line.strip():
                        continue
                    try:
                        response = json.loads(line)
                        msg_type = response.get("type")
                        
                        if msg_type == "CLIENT_LIST":
                            with clients_lock:
                                connected_clients = response.get("clients", [])
                            safe_print("\n[UPDATE] Client list updated.")
                            
                        elif msg_type == "EXECUTE_QUERY_ACK":
                            status = response.get("status")
                            message = response.get("message")
                            if status == "OK":
                                safe_print(f"\n[ACK SUCCESS] {message}")
                                safe_print(f"Query: {response.get('query')}")
                                safe_print(f"Request ID: {response.get('request_id')}")
                            else:
                                safe_print(f"\n[ACK ERROR] {message}")
                            safe_print("\nChoice: ", end="", flush=True)

                        elif msg_type == "RUN_QUERY":
                            req_id = response.get("request_id")
                            query = response.get("query")
                            safe_print(f"\n[RUN_QUERY RECEIVED] Request: {req_id} | Query: {query}")
                            
                            status, result = execute_simulated_query(query)
                            
                            if status == "SKIP":
                                safe_print(f"[SIMULATING NO RESPONSE] Ignoring request.")
                            else:
                                result_msg = {
                                    "type": "QUERY_RESULT",
                                    "request_id": req_id,
                                    "status": status,
                                    "result": result
                                }
                                client_socket.sendall((json.dumps(result_msg) + "\n").encode('utf-8'))
                                safe_print(f"[RESULT SENT] Status: {status}")
                            safe_print("\nChoice: ", end="", flush=True)

                        elif msg_type == "AGGREGATED_RESULT":
                            req_id = response.get("request_id")
                            query = response.get("query")
                            results = response.get("results", [])
                            
                            safe_print("\n" + "="*50)
                            safe_print(f"[AGGREGATED RESULT] ID: {req_id}")
                            safe_print(f"Query: {query}")
                            safe_print("-" * 50)
                            for r in results:
                                safe_print(f"Client ID: {r['client_id']} | Status: {r['status']}")
                                safe_print(f"Result: {r['result']}")
                                safe_print("-" * 50)
                            safe_print("="*50)
                            safe_print("\nChoice: ", end="", flush=True)

                        elif msg_type == "ERROR":
                            safe_print(f"\n[SERVER ERROR] {response.get('message')}")
                            safe_print("\nChoice: ", end="", flush=True)

                    except json.JSONDecodeError:
                        continue
            except (socket.error, OSError):
                break
                
    except Exception as e:
        if not stop_event.is_set():
            safe_print(f"\n[ERROR] Receiver thread error: {e}")
    finally:
        if not stop_event.is_set():
            safe_print("\n[INFO] Stopped listening.")

def execute_simulated_query(query):
    """
    Simulates a WMI/system query execution.
    Returns (status, result).
    """
    query = query.upper()
    if query == "GET_OS":
        return "OK", platform.platform()
    elif query == "GET_HOSTNAME":
        return "OK", platform.node()
    elif query == "GET_TIME":
        return "OK", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    elif query == "GET_IP":
        return "OK", local_ip_addr
    elif query == "NO_RESPONSE":
        return "SKIP", ""
    elif query == "GET_PLATFORM":
        return "OK", platform.system()
    elif query == "GET_ARCHITECTURE":
        return "OK", platform.machine()
    elif query == "GET_PROCESSOR":
        proc = platform.processor()
        return "OK", proc if proc else "Processor information not available"
    elif query == "GET_PYTHON_VERSION":
        return "OK", platform.python_version()
    elif query == "GET_CLIENT_INFO":
        info = (f"Hostname: {platform.node()}\n"
                f"IP Address: {local_ip_addr}\n"
                f"OS/Platform: {platform.platform()}\n"
                f"Architecture: {platform.machine()}\n"
                f"Python Version: {platform.python_version()}")
        return "OK", info
    else:
        return "ERROR", f"Unknown query: {query}"

def display_clients():
    """Displays the current list of connected clients stored locally."""
    with clients_lock:
        safe_print("\n" + "="*45)
        safe_print("CURRENT CONNECTED CLIENTS")
        safe_print("-" * 45)
        safe_print(f"{'ID':<5} | {'MACHINE NAME':<20} | {'IP ADDRESS':<15}")
        safe_print("-" * 45)
        for c in connected_clients:
            safe_print(f"{c['id']:<5} | {c['machine_name']:<20} | {c['ip']:<15}")
        safe_print("="*45 + "\n")

def send_query(client_socket):
    """Handles the operator query composition and sending with local validation."""
    query_str = input("Enter query (e.g., GET_OS, GET_HOSTNAME, GET_TIME, GET_CLIENT_INFO): ").strip()
    if not query_str:
        safe_print("[ERROR] Query cannot be empty.")
        return

    targets_input = input("Enter targets ('all' or comma-separated IDs like 1,2): ").strip().lower()
    if not targets_input:
        safe_print("[ERROR] Targets cannot be empty.")
        return
    
    if targets_input == "all":
        targets = "all"
    else:
        try:
            id_list = [x.strip() for x in targets_input.split(",") if x.strip()]
            if not id_list:
                safe_print("[ERROR] No valid IDs provided.")
                return
            
            targets = []
            for tid in id_list:
                targets.append(int(tid))
            
            # Remove duplicates preserving order
            targets = list(dict.fromkeys(targets))
            
        except ValueError:
            safe_print("[ERROR] Invalid targets format. Use numeric IDs.")
            return

    request = {
        "type": "EXECUTE_QUERY",
        "query": query_str,
        "targets": targets
    }
    client_socket.sendall((json.dumps(request) + "\n").encode('utf-8'))
    safe_print("[SENT] Query request sent to server.")

def run_client():
    """Connects, registers, and runs the interactive menu."""
    machine_name = platform.node()
    global local_ip_addr
    try:
        temp_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        temp_s.connect(("8.8.8.8", 80))
        local_ip_addr = temp_s.getsockname()[0]
        temp_s.close()
    except Exception:
        local_ip_addr = "127.0.0.1"

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        safe_print(f"[CONNECTING] Connecting to {SERVER_HOST}:{SERVER_PORT}...")
        client_socket.connect((SERVER_HOST, SERVER_PORT))
        
        listener_thread = threading.Thread(target=listen_to_server, args=(client_socket,))
        listener_thread.daemon = False
        listener_thread.start()
        
        register_msg = {
            "type": "REGISTER",
            "machine_name": machine_name,
            "ip": local_ip_addr
        }
        client_socket.sendall((json.dumps(register_msg) + "\n").encode('utf-8'))
        
        while True:
            print("\n--- MENU ---")
            print("1. Show current client list")
            print("2. Send query request as operator")
            print("3. Disconnect")
            try:
                choice = input("Choice: ").strip()
            except EOFError:
                choice = "3"

            if choice == "1":
                display_clients()
            elif choice == "2":
                send_query(client_socket)
            elif choice == "3":
                stop_event.set()
                print("[DISCONNECTING] Closing connection.")
                try:
                    disconnect_msg = {"type": "DISCONNECT"}
                    client_socket.sendall((json.dumps(disconnect_msg) + "\n").encode('utf-8'))
                    client_socket.shutdown(socket.SHUT_RDWR)
                except:
                    pass
                break
            else:
                safe_print("[!] Invalid choice. Try again.")
        
    except ConnectionRefusedError:
        safe_print("[ERROR] Could not connect to server. Is it running?")
    except Exception as e:
        safe_print(f"[ERROR] An error occurred: {e}")
    finally:
        client_socket.close()
        if 'listener_thread' in locals():
            listener_thread.join(timeout=1)
        print("[INFO] Client stopped.")

if __name__ == "__main__":
    run_client()
