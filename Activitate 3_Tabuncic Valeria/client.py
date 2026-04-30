import socket
import json
import os
from pathlib import Path

# Configuration
SERVER_HOST = 'localhost'
SERVER_PORT = 5000
LOCAL_FILES_DIR = 'local_files'

class FTPClient:
    def __init__(self):
        self.socket = None
        self.authenticated = False
        self.current_user = None
        self.ensure_local_dir()
    
    def ensure_local_dir(self):
        """Ensure local files directory exists"""
        if not os.path.exists(LOCAL_FILES_DIR):
            os.makedirs(LOCAL_FILES_DIR)
            print(f"✓ Local directory '{LOCAL_FILES_DIR}' created")
    
    def connect(self):
        """Connect to FTP server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((SERVER_HOST, SERVER_PORT))
            print(f"✓ Connected to {SERVER_HOST}:{SERVER_PORT}")
        except Exception as e:
            print(f"✗ Connection failed: {str(e)}")
            return False
        return True
    
    def send_command(self, command_data):
        """Send command to server and receive response"""
        try:
            self.socket.send(json.dumps(command_data).encode('utf-8'))
            response = self.socket.recv(4096).decode('utf-8')
            return json.loads(response)
        except Exception as e:
            print(f"✗ Error: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    def select_server_file(self):
        """Helper function: get list of files from server and let user choose one"""
        command = {'command': 'list_files'}
        response = self.send_command(command)

        if response['status'] != 'success':
            print(f"✗ {response['message']}")
            return None

        files = response.get('files', [])

        if not files:
            print("✗ No files on server")
            return None

        print("\n📂 Files on server:")
        for i, file in enumerate(files, 1):
            print(f"  {i}. {file}")

        choice = input("Enter file number or name: ").strip()

        try:
            file_index = int(choice) - 1
            if 0 <= file_index < len(files):
                return files[file_index]
            else:
                print("✗ Invalid choice")
                return None
        except ValueError:
            if choice in files:
                return choice
            else:
                print(f"✗ File '{choice}' not found on server")
                return None
    
    # ==================== IMPLEMENTED COMMANDS ====================
    
    def login(self, username, password):
        """Login to server"""
        command = {
            'command': 'login',
            'username': username,
            'password': password
        }
        response = self.send_command(command)
        
        if response['status'] == 'success':
            self.authenticated = True
            self.current_user = username
            print(f"✓ {response['message']}")
        else:
            print(f"✗ {response['message']}")
        
        return response['status'] == 'success'
    
    def create_file(self):
        """Create a file locally"""
        print("\n📝 CREATE FILE (Local)")
        print("-" * 40)
        
        filename = input("Enter filename (with extension): ").strip()
        if not filename:
            print("✗ Invalid filename")
            return
        
        extension = input("Enter extension (or press Enter to skip): ").strip()
        if extension and not extension.startswith('.'):
            extension = '.' + extension
        
        if extension:
            filename = filename if filename.endswith(extension) else filename + extension
        
        content = input("Enter file content: ").strip()
        
        filepath = os.path.join(LOCAL_FILES_DIR, filename)
        try:
            with open(filepath, 'w') as f:
                f.write(content)
            print(f"✓ Local file '{filename}' created in {LOCAL_FILES_DIR}/")
        except Exception as e:
            print(f"✗ Error creating file: {str(e)}")
    
    def upload(self):
        """Upload file from local to server"""
        print("\n📤 UPLOAD FILE")
        print("-" * 40)
        
        # List available local files
        try:
            files = os.listdir(LOCAL_FILES_DIR)
            if not files:
                print("✗ No files in local directory")
                return
            
            print("Available files:")
            for i, file in enumerate(files, 1):
                print(f"  {i}. {file}")
            
            choice = input("Enter file number or name: ").strip()
            
            # Try to get file by number
            try:
                file_index = int(choice) - 1
                if 0 <= file_index < len(files):
                    filename = files[file_index]
                else:
                    print("✗ Invalid choice")
                    return
            except ValueError:
                filename = choice
            
            filepath = os.path.join(LOCAL_FILES_DIR, filename)
            if not os.path.exists(filepath):
                print(f"✗ File '{filename}' not found")
                return
            
            # Read file content
            with open(filepath, 'r') as f:
                content = f.read()
            
            # Send to server
            command = {
                'command': 'upload',
                'filename': filename,
                'content': content
            }
            response = self.send_command(command)
            
            if response['status'] == 'success':
                print(f"✓ {response['message']}")
            else:
                print(f"✗ {response['message']}")
        
        except Exception as e:
            print(f"✗ Error: {str(e)}")
    
    # ==================== COMMANDS TO IMPLEMENT ====================
    
    def rename_file(self):
        """STUDENT TASK: Rename a file on server"""
        print("\n✏️  RENAME FILE (Server)")
        print("-" * 40)

        old_name = input("Enter OLD filename: ").strip()
        if not old_name:
            print("✗ Invalid old filename")
            return

        new_name = input("Enter NEW filename: ").strip()
        if not new_name:
            print("✗ Invalid new filename")
            return
        
        command = {
            'command': 'rename_file',
            'old_name': old_name,
            'new_name': new_name
        }

        response = self.send_command(command)
        
        if response['status'] == 'error':
            print(f"✗ {response['message']}")
        else:
            print(f"✓ {response['message']}")
    
    def read_file(self):
        """STUDENT TASK: Read file content from server"""
        print("\n📖 READ FILE (Server)")
        print("-" * 40)

        filename = self.select_server_file()
        if not filename:
            return
        
        command = {
            'command': 'read_file',
            'filename': filename
        }

        response = self.send_command(command)
        
        if response['status'] == 'error':
            print(f"✗ {response['message']}")
        else:
            print(f"\n✓ File '{filename}' content:")
            print("-" * 40)
            print(response.get('content', ''))
            print("-" * 40)
    
    def download(self):
        """STUDENT TASK: Download file from server to local"""
        print("\n📥 DOWNLOAD FILE")
        print("-" * 40)

        filename = self.select_server_file()
        if not filename:
            return
        
        command = {
            'command': 'download',
            'filename': filename
        }

        response = self.send_command(command)
        
        if response['status'] == 'error':
            print(f"✗ {response['message']}")
        else:
            content = response.get('content', '')
            filepath = os.path.join(LOCAL_FILES_DIR, filename)

            try:
                with open(filepath, 'w') as f:
                    f.write(content)
                print(f"✓ File '{filename}' downloaded and saved in {LOCAL_FILES_DIR}/")
            except Exception as e:
                print(f"✗ Error saving file locally: {str(e)}")
    
    def edit_file(self):
        """STUDENT TASK: Edit file on server"""
        print("\n🛠️  EDIT FILE (Server)")
        print("-" * 40)

        filename = self.select_server_file()
        if not filename:
            return

        print("Enter new content for the file:")
        new_content = input("> ")
        
        command = {
            'command': 'edit_file',
            'filename': filename,
            'content': new_content
        }

        response = self.send_command(command)
        
        if response['status'] == 'error':
            print(f"✗ {response['message']}")
        else:
            print(f"✓ {response['message']}")
    
    def see_file_operation_history(self):
        """STUDENT TASK: See file operation history on server"""
        print("\n📜 SEE FILE OPERATION HISTORY")
        print("-" * 40)

        filename = self.select_server_file()
        if not filename:
            return
        
        command = {
            'command': 'see_file_operation_history',
            'filename': filename
        }

        response = self.send_command(command)
        
        if response['status'] == 'error':
            print(f"✗ {response['message']}")
        else:
            history = response.get('history', [])

            print(f"\n📜 Operation history for '{filename}':")
            print("-" * 40)

            if not history:
                print("No history found for this file.")
            else:
                for i, item in enumerate(history, 1):
                    operation = item.get('operation', 'unknown')
                    user = item.get('user', 'unknown')
                    details = item.get('details', '')
                    timestamp = item.get('timestamp', 'unknown time')

                    if details:
                        print(f"{i}. [{timestamp}] {operation} by {user} - {details}")
                    else:
                        print(f"{i}. [{timestamp}] {operation} by {user}")

            print("-" * 40)
    
    def list_files(self):
        """List files on server"""
        command = {'command': 'list_files'}
        response = self.send_command(command)
        
        if response['status'] == 'success':
            files = response.get('files', [])
            if files:
                print(f"\n📂 Files on server ({len(files)} total):")
                for file in files:
                    print(f"  • {file}")
            else:
                print("\n✗ No files on server")
        else:
            print(f"✗ {response['message']}")
    
    def logout(self):
        """Logout from server"""
        command = {'command': 'logout'}
        response = self.send_command(command)
        
        if response['status'] == 'success':
            self.authenticated = False
            self.current_user = None
            print(f"✓ {response['message']}")
        else:
            print(f"✗ {response['message']}")
    
    def disconnect(self):
        """Disconnect from server"""
        if self.socket:
            self.socket.close()
            print("✓ Disconnected from server")
    
    def show_menu(self):
        """Show main menu"""
        print("\n" + "=" * 60)
        print("🌐 FTP CLIENT")
        print("=" * 60)
        if self.authenticated:
            print(f"User: {self.current_user} ✓")
        else:
            print("Status: Not authenticated")
        print("=" * 60)
        print("\n1. Login")
        print("2. Create File (Local)")
        print("3. Upload File")
        print("4. Rename File (Server)       [STUDENT]")
        print("5. Read File (Server)         [STUDENT]")
        print("6. Download File              [STUDENT]")
        print("7. Edit File (Server)         [STUDENT]")
        print("8. See File Operation History [STUDENT]")
        print("9. List Files on Server")
        print("10. Logout")
        print("h. Help (afiseaza meniu)")
        print("0. Exit")
        print("-" * 60)
    
    def show_status(self):
        """Show user status without full menu"""
        if self.authenticated:
            print(f"\n✓ Logged in as: {self.current_user}")
        else:
            print("\n✗ Not authenticated")
    
    def run(self):
        """Main client loop"""
        if not self.connect():
            return
        
        self.show_menu()
        
        while True:
            self.show_status()
            choice = input("Enter choice (or 'h' for help): ").strip().lower()
            
            if choice == '1':
                if not self.authenticated:
                    username = input("Username: ").strip()
                    password = input("Password: ").strip()
                    self.login(username, password)
                else:
                    print("✓ Already authenticated")
            
            elif choice == '2':
                self.create_file()
            
            elif choice == '3':
                if self.authenticated:
                    self.upload()
                else:
                    print("✗ Please login first")
            
            elif choice == '4':
                if self.authenticated:
                    self.rename_file()
                else:
                    print("✗ Please login first")
            
            elif choice == '5':
                if self.authenticated:
                    self.read_file()
                else:
                    print("✗ Please login first")
            
            elif choice == '6':
                if self.authenticated:
                    self.download()
                else:
                    print("✗ Please login first")
            
            elif choice == '7':
                if self.authenticated:
                    self.edit_file()
                else:
                    print("✗ Please login first")
            
            elif choice == '8':
                if self.authenticated:
                    self.see_file_operation_history()
                else:
                    print("✗ Please login first")
            
            elif choice == '9':
                if self.authenticated:
                    self.list_files()
                else:
                    print("✗ Please login first")
            
            elif choice == '10':
                if self.authenticated:
                    self.logout()
                else:
                    print("✗ Not authenticated")
            
            elif choice == 'h':
                self.show_menu()
            
            elif choice == '0':
                print("\n👋 Goodbye!")
                self.disconnect()
                break
            
            else:
                print("✗ Invalid choice. Type 'h' for help.")


if __name__ == '__main__':
    client = FTPClient()
    client.run()