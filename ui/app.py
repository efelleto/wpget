import os
import sys
import threading
import re
import subprocess
import shutil
import webbrowser
import customtkinter as ctk
from PIL import Image, ImageTk
import requests
from io import BytesIO
from ui.qr_popup import QRPopup
from ui.theme import COLORS, FONTS
from core.steam_api import SteamAPI
from core.downloader import Downloader
from core.auth import SteamAuth

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class WPGetApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window config
        self.title("wpget")
        self.geometry("700x750")
        self.configure(fg_color=COLORS["bg"])

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(6, weight=1)

        self.qr_popup = None
        self.current_steam_user = None
        self.auth_instance = None
        self._auth_lock = threading.Lock()
        self._auth_in_progress = False
        self._auth_started = False
        self.current_item_data = None
        self._last_fetch_id = None
        self._fetch_in_progress = False
        self.last_download_path = None

        self.steam_photo = None
        try:
            icon_path = resource_path(os.path.join("assets", "steam_icon.png"))
            if os.path.exists(icon_path):
                img = Image.open(icon_path).convert("RGBA")
                img = img.resize((20, 20), Image.Resampling.LANCZOS)
                self.steam_photo = ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Erro ao processar ícone: {e}")

        self.header_label = ctk.CTkLabel(
            self, text="wpget", font=FONTS["title"], text_color=COLORS["accent"]
        )
        self.header_label.grid(row=0, column=0, padx=20, pady=(20, 0), sticky="nw")

        self.status_label = ctk.CTkLabel(
            self, text="status: not logged in", font=FONTS["main"],
            text_color=COLORS["error"]
        )
        self.status_label.grid(row=0, column=0, padx=20, pady=(25, 0), sticky="ne")

        self.sub_label = ctk.CTkLabel(
            self, text="workshop wallpaper downloader",
            font=FONTS["main"], text_color=COLORS["text"]
        )
        self.sub_label.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nw")

        # 2. Auth section
        self.auth_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.auth_frame.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")

        self.login_btn = ctk.CTkButton(
            self.auth_frame, 
            text="connect with steam", 
            image=self.steam_photo,
            compound="left",
            width=220, height=38,
            font=FONTS["main"], fg_color="#3d4455", hover_color="#565f89",
            command=self.start_auth_process
        )
        self.login_btn.image = self.steam_photo
        self.login_btn.pack(side="left")

        self.input_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.input_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.url_entry = ctk.CTkEntry(
            self.input_frame, placeholder_text="paste workshop url...", height=45,
            border_color=COLORS["accent"], fg_color=COLORS["log_bg"],
            text_color="#ffffff", state="disabled"
        )
        self.url_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        self.url_entry.bind("<KeyRelease>", self.on_url_change)
        self.url_entry.bind("<FocusOut>", self.on_url_change)

        self.download_btn = ctk.CTkButton(
            self.input_frame, text="↓ download", font=FONTS["main"],
            fg_color="#3d4455", hover_color="#565f89",
            text_color="#ffffff", width=120, height=45,
            command=self.start_download_trigger, state="disabled"
        )
        self.download_btn.grid(row=0, column=1)

        self.preview_frame = ctk.CTkFrame(
            self, fg_color=COLORS["log_bg"], border_width=1, border_color="#24283b"
        )
        self.preview_frame.grid(row=4, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.preview_frame.grid_remove() 

        self.preview_info_frame = ctk.CTkFrame(
            self.preview_frame, fg_color="transparent"
        )
        self.preview_info_frame.pack(side="left", fill="both", expand=True, padx=15, pady=15)

        self.preview_title = ctk.CTkLabel(
            self.preview_info_frame, text="", font=("JetBrains Mono", 14, "bold"),
            text_color=COLORS["accent"], wraplength=550
        )
        self.preview_title.pack(anchor="w", pady=(0, 8))

        self.preview_type = ctk.CTkLabel(
            self.preview_info_frame, text="", font=("JetBrains Mono", 11),
            text_color=COLORS["text"]
        )
        self.preview_type.pack(anchor="w", pady=(0, 4))

        self.preview_res = ctk.CTkLabel(
            self.preview_info_frame, text="", font=("JetBrains Mono", 11),
            text_color=COLORS["text"]
        )
        self.preview_res.pack(anchor="w", pady=(0, 4))

        self.preview_author = ctk.CTkLabel(
            self.preview_info_frame, text="", font=("JetBrains Mono", 10),
            text_color=COLORS["warning"]
        )
        self.preview_author.pack(anchor="w", pady=(0, 10))

        self.open_folder_btn = ctk.CTkButton(
            self.preview_info_frame, text="📂 open folder", font=("JetBrains Mono", 10),
            fg_color="#24283b", hover_color="#3d4455", width=120, height=28,
            command=self.open_folder_action
        )

        self.clear_junk_btn = ctk.CTkButton(
            self.preview_info_frame, text="🗑️ clear junk files", font=("JetBrains Mono", 10),
            fg_color="#24283b", hover_color="#e06868", width=120, height=28,
            command=self.clear_junk_action
        )

        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.progress_frame.grid(row=5, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.progress_frame.grid_remove()

        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame, width=660, height=8,
            fg_color=COLORS["log_bg"], progress_color=COLORS["accent"],
            mode="determinate"
        )
        self.progress_bar.pack(fill="x")
        self.progress_bar.set(0)

        self.progress_status = ctk.CTkLabel(
            self.progress_frame, text="", font=("JetBrains Mono", 10),
            text_color="#565f89"
        )
        self.progress_status.pack(pady=(8, 0))

        self.console_box = ctk.CTkTextbox(
            self, fg_color=COLORS["log_bg"], text_color=COLORS["text"],
            font=FONTS["console"], border_width=1, border_color="#24283b", height=150
        )
        self.console_box.grid(row=6, column=0, padx=20, pady=20, sticky="nsew")
        self.console_box.configure(state="disabled")

        self.console_box.tag_config("success", foreground=COLORS["success"])
        self.console_box.tag_config("error", foreground=COLORS["error"])
        self.console_box.tag_config("warning", foreground=COLORS["warning"])
        self.console_box.tag_config("accent", foreground=COLORS["accent"])
        self.console_box.tag_config("text", foreground=COLORS["text"])
        self.console_box.tag_config("info", foreground="#565f89")

        # Github Support Footer
        self.github_label = ctk.CTkLabel(
            self, text="support wpget on github", font=("JetBrains Mono", 10),
            text_color="#565f89", cursor="hand2"
        )
        self.github_label.grid(row=7, column=0, padx=20, pady=(0, 10), sticky="se")
        self.github_label.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/eduardo/wpget"))

        self.after(1000, self.start_auth_process)
        self.log("wpget started.", "success")

    def update_status(self, logged_in, username=""):
        self.after(0, lambda: self._update_status_ui(logged_in, username))

    def _update_status_ui(self, logged_in, username=""):
        if logged_in:
            if not username and self.current_steam_user:
                username = self.current_steam_user
            self.current_steam_user = username
            self.status_label.configure(
                text=f"status: logged in on {username}" if username else "status: logged in",
                text_color=COLORS["success"]
            )
            self.login_btn.configure(text=f"connected: {username}", state="disabled")
            self.show_qr(None)
            self._auth_in_progress = False
            self.url_entry.configure(state="normal")
            self.log("steam connected! paste a workshop url to begin.", "accent")
        else:
            self.current_steam_user = None
            self.status_label.configure(text="status: not logged in", text_color=COLORS["error"])
            self.login_btn.configure(text="connect with steam", image=self.steam_photo, state="normal")
            self.login_btn.image = self.steam_photo
            self._auth_in_progress = False
            self._auth_started = False
            self.url_entry.configure(state="disabled")
            self.download_btn.configure(state="disabled")
            self.show_qr(None)

    def log(self, message, color_key="text", prefix=True):
        self.after(0, lambda: self._internal_log(message, color_key, prefix))

    def _internal_log(self, message, color_key, prefix):
        self.console_box.configure(state="normal")
        display_msg = f"> {message}\n" if prefix else f"{message}\n"
        self.console_box.insert("end", display_msg, color_key)
        self.console_box.configure(state="disabled")
        self.console_box.see("end")

    def show_qr(self, qr_text):
        self.after(0, lambda: self._show_qr_ui(qr_text))

    def _show_qr_ui(self, qr_text):
        if qr_text is None:
            if self.qr_popup and self.qr_popup.winfo_exists():
                self.qr_popup.destroy()
            self.qr_popup = None
            return
        if self.qr_popup is None or not self.qr_popup.winfo_exists():
            self.qr_popup = QRPopup(self)
        self.qr_popup.update_qr(qr_text)

    def on_url_change(self, event=None):
        url = self.url_entry.get().strip()
        if not url:
            self.preview_frame.grid_remove()
            self.open_folder_btn.pack_forget()
            self.clear_junk_btn.pack_forget()
            self.download_btn.configure(state="disabled", fg_color="#3d4455")
            self.current_item_data = None
            self._last_fetch_id = None
            return

        item_id = SteamAPI.extract_id(url)
        if item_id == self._last_fetch_id or self._fetch_in_progress:
            return

        if item_id:
            self.open_folder_btn.pack_forget()
            self.clear_junk_btn.pack_forget()
            self._last_fetch_id = item_id
            self._fetch_in_progress = True
            self.log(f"fetching wallpaper info...", "accent")
            threading.Thread(target=self._fetch_preview, args=(item_id,), daemon=True).start()

    def _fetch_preview(self, item_id):
        data = SteamAPI.get_metadata(item_id)
        self._fetch_in_progress = False 
        if data:
            self.after(0, lambda: self._show_preview(data))
        else:
            self.log("failed to fetch wallpaper info", "error")

    def _show_preview(self, data):
        self.current_item_data = data
        self.preview_title.configure(text=data.get("title", "Unknown"))
        self.preview_type.configure(text=f"type: {data.get('type', 'scene')}")
        self.preview_frame.grid()

        if self.current_steam_user:
            self.download_btn.configure(state="normal", fg_color=COLORS["accent"])
            self.log("wallpaper ready to download!", "success")

    def start_auth_process(self):
        if self._auth_in_progress:
            return
        
        self.login_btn.configure(text="connecting...", state="disabled", image=self.steam_photo)
        self.login_btn.image = self.steam_photo
        self._auth_in_progress = True
        self._auth_started = True
        
        with self._auth_lock:
            if self.auth_instance:
                self.auth_instance.stop()
        
        # Detect OS and set correct binary name
        bin_name = "DepotDownloader.exe" if sys.platform == "win32" else "DepotDownloader"
        bin_path = resource_path(os.path.join("bin", bin_name))
        
        if not os.path.exists(bin_path):
            self.log(f"depotdownloader not found", "error")
            self._auth_in_progress = False
            self.login_btn.configure(text="connect with steam", image=self.steam_photo, state="normal")
            self.login_btn.image = self.steam_photo
            return
            
        with self._auth_lock:
            self.auth_instance = SteamAuth(self.log, bin_path, self.update_status, qr_callback=self.show_qr)
            self.auth_instance.start_qr_login()
        self.log("generating qr code...", "accent")

    def start_download_trigger(self):
        if not self.current_item_data: return
        item_id = self.current_item_data["id"]
        self.download_btn.configure(state="disabled")
        self.progress_frame.grid()
        self.progress_bar.set(0)
        self.progress_status.configure(text="initializing download...")

        # Get correct bin_path for the Downloader
        bin_name = "DepotDownloader.exe" if sys.platform == "win32" else "DepotDownloader"
        bin_path = resource_path(os.path.join("bin", bin_name))

        def process():
            temp_path = os.path.join(os.getcwd(), "temp", item_id)
            os.makedirs(temp_path, exist_ok=True)
            dl = Downloader(self.log, bin_path=bin_path, progress_callback=self.update_progress)
            success = dl.download_item(item_id, temp_path, self.current_steam_user)
            if success:
                self.after(0, lambda: self._download_success(temp_path))
            else:
                self.after(0, lambda: self._download_error())
        threading.Thread(target=process, daemon=True).start()

    def update_progress(self, percent, status_text):
        self.after(0, lambda: self._update_progress_ui(percent, status_text))

    def _update_progress_ui(self, percent, status_text):
        self.progress_bar.set(percent / 100)
        self.progress_status.configure(text=status_text.lower())

    def _download_success(self, folder_path):
        self.last_download_path = folder_path
        self.progress_bar.set(1.0)
        self.progress_status.configure(text="download complete!")
        self.download_btn.configure(state="normal", fg_color=COLORS["accent"])
        self.log(f"download completed!", "success")
        self.open_folder_btn.pack(anchor="w", pady=(5, 0))
        self.clear_junk_btn.pack(anchor="w", pady=(5, 0))

    def _download_error(self):
        self.progress_bar.set(0)
        self.progress_status.configure(text="download failed")
        self.download_btn.configure(state="normal", fg_color=COLORS["accent"])
        self.log("download failed!", "error")

    def open_folder_action(self):
        if self.last_download_path and os.path.exists(self.last_download_path):
            if sys.platform == "win32":
                os.startfile(self.last_download_path)
            else:
                subprocess.Popen(['xdg-open', self.last_download_path])

    def clear_junk_action(self):
        try:
            depots_path = os.path.join(os.getcwd(), "depots")
            if os.path.exists(depots_path):
                shutil.rmtree(depots_path)
                self.log("junk files (depots) cleared!", "success")
                self.clear_junk_btn.pack_forget()
            else:
                self.log("no junk files found to clear.", "warning")
        except Exception as e:
            self.log(f"error clearing junk: {e}", "error")

if __name__ == "__main__":
    app = WPGetApp()
    app.mainloop()