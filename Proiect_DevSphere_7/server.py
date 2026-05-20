import socket
import threading
import json
import uuid
import time

# Configuration
HOST = '0.0.0.0'
PORT = 65432
QUERY_TIMEOUT_SECONDS = 5

# Server state
clients = []  # List of dicts: {id, machine_name, ip, socket}
next_id = 1
clients_lock = threading.Lock()

# Query aggregation state
# request_id -> {operator_id, operator_socket, query, target_ids, results, created_at, completed}
pending_requests = {} 
pending_lock = threading.Lock()

# UI state
print_lock = threading.Lock()

def safe_print(*args, **kwargs):
    """Thread-safe print helper."""
    with print_lock:
        print(*args, **kwargs)

def get_public_clients():
    """
    Returns the list of clients without the socket objects.
    Safe for JSON serialization.
    """
    with clients_lock:
        return [
            {"id": c["id"], "machine_name": c["machine_name"], "ip": c["ip"]}
            for c in clients
        ]

def broadcast_client_list():
    """
    Sends the current list of connected clients to all registered clients.
    """
    public_list = get_public_clients()
    message = (json.dumps({
        "type": "CLIENT_LIST",
        "clients": public_list
    }) + "\n").encode('utf-8')
    
    with clients_lock:
        sockets_to_notify = [c["socket"] for c in clients]
        
    for sock in sockets_to_notify:
        try:
            sock.sendall(message)
        except Exception as e:
            safe_print(f"[ERROR] Failed to send broadcast: {e}")

def send_aggregated_result(request_id):
    """
    Builds and sends the aggregated result to the operator.
    Fills in missing results with timeout errors if necessary.
    """
    with pending_lock:
        if request_id not in pending_requests:
            return
            
        req_data = pending_requests[request_id]
        if req_data["completed"]:
            return
            
        req_data["completed"] = True
        
        # Fill missing targets with timeout error
        for tid in req_data["target_ids"]:
            if tid not in req_data["results"]:
                req_data["results"][tid] = {
                    "client_id": tid,
                    "status": "ERROR",
                    "result": "Timeout: client did not respond in time."
                }
        
        agg_msg = {
            "type": "AGGREGATED_RESULT",
            "request_id": request_id,
            "query": req_data["query"],
            "results": list(req_data["results"].values())
        }
        
        try:
            req_data["operator_socket"].sendall((json.dumps(agg_msg) + "\n").encode('utf-8'))
            safe_print(f"[AGGREGATED] Sent results for {request_id} to operator {req_data['operator_id']}")
        except Exception as e:
            safe_print(f"[ERROR] Failed to send aggregated result: {e}")
            
        del pending_requests[request_id]

def check_pending_timeouts():
    """Background thread to periodically check for timed out requests."""
    while True:
        time.sleep(1)
        now = time.time()
        to_timeout = []
        with pending_lock:
            for rid, data in pending_requests.items():
                if not data["completed"] and (now - data["created_at"] >= QUERY_TIMEOUT_SECONDS):
                    to_timeout.append(rid)
        for rid in to_timeout:
            safe_print(f"[TIMEOUT] Request {rid} timed out.")
            send_aggregated_result(rid)

