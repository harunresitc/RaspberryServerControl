class BackendError(Exception):
    pass


class Backend:
    def tail(self, path: str, lines: int) -> str:
        raise NotImplementedError

    def size_bytes(self, path: str) -> int:
        raise NotImplementedError

    def search(self, path: str, pattern: str, tail_lines: int = 5000, max_hits: int = 300) -> str:
        raise NotImplementedError

    def truncate(self, path: str) -> str:
        raise NotImplementedError

    def list_var_log(self) -> list[tuple[str, int, str]]:
        """Returns list of (name, size_bytes, mtime_str) for files directly under /var/log"""
        raise NotImplementedError

    def download_file(self, remote_path: str, local_path: str) -> str:
        """Downloads a file from remote to local. Returns status message."""
        raise NotImplementedError

    def get_nginx_version(self) -> str:
        raise NotImplementedError

    def get_nginx_status(self) -> str:
        raise NotImplementedError

    def check_nginx_config(self) -> str:
        """Executes 'sudo nginx -t' and returns output"""
        raise NotImplementedError

    def get_php_version(self) -> str:
        """Returns PHP version string (e.g. '8.2.7')"""
        raise NotImplementedError

    def get_php_fpm_status(self, version: str) -> str:
        """Returns status of php<version>-fpm service"""
        raise NotImplementedError

    def list_web_root(self) -> str:
        """Returns 'ls -lh /var/www/html' output"""
        raise NotImplementedError

    def check_php_errors(self) -> str:
        """Returns grep output for 'php' in nginx error log"""
        raise NotImplementedError

    def control_service(self, service_name: str, action: str) -> str:
        """
        Executes systemctl {action} {service_name}. 
        action: start, stop, restart, reload
        Returns output or success message.
        """
        raise NotImplementedError

    # MySQL / MariaDB
    def get_mysql_version(self) -> str:
        raise NotImplementedError

    def get_mysql_status(self) -> str:
        """Returns full status output"""
        raise NotImplementedError
    
    def get_mysql_service_name(self) -> str:
        """Returns 'mariadb' or 'mysql' based on check"""
        raise NotImplementedError

    def check_mysql_port(self) -> str:
        """Checks port 3306"""
        raise NotImplementedError

    def check_mysql_socket(self) -> str:
        """Checks /var/run/mysqld/"""
        raise NotImplementedError

    def get_mysql_error_log(self) -> str:
        """Tails mysql error log"""
        raise NotImplementedError

    def check_mysql_bind_address(self) -> str:
        """Greps bind-address in /etc/mysql"""
        raise NotImplementedError

    def search_db_errors_in_nginx(self) -> str:
        """Greps db related errors in nginx log"""
        raise NotImplementedError

    def search_db_errors_in_varlog(self) -> str:
        """Greps db related errors in /var/log"""
        raise NotImplementedError
    
    def truncate_all_nginx_logs(self) -> str:
        """Truncates all nginx logs"""
        raise NotImplementedError

    def truncate_php_logs(self) -> str:
        """Truncates php error logs"""
        raise NotImplementedError

    def truncate_mysql_logs(self) -> str:
        """Truncates mysql/mariadb logs"""
        raise NotImplementedError
