import os
import shlex
import shutil
import subprocess
from .base import Backend, BackendError

NGINX_ERROR = "/var/log/nginx/error.log"
NGINX_ACCESS = "/var/log/nginx/access.log"
VAR_LOG_DIR = "/var/log"


class LocalBackend(Backend):
    def tail(self, path: str, lines: int) -> str:
        if not os.path.exists(path):
            raise BackendError(f"Dosya bulunamadı: {path}")
        cmd = ["tail", "-n", str(lines), path]
        return subprocess.check_output(cmd, text=True, errors="replace")

    def size_bytes(self, path: str) -> int:
        if not os.path.exists(path):
            raise BackendError(f"Dosya bulunamadı: {path}")
        return os.path.getsize(path)

    def search(self, path: str, pattern: str, tail_lines: int = 5000, max_hits: int = 300) -> str:
        if not os.path.exists(path):
            raise BackendError(f"Dosya bulunamadı: {path}")
        # Hız: son N satır içinde arama
        cmd = f"tail -n {tail_lines} {shlex.quote(path)} | grep -n --color=never -i {shlex.quote(pattern)} | head -n {max_hits}"
        return subprocess.check_output(cmd, shell=True, text=True, errors="replace")

    def truncate(self, path: str) -> str:
        if not os.path.exists(path):
            raise BackendError(f"Dosya bulunamadı: {path}")
        # sudo gerekebilir; kullanıcıya bağlı
        cmd = ["sudo", "truncate", "-s", "0", path]
        subprocess.check_call(cmd)
        return "Log temizlendi."

    def list_var_log(self) -> list[tuple[str, int, str]]:
        if not os.path.isdir(VAR_LOG_DIR):
            # If not found, create it for testing if on Windows, else raise error
            if os.name == 'nt':
                 os.makedirs(VAR_LOG_DIR, exist_ok=True)
            else:
                 raise BackendError(f"Klasör bulunamadı: {VAR_LOG_DIR}")
        
        items = []
        try:
            for name in sorted(os.listdir(VAR_LOG_DIR)):
                full = os.path.join(VAR_LOG_DIR, name)
                if os.path.isfile(full):
                    try:
                        st = os.stat(full)
                        items.append((name, st.st_size, str(int(st.st_mtime))))
                    except OSError:
                        pass # Skip files we can't stat
        except OSError as e:
             raise BackendError(f"Klasör okuma hatası: {e}")
             
        return items

    def download_file(self, remote_path: str, local_path: str) -> str:
        # Local mode: simple copy
        if not os.path.exists(remote_path):
            raise BackendError(f"Kaynak dosya yok: {remote_path}")
        try:
            shutil.copy2(remote_path, local_path)
            return f"Dosya kopyalandı: {local_path}"
        except Exception as e:
            raise BackendError(f"Kopyalama hatası: {e}")

    def get_nginx_version(self) -> str:
        if os.name == 'nt':
            return "Nginx (Local/Win: Not Installed)"
        try:
            # nginx -v writes to stderr!
            cmd = ["nginx", "-v"]
            # We need to capture stderr
            res = subprocess.run(cmd, capture_output=True, text=True)
            # Combine stdout and stderr just in case
            output = res.stderr.strip() or res.stdout.strip()
            return output
        except FileNotFoundError:
             return "Nginx bulunamadı"
        except Exception as e:
            return f"Nginx sürümü alınamadı: {e}"

    def get_nginx_status(self) -> str:
        if os.name == 'nt':
            return "Active: active (running) (Simulated on Windows)"
        # Real local linux
        try:
             return subprocess.check_output(["systemctl", "is-active", "nginx"], text=True).strip()
        except:
             return "inactive"

    def check_nginx_config(self) -> str:
        if os.name == 'nt':
             return "nginx: the configuration file /etc/nginx/nginx.conf syntax is ok\nnginx: configuration file /etc/nginx/nginx.conf test is successful"
        
        # Local linux
        cmd = ["sudo", "nginx", "-t"]
        try:
            # nginx -t writes to stderr usually
            p = subprocess.run(cmd, capture_output=True, text=True)
            return p.stdout + p.stderr
        except Exception as e:
            return f"Error checking config: {e}"

    def get_php_version(self) -> str:
        if os.name == 'nt':
            return "PHP 8.2 (Simulated)"
        try:
            res = subprocess.run(["php", "-v"], capture_output=True, text=True)
            # Output example: PHP 8.2.7 (cli) ...
            return res.stdout.splitlines()[0]
        except:
            return "PHP bulunamadı"

    def get_php_fpm_status(self, version: str) -> str:
        if os.name == 'nt':
            return "active (Simulated)"
        if not version or "bulunamadı" in version:
            return "PHP yok"
        
        # Extract version number like 8.2 from "PHP 8.2.7 (cli)..."
        # Simple heuristic: look for X.Y
        import re
        match = re.search(r"PHP (\d+\.\d+)", version)
        if match:
             ver_num = match.group(1)
             service = f"php{ver_num}-fpm"
        else:
             return "Sürüm ayrıştırılamadı"

        try:
            res = subprocess.run(["systemctl", "is-active", service], capture_output=True, text=True)
            return res.stdout.strip()
        except:
            return "Servis kontrol hatası"

    def list_web_root(self) -> str:
        if os.name == 'nt':
            return "drwxr-xr-x root root 4096 index.php\n-rw-r--r-- root root 1024 style.css"
        
        try:
            cmd = ["ls", "-lh", "/var/www/html"]
            return subprocess.check_output(cmd, text=True, errors="replace")
        except Exception as e:
            return f"Liste alınamadı: {e}"

    def check_php_errors(self) -> str:
        if os.name == 'nt':
            return "2023/10/27 10:00:00 [error] PHP Fatal error: Uncaught TypeError..."
        
        log_path = "/var/log/nginx/error.log"
        if not os.path.exists(log_path):
             return "Log dosyası yok"
             
        try:
            # grep -i php log_path | tail -n 20
            # Local pipe simulation
            p1 = subprocess.Popen(["grep", "-i", "php", log_path], stdout=subprocess.PIPE, text=True)
            p2 = subprocess.run(["tail", "-n", "20"], stdin=p1.stdout, capture_output=True, text=True)
            return p2.stdout
        except Exception as e:
            return f"Hata tarama başarısız: {e}"

    def control_service(self, service_name: str, action: str) -> str:
        if os.name == 'nt':
            return f"Simulated: sudo systemctl {action} {service_name}"
        
        # Local linux implementation
        # usage: sudo systemctl action service
        cmd = ["sudo", "systemctl", action, service_name]
        try:
             subprocess.check_call(cmd)
             return f"{service_name} {action} başarılı."
        except subprocess.CalledProcessError as e:
             raise BackendError(f"İşlem başarısız: {e}")
        except Exception as e:
             raise BackendError(f"Hata: {e}")

    # MySQL - Local Simulation
    def get_mysql_version(self) -> str:
        if os.name == 'nt': return "mysql  Ver 15.1 Distrib 10.5.19-MariaDB"
        return "Local implementation needed"

    def get_mysql_status(self) -> str:
        if os.name == 'nt': return "Active: active (running) since..."
        return "Local implementation needed"
    
    def get_mysql_service_name(self) -> str:
        return "mariadb"

    def check_mysql_port(self) -> str:
        if os.name == 'nt': return "tcp LISTEN 0 0 0.0.0.0:3306"
        return "Local implementation needed"

    def check_mysql_socket(self) -> str:
        if os.name == 'nt': return "mysqld.sock 0"
        return "Local implementation needed"

    def get_mysql_error_log(self) -> str:
        if os.name == 'nt': return "[Note] InnoDB: Buffer pool(s) load completed at..."
        return "Local implementation needed"

    def check_mysql_bind_address(self) -> str:
        if os.name == 'nt': return "/etc/mysql/mariadb.conf.d/50-server.cnf: bind-address = 0.0.0.0"
        return "Local implementation needed"

    def search_db_errors_in_nginx(self) -> str:
        if os.name == 'nt': return "Simulated: No DB errors in nginx log"
        return "Local implementation needed"

    def search_db_errors_in_varlog(self) -> str:
        if os.name == 'nt': return "Simulated: No DB errors in /var/log"
        return "Local implementation needed"

    def truncate_all_nginx_logs(self) -> str:
        if os.name == 'nt':
            return "Simulated: Nginx logs truncated."
        # sudo truncate -s 0 /var/log/nginx/*.log
        cmd = "sudo truncate -s 0 /var/log/nginx/*.log"
        subprocess.check_call(cmd, shell=True)
        return "Tüm Nginx logları temizlendi."

    def truncate_php_logs(self) -> str:
        if os.name == 'nt':
            return "Simulated: PHP logs truncated."
        # Find php log (usually /var/log/php*-fpm.log or in nginx error log)
        # Assuming typical location or just same as nginx error log for now
        # Actually PHP-FPM usually logs to /var/log/phpX.Y-fpm.log
        cmd = "sudo truncate -s 0 /var/log/php*-fpm.log"
        try:
            subprocess.check_call(cmd, shell=True)
            return "PHP logları temizlendi."
        except:
            return "PHP logu bulunamadı veya temizlenemedi."

    def truncate_mysql_logs(self) -> str:
        if os.name == 'nt':
            return "Simulated: MySQL logs truncated."
        cmd = "sudo truncate -s 0 /var/log/mysql/error.log /var/log/mariadb/mariadb.log 2>/dev/null"
        try:
            subprocess.check_call(cmd, shell=True)
            return "MySQL/MariaDB logları temizlendi."
        except:
             return "MySQL logları temizlenemedi."
