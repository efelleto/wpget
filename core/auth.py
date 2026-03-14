import subprocess
import threading
import os
import re
import time


class SteamAuth:
    def __init__(self, log_callback, bin_path, status_callback, qr_callback=None):
        self.log = log_callback
        self.bin_path = bin_path
        self.status_callback = status_callback
        self.qr_callback = qr_callback
        self.process = None
        self._lock = threading.Lock()
        self._stopped = False

    def start_qr_login(self):
        """Inicia o processo de login via QR Code em uma thread separada."""
        def run():
            try:
                os.chmod(self.bin_path, 0o755)
                
                cmd = [
                    self.bin_path,
                    "-app", "431960",
                    "-qr",
                    "-manifest-only",
                    "-remember-password"
                ]

                with self._lock:
                    if self._stopped:
                        return
                    self.process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                        universal_newlines=True
                    )

                qr_lines = []
                capturing_qr = False
                last_qr_send_time = 0
                qr_cooldown = 1.5  # Evita enviar QR duplicado muito rápido

                for line in iter(self.process.stdout.readline, ""):
                    with self._lock:
                        if self._stopped:
                            break

                    if not line:
                        break

                    print(line, end="")
                    clean_line = line.rstrip("\n")

                    # Detecta linhas do QR code (caracteres de bloco)
                    is_qr_line = any(c in clean_line for c in ["█", "▄", "▀", "▌", "▐", "▖", "▗"])

                    if is_qr_line:
                        if not capturing_qr:
                            capturing_qr = True
                            qr_lines = []
                        qr_lines.append(clean_line)
                    else:
                        # Linha não-QR após capturar = QR terminou, envia pro popup
                        if capturing_qr and qr_lines:
                            capturing_qr = False
                            current_time = time.time()
                            if current_time - last_qr_send_time > qr_cooldown:
                                qr_text = "\n".join(qr_lines)
                                if self.qr_callback:
                                    self.qr_callback(qr_text)
                                last_qr_send_time = current_time
                            qr_lines = []

                    # Sucesso no login - extrai username da mensagem de sucesso
                    if "Logged in" in clean_line or "Success!" in clean_line:
                        self.log("authenticated! session saved.", "success")
                        # Tenta extrair username da mensagem: "-username NOME -remember-password"
                        user_match = re.search(r"-username\s+(\S+)", clean_line)
                        username = user_match.group(1) if user_match else ""
                        self.status_callback(True, username)
                        if self.qr_callback:
                            self.qr_callback(None)  # Fecha o popup
                        break

                    # Sessão já existente
                    if "Logging" in clean_line and "Steam3" in clean_line:
                        user_match = re.search(r"Logging in user '(.+?)'", clean_line)
                        if user_match:
                            username = user_match.group(1)
                            self.log(f"session restored for {username}!", "success")
                            self.status_callback(True, username)
                            if self.qr_callback:
                                self.qr_callback(None)
                            break

                    if "Invalid" in clean_line or "denied" in clean_line.lower():
                        self.log(f"auth failed: {clean_line}", "error")

                self.process.stdout.close()
                self.process.wait()

            except Exception as e:
                self.log(f"auth error: {e}", "error")
            finally:
                self._cleanup()

        # Inicia a thread
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        return thread

    def _cleanup(self):
        """Encerra o processo do DepotDownloader de forma limpa."""
        with self._lock:
            self._stopped = True
            if self.process:
                try:
                    self.process.terminate()
                    try:
                        self.process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        self.process.kill()
                        self.process.wait()
                except Exception:
                    pass
                finally:
                    if self.process.stdout:
                        self.process.stdout.close()
                    self.process = None

    def stop(self):
        """Método público para parar a autenticação."""
        self._cleanup()
