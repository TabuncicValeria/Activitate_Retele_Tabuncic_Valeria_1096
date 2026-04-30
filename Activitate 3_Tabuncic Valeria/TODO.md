# 📋 FTP Exercise - TODO List

## ✅ IMPLEMENTED (Backend & Frontend)

### Server-Side (server.py)
- [x] FTP Server with socket communication
- [x] User authentication (default: student/1234)
- [x] `files/` directory management (auto-create)
- [x] Command processing and response handling
- [x] **create_file**: Store file on server
- [x] **upload**: Receive file from client
- [x] **rename_file**: Server returns "not implemented" message for students
- [x] **read_file**: Server returns "not implemented" message for students
- [x] **download**: Server returns "not implemented" message for students
- [x] **edit_file**: Server returns "not implemented" message for students
- [x] **see_file_operation_history**: Server returns "not implemented" message for students
- [x] **list_files**: Show all files on server
- [x] **logout**: End user session
- [x] Multi-threaded client handling
- [x] JSON protocol for communication

### Client-Side (client.py)
- [x] Connection to FTP server
- [x] **login**: Authenticate with username/password
- [x] **create_file()**: Create file locally with name, extension, and content
- [x] **upload()**: Send local file to server
- [x] **rename_file()**: Send request to server and display server message
- [x] **read_file()**: Send request to server and display server message
- [x] **download()**: Send request to server and display server message
- [x] **edit_file()**: Send request to server and display server message
- [x] **see_file_operation_history()**: Send request to server and display server message
- [x] **list_files()**: Display files on server
- [x] **logout()**: Disconnect from server
- [x] **disconnect()**: Close connection
- [x] Menu interface with all options
- [x] Local files directory management (`local_files/`)

---

## 🚀 TO IMPLEMENT BY STUDENTS

All these methods are in `client.py` and marked with `[STUDENT]` in the menu.

### 1. **rename_file()** 
- [ ] Ask user for OLD filename
- [ ] Ask user for NEW filename
- [ ] Send `rename_file` command to server with old_name and new_name
- [ ] Display success/error response

### 2. **read_file()**
- [ ] Get list of files from server
- [ ] Ask user to select a file
- [ ] Send `read_file` command to server
- [ ] Display file content in console

### 3. **download()**
- [ ] Get list of files from server
- [ ] Ask user to select a file
- [ ] Send `download` command to server
- [ ] Save received content to `local_files/` directory
- [ ] Confirm file was saved

### 4. **edit_file()**
- [ ] Get list of files from server
- [ ] Ask user to select a file
- [ ] Ask user for new content
- [ ] Send `edit_file` command to server with filename and new content
- [ ] Display success/error response

### 5. **see_file_operation_history()**
- [ ] Get list of files from server
- [ ] Ask user to select a file
- [ ] Send `see_file_operation_history` command to server
- [ ] Display the server response message
- [ ] Students must implement file history tracking on the server (create, edit, rename, etc operations)

---

## 📁 Project Structure

```
Seminar 10/
├── server.py
├── client.py
├── TODO.md
├── files/
└── local_files/
```

---

## 🔐 Default Credentials

- **Username**: student
- **Password**: 1234

