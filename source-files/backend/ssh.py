import paramiko
import os
from .base import Backend, BackendError
from .config import ConnConfig

class SSHBackend(Backend):
    """
    SSH işlemleri: paramiko kütüphanesini kullanır.
    """

    def __init__(self, cfg: ConnConfig):
        self.cfg = cfg
        self.client = None
        self._connect()

    def _connect(self):
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            connect_kwargs = {
                "hostname": self.cfg.host,
                "port": self.cfg.port,
                "username": self.cfg.user,
                "timeout": 10
            }
            
            if self.cfg.password:
                connect_kwargs["password"] = self.cfg.password
                # If using password and no specific key, disable auto-key discovery 
                # to prevent "Authentication failed" if a wrong local key is tried first.
                if not self.cfg.key_path:
                    connect_kwargs["look_for_keys"] = False
                    connect_kwargs["allow_agent"] = False
            
            if self.cfg.key_path:
                connect_kwargs["key_filename"] = self.cfg.key_path
                
            self.client.connect(**connect_kwargs)
            
        except Exception as e:
            raise BackendError(f"SSH Bağlantı Hatası: {e}")

    def _run(self, command: str) -> str:
        if not self.client:
            self._connect()
        try:
            # exec_command returns (stdin, stdout, stderr)
            stdin, stdout, stderr = self.client.exec_command(command)
            out = stdout.read().decode('utf-8', errors='replace')
            err = stderr.read().decode('utf-8', errors='replace')
            
            if err and not out: 
                 # Some commands write to stderr even on success, but usually empty stdout + stderr means error
                 # However, warnings might also be in stderr. 
                 # Let's return out if present, else err if it looks like a failure?
                 # ideally exit_status check
                 if stdout.channel.recv_exit_status() != 0:
                     raise BackendError(f"Komut Hatası ({command}): {err}")
                 else:
                     # Exit code 0, but content in stderr (like nginx -v)
                     # If out is empty, return err
                     return out or err
            
            return out
        except Exception as e:
            raise BackendError(f"Komut Çalıştırma Hatası: {e}")

    def tail(self, path: str, lines: int) -> str:
        # quote path manually since shlex is local
        path_q =f"'{path}'"
        cmd = f"tail -n {int(lines)} {path_q}"
        
        # Add sudo if needed
        if self.cfg.use_sudo_nopass:
            cmd = f"sudo -n {cmd}"
        elif self.cfg.password:
             cmd = f"echo '{self.cfg.password}' | sudo -S {cmd}"
             
        return self._run(cmd)

    def size_bytes(self, path: str) -> int:
        path_q = f"'{path}'"
        cmd = f"stat -c %s {path_q}"
        
        # Add sudo if needed
        if self.cfg.use_sudo_nopass:
            cmd = f"sudo -n {cmd}"
        elif self.cfg.password:
             # Try with sudo -S if password provided, though stat usually doesn't need it unless file is restricted (like access.log)
             cmd = f"echo '{self.cfg.password}' | sudo -S {cmd}"
        
        out = self._run(cmd).strip()
        try:
            return int(out)
        except ValueError:
            raise BackendError(f"Boyut okunamadı: {out}")

    def search(self, path: str, pattern: str, tail_lines: int = 5000, max_hits: int = 300) -> str:
        path_q = f"'{path}'"
        # escape single quotes in pattern for bash single-quoted string
        pat_escaped = pattern.replace("'", "'\\''")
        pat_q = f"'{pat_escaped}'"
        
        # Construct the pipe
        # We need to run the whole pipe with sudo? Or just the tail?
        # Usually just tail needs read access. grep is processing output of tail.
        # But if we sudo the whole thing, it might be easier. 
        # Actually: sudo tail ... | grep ... is better because grep doesn't need root.
        
        tail_cmd = f"tail -n {int(tail_lines)} {path_q}"
        
        if self.cfg.use_sudo_nopass:
            tail_cmd = f"sudo -n {tail_cmd}"
        elif self.cfg.password:
             tail_cmd = f"echo '{self.cfg.password}' | sudo -S {tail_cmd}"
             
        full_cmd = f"{tail_cmd} | grep -n --color=never -i {pat_q} | head -n {int(max_hits)}"
        return self._run(full_cmd)

    def truncate(self, path: str) -> str:
        path_q = f"'{path}'"
        if self.cfg.use_sudo_nopass:
            cmd = f"sudo -n truncate -s 0 {path_q}"
        else:
            # If sudo requires password, we can pipe it: echo password | sudo -S ...
            if self.cfg.password:
                cmd = f"echo '{self.cfg.password}' | sudo -S truncate -s 0 {path_q}"
            else:
                 # fallback to non-interactive sudo attempt
                cmd = f"sudo -n truncate -s 0 {path_q}"
        
        return self._run(cmd).strip() or "Log temizlendi (remote)."

    def list_var_log(self) -> list[tuple[str, int, str]]:
        out = self._run(
            "find /var/log -maxdepth 1 -type f -printf '%f\\t%s\\t%TY-%Tm-%Td %TH:%TM\\n' | sort"
        )
        items: list[tuple[str, int, str]] = []
        for line in out.splitlines():
            parts = line.split("\t")
            if len(parts) != 3:
                continue
            name, sz, mtime = parts
            try:
                items.append((name, int(sz), mtime))
            except ValueError:
                continue
        return items

    def download_file(self, remote_path: str, local_path: str) -> str:
        if not self.client:
            self._connect()
        try:
            sftp = self.client.open_sftp()
            sftp.get(remote_path, local_path)
            sftp.close()
            return f"İndirildi: {local_path}"
        except Exception as e:
            # Fallback: Try reading via sudo cat if SFTP fails (likely permission denied)
            try:
                # Use cat with sudo support
                path_q = f"'{remote_path}'"
                cmd = f"cat {path_q}"
                
                if self.cfg.use_sudo_nopass:
                    cmd = f"sudo -n {cmd}"
                elif self.cfg.password:
                    cmd = f"echo '{self.cfg.password}' | sudo -S {cmd}"
                
                # self._run returns decoded string (utf-8)
                content = self._run(cmd)
                
                # Write to local file
                with open(local_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return f"İndirildi (sudo ile okundu): {local_path}"
            except Exception as e2:
                raise BackendError(f"SFTP İndirme Hatası: {e}\nAlternatif yöntem (sudo cat) de başarısız: {e2}")

    def get_nginx_version(self) -> str:
        # Helper to execute and catch
        def try_cmd(cmd_str):
            try:
                # Redirect stderr to stdout to capture version info
                return self._run(f"{cmd_str} 2>&1")
            except Exception:
                return None

        # 1. Try to find nginx path first
        paths = ["nginx", "/usr/sbin/nginx", "/usr/local/nginx/sbin/nginx", "/usr/local/sbin/nginx"]
        
        for path in paths:
            # Check if command works
            out = try_cmd(f"{path} -v")
            if out and "nginx version:" in out:
                # Format: "nginx version: nginx/1.18.0" -> "nginx/1.18.0"
                # Strip "nginx version: " prefix if present
                return out.replace("nginx version:", "").strip()
        
        # 2. Try sudo if configured
        if self.cfg.use_sudo_nopass or self.cfg.password:
             for path in paths:
                cmd = f"{path} -v"
                if self.cfg.use_sudo_nopass:
                    cmd = f"sudo -n {cmd}"
                else:
                    cmd = f"echo '{self.cfg.password}' | sudo -S {cmd}"
                
                out = try_cmd(cmd)
                if out and "nginx version:" in out:
                     return out.replace("nginx version:", "").strip()

        return "Nginx bulunamadı"

    def get_nginx_status(self) -> str:
        try:
            return self._run("systemctl is-active nginx")
        except Exception as e:
            return f"Durum alınamadı: {e}"

    def check_nginx_config(self) -> str:
        # sudo nginx -t
        # Redirect stderr to stdout because nginx -t writes success/fail msg to stderr
        cmd = "nginx -t 2>&1"
        return self._sudo_run(cmd)
    def get_php_version(self) -> str:
        try:
            # php -v
            out = self._run("php -v")
            # Output example: PHP 8.2.7 (cli) ...
            if out:
                return out.splitlines()[0]
            return "PHP çıktısı boş"
        except Exception as e:
            return f"PHP bulunamadı: {e}"

    def get_php_fpm_status(self, version_str: str) -> str:
        if not version_str or "bulunamadı" in version_str:
            return "PHP yok"
            
        # Extract version number like 8.2 from "PHP 8.2.7 (cli)..."
        import re
        match = re.search(r"PHP (\d+\.\d+)", version_str)
        if match:
             ver_num = match.group(1)
             service = f"php{ver_num}-fpm"
        else:
             # Fallback, maybe try common versions?
             # For now return error
             return f"Sürüm ayrıştırılamadı ({version_str})"

        try:
            return self._run(f"systemctl is-active {service}")
        except Exception as e:
             return f"Servis kontrol hatası: {e}"

    def list_web_root(self) -> str:
        try:
            return self._run("ls -lh /var/www/html")
        except Exception as e:
            return f"Liste alınamadı: {e}"

        except Exception as e:
             raise BackendError(f"{action} hatası: {e}")

    # MySQL / MariaDB
    def get_mysql_service_name(self) -> str:
        # Try to detect service name
        try:
            # Check for mariadb first
            out = self._run("systemctl list-units --type=service --all | grep mariadb")
            if "mariadb" in out:
                return "mariadb"
            # Check for mysql
            out = self._run("systemctl list-units --type=service --all | grep mysql")
            if "mysql" in out:
                return "mysql"
            return "mariadb" # Default
        except:
             return "mariadb"

    def get_mysql_version(self) -> str:
        # sudo mysql --version || sudo mariadb --version
        cmd = "mysql --version || mariadb --version"
        return self._sudo_run(cmd)

    def get_mysql_status(self) -> str:
        svc = self.get_mysql_service_name()
        return self._sudo_run(f"systemctl status {svc}")

    def check_mysql_port(self) -> str:
        return self._sudo_run("ss -lntp | grep 3306")

    def check_mysql_socket(self) -> str:
        # sudo ls -lh /var/run/mysqld/ || sudo ls -lh /run/mysqld/
        return self._sudo_run("ls -lh /var/run/mysqld/ || ls -lh /run/mysqld/")

    def get_mysql_error_log(self) -> str:
        # sudo tail -n 200 /var/log/mysql/error.log || sudo tail -n 200 /var/log/mariadb/mariadb.log
        cmd = "tail -n 200 /var/log/mysql/error.log 2>/dev/null || tail -n 200 /var/log/mariadb/mariadb.log 2>/dev/null"
        return self._sudo_run(cmd)

    def check_mysql_bind_address(self) -> str:
        # grep -Rin "bind-address" /etc/mysql/ /etc/my.cnf /etc/my.cnf.d
        cmd = 'grep -Rin "bind-address" /etc/mysql/ /etc/my.cnf /etc/my.cnf.d 2>/dev/null'
        return self._sudo_run(cmd)

    def search_db_errors_in_nginx(self) -> str:
        # sudo grep -Ei "php|fastcgi|mysqli|pdo|sql|mysql|mariadb|denied|permission" /var/log/nginx/error.log
        pat = "php|fastcgi|mysqli|pdo|sql|mysql|mariadb|denied|permission"
        cmd = f"grep -Ei \"{pat}\" /var/log/nginx/error.log | tail -n 200"
        return self._sudo_run(cmd)

    def search_db_errors_in_varlog(self) -> str:
        # sudo grep -Rin "SQLSTATE|mysql|mysqli|pdo" /var/log 2>/dev/null | head -n 50
        pat = "SQLSTATE|mysql|mysqli|pdo"
        cmd = f"grep -Rin \"{pat}\" /var/log 2>/dev/null | head -n 50"
        return self._sudo_run(cmd)

    def truncate_all_nginx_logs(self) -> str:
        # sudo truncate -s 0 /var/log/nginx/*.log
        cmd = "truncate -s 0 /var/log/nginx/*.log"
        return self._sudo_run(cmd) or "Nginx logları temizlendi."

    def truncate_php_logs(self) -> str:
        # sudo truncate -s 0 /var/log/php*-fpm.log
        cmd = "truncate -s 0 /var/log/php*-fpm.log"
        return self._sudo_run(cmd) or "PHP logları temizlendi."

    def truncate_mysql_logs(self) -> str:
        # sudo truncate -s 0 /var/log/mysql/error.log /var/log/mariadb/mariadb.log 2>/dev/null
        cmd = "truncate -s 0 /var/log/mysql/error.log /var/log/mariadb/mariadb.log 2>/dev/null"
        return self._sudo_run(cmd) or "MySQL logları temizlendi."

    def check_php_errors(self) -> str:
        # Refined as requested: just grep php, but we'll limit output to avoid UI freeze
        # User asked: sudo grep -i php /var/log/nginx/error.log
        cmd = "grep -i php /var/log/nginx/error.log | tail -n 200"
        return self._sudo_run(cmd)

    def _sudo_run(self, cmd: str) -> str:
        """Helper for simple sudo commands"""
        if self.cfg.use_sudo_nopass:
            full = f"sudo -n {cmd}"
        elif self.cfg.password:
            # Complex commands might fail with pipe, better wrap in sh -c?
            # Or just simple echo password pipe
            # But cmd might contain pipes itself.
            # Safe way: sudo -S bash -c 'cmd'
            escaped_cmd = cmd.replace("'", "'\\''")
            full = f"echo '{self.cfg.password}' | sudo -S bash -c '{escaped_cmd}'"
        else:
            full = cmd
            
        try:
            return self._run(full).strip()
        except Exception as e:
            return f"Error: {e}"
