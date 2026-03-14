import subprocess
import os
import sys
import re
import shutil
import stat

class Downloader:
    def __init__(self, log_callback, bin_path=None, progress_callback=None):
        self.log = log_callback
        self.progress_callback = progress_callback
        self.bin_path = bin_path

    def download_item(self, item_id, output_path, username):
        if not self.bin_path:
            app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.bin_path = os.path.join(app_dir, "bin", "DepotDownloader")

        if os.path.exists(self.bin_path) and sys.platform != "win32":
            try:
                st = os.stat(self.bin_path)
                os.chmod(self.bin_path, st.st_mode | stat.S_IEXEC)
            except Exception as e:
                self.log(f"warning: could not set executable permissions: {e}", "warning")

        temp_dl_path = os.path.join(output_path, ".depot_temp")
        os.makedirs(temp_dl_path, exist_ok=True)

        cmd = [
            self.bin_path,
            "-app", "431960",
            "-username", username,
            "-pubfile", item_id,
            "-dir", output_path,
            "-remember-password"
        ]

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            for line in iter(process.stdout.readline, ""):
                clean_line = line.strip()
                if not clean_line: continue
                
                percent_match = re.search(r"(\d+\.?\d*)%", clean_line)
                if percent_match and self.progress_callback:
                    self.progress_callback(float(percent_match.group(1)), "downloading...")

            process.wait()
            
            for extra in [".DepotDownloader", "depots"]:
                extra_path = os.path.join(output_path, extra)
                if os.path.exists(extra_path):
                    if os.path.isdir(extra_path):
                        shutil.rmtree(extra_path)
                    else:
                        os.remove(extra_path)
            
            return process.returncode == 0

        except Exception as e:
            self.log(f"download error: {e}", "error")
            return False