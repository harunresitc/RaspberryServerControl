import threading
import time
from PySide6.QtCore import QThread, Signal
from backend.ssh import SSHBackend

class SSHLogThread(QThread):
    log_output = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, backend: SSHBackend, path: str):
        super().__init__()
        self.backend = backend
        self.path = path
        self.running = False
        self._stop_event = threading.Event()

    def run(self):
        self.running = True
        client = self.backend.client
        if not client:
            try:
                self.backend._connect()
                client = self.backend.client
            except Exception as e:
                self.error_occurred.emit(str(e))
                return

        # tail -f komutunu çalıştır
        cmd = f"tail -f '{self.path}'"
        if self.backend.cfg.use_sudo_nopass:
            cmd = f"sudo -n {cmd}"
        elif self.backend.cfg.password:
             # Interactive sudo handling in a thread is complex. 
             # For now, we rely on passwordless sudo or user rights.
             # If we really need to support password sudo here, we'd need to write to stdin.
             pass
        
        try:
            self.stdin, self.stdout, self.stderr = client.exec_command(cmd, get_pty=True)
            self.channel = self.stdout.channel
            
            # Non-blocking read loop
            while self.running and not self._stop_event.is_set():
                if self.channel.recv_ready():
                    line = self.channel.recv(1024).decode('utf-8', errors='replace')
                    if line:
                        self.log_output.emit(line)
                
                if self.channel.exit_status_ready():
                    break
                
                time.sleep(0.1)
                
        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            self.running = False


    def stop(self):
        self.running = False
        self._stop_event.set()
        # Force close channel to break potential blocking
        if hasattr(self, 'channel') and self.channel:
            try:
                self.channel.close()
            except:
                pass
        self.wait(2000) # Wait max 2 seconds, then proceed to prevent infinite freeze
