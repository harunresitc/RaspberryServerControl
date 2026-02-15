from dataclasses import dataclass

@dataclass
class ConnConfig:
    mode: str  # "local" or "ssh"
    host: str = ""
    user: str = "pi"
    password: str = ""
    port: int = 22
    key_path: str = ""
    use_sudo_nopass: bool = True