def handle_client(client_socket, client_address):
    """Handles the communication with a single client."""
    global next_id
    safe_print(f"[INFO] New connection from {client_address}")
    current_client_info = None
    
    try:
        buffer = ""
        while True:
            raw_data = client_socket.recv(1024)
            if not raw_data:
                break
                
            buffer += raw_data.decode('utf-8')
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if not line.strip():
                    continue
                
                try:
                    message = json.loads(line)
                except json.JSONDecodeError:
                    safe_print(f"[MALFORMED JSON] from {client_address}")
                    try:
                        err_msg = json.dumps({"type": "ERROR", "message": "Malformed JSON message."}) + "\n"
                        client_socket.sendall(err_msg.encode('utf-8'))
                    except:
                        pass
                    continue

                msg_type = message.get("type")
                
                if msg_type == "REGISTER":
                    machine_name = message.get("machine_name")
                    ip = message.get("ip")
                    
                    if not isinstance(machine_name, str) or not machine_name.strip() or \
                       not isinstance(ip, str) or not ip.strip():
                        safe_print(f"[INVALID REGISTER] from {client_address}")
                        err_msg = json.dumps({"type": "ERROR", "message": "Invalid REGISTER: machine_name and ip are required."}) + "\n"
                        client_socket.sendall(err_msg.encode('utf-8'))
                        return # Close connection

                    with clients_lock:
                        client_id = next_id
                        next_id += 1
                        current_client_info = {
                            "id": client_id,
                            "machine_name": machine_name.strip(),
                            "ip": ip.strip(),
                            "socket": client_socket
                        }
                        clients.append(current_client_info)
                        safe_print(f"[REGISTER] Client {client_id} registered: {machine_name} ({ip})")
                    broadcast_client_list()
                    
                elif msg_type == "DISCONNECT":
                    if current_client_info:
                        safe_print(f"[INFO] Client {current_client_info['id']} clean disconnect.")
                    break
                    
                elif msg_type == "EXECUTE_QUERY":
                    if not current_client_info:
                        response = {"type": "EXECUTE_QUERY_ACK", "status": "ERROR", "message": "Client must register before sending queries."}
                        client_socket.sendall((json.dumps(response) + "\n").encode('utf-8'))
                        continue

                    query_str = message.get("query")
                    targets = message.get("targets")
                    
                    # Validation
                    error_msg = ""
                    if not isinstance(query_str, str) or not query_str.strip():
                        error_msg = "Query string cannot be empty."
                    elif targets != "all" and not (isinstance(targets, list) and len(targets) > 0):
                        error_msg = "Targets must be 'all' or a non-empty list of IDs."
                    elif isinstance(targets, list) and not all(isinstance(tid, int) for tid in targets):
                        error_msg = "Targets list must contain only integers."

                    if error_msg:
                        response = {"type": "EXECUTE_QUERY_ACK", "status": "ERROR", "message": error_msg}
                        client_socket.sendall((json.dumps(response) + "\n").encode('utf-8'))
                        continue

                    with clients_lock:
                        all_ids = [c["id"] for c in clients]
                            
                    resolved_targets = []
                    if targets == "all":
                        resolved_targets = all_ids
                    else:
                        unique_targets = list(dict.fromkeys(targets)) # Remove duplicates preserving order
                        for tid in unique_targets:
                            if tid not in all_ids:
                                error_msg = f"Target ID {tid} does not exist."
                                break
                            resolved_targets.append(tid)
                    
                    if error_msg:
                        response = {"type": "EXECUTE_QUERY_ACK", "status": "ERROR", "message": error_msg}
                    else:
                        request_id = str(uuid.uuid4())
                        with pending_lock:
                            pending_requests[request_id] = {
                                "operator_id": current_client_info['id'],
                                "operator_socket": client_socket,
                                "query": query_str.strip(),
                                "target_ids": resolved_targets,
                                "results": {},
                                "created_at": time.time(),
                                "completed": False
                            }
                        response = {
                            "type": "EXECUTE_QUERY_ACK",
                            "status": "OK",
                            "message": "Query request received, validated, and forwarded to selected targets.",
                            "query": query_str.strip(),
                            "request_id": request_id,
                            "resolved_targets": resolved_targets
                        }
                        
                        forward_msg = (json.dumps({
                            "type": "RUN_QUERY",
                            "request_id": request_id,
                            "query": query_str.strip(),
                            "operator_id": current_client_info['id']
                        }) + "\n").encode('utf-8')
                        
                        with clients_lock:
                            target_sockets = [c["socket"] for c in clients if c["id"] in resolved_targets]
                        for t_sock in target_sockets:
                            try:
                                t_sock.sendall(forward_msg)
                            except:
                                pass
                    client_socket.sendall((json.dumps(response) + "\n").encode('utf-8'))
                    
                elif msg_type == "QUERY_RESULT":
                    if not current_client_info:
                        safe_print(f"[UNAUTHORIZED QUERY_RESULT] from {client_address}")
                        continue

                    req_id = message.get("request_id")
                    status = message.get("status")
                    result = message.get("result")
                    client_id = current_client_info['id']
                    
                    if not isinstance(req_id, str) or not req_id or \
                       status not in ["OK", "ERROR"] or "result" not in message:
                        safe_print(f"[INVALID QUERY_RESULT] from client {client_id}")
                        continue

                    should_aggregate = False
                    with pending_lock:
                        if req_id in pending_requests:
                            req_data = pending_requests[req_id]
                            if not req_data["completed"]:
                                if client_id not in req_data["target_ids"]:
                                    safe_print(f"[IGNORED] Client {client_id} is not a target for request {req_id}")
                                    continue

                                safe_print(f"[RESULT] Request: {req_id} | From: {client_id} | Status: {status}")
                                req_data["results"][client_id] = {
                                    "client_id": client_id,
                                    "status": status,
                                    "result": result
                                }
                                received_ids = set(req_data["results"].keys())
                                target_ids = set(req_data["target_ids"])
                                if target_ids.issubset(received_ids):
                                    should_aggregate = True
                            else:
                                safe_print(f"[LATE RESULT IGNORED] request_id={req_id} from client={client_id}")
                        else:
                            safe_print(f"[LATE RESULT IGNORED] request_id={req_id} from client={client_id}")
                    if should_aggregate:
                        send_aggregated_result(req_id)

    except Exception as e:
        safe_print(f"[ERROR] Connection error with {client_address}: {e}")
    finally:
        if current_client_info:
            with clients_lock:
                if current_client_info in clients:
                    clients.remove(current_client_info)
                    safe_print(f"[DISCONNECT] Client {current_client_info['id']} removed.")
                    
                    # Handle if the disconnected client was a target for pending requests
                    client_id = current_client_info['id']
                    requests_to_complete = []
                    with pending_lock:
                        for rid, req_data in pending_requests.items():
                            if client_id in req_data["target_ids"] and client_id not in req_data["results"]:
                                # Mark as error/disconnected
                                req_data["results"][client_id] = {
                                    "client_id": client_id,
                                    "status": "ERROR",
                                    "result": "Client disconnected before sending result."
                                }
                                # Check if this was the last response needed
                                received_ids = set(req_data["results"].keys())
                                target_ids = set(req_data["target_ids"])
                                if target_ids.issubset(received_ids):
                                    requests_to_complete.append(rid)
                    
                    for rid in requests_to_complete:
                        send_aggregated_result(rid)
            broadcast_client_list()
        client_socket.close()

def start_server():
    """Starts the TCP server."""
    timeout_thread = threading.Thread(target=check_pending_timeouts)
    timeout_thread.daemon = True
    timeout_thread.start()
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        safe_print(f"[START] Server listening on {HOST}:{PORT}")
        while True:
            client_socket, client_address = server_socket.accept()
            thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
            thread.daemon = True
            thread.start()
    except Exception as e:
        safe_print(f"[CRITICAL] Server error: {e}")
    finally:
        server_socket.close()

if __name__ == "__main__":
    start_server()
