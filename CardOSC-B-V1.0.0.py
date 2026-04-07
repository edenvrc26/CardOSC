#Programmed by Cubix-X LLC.
#MIT License

import customtkinter as ctk
from tkinter import messagebox
from pythonosc import udp_client
from datetime import datetime
from pathlib import Path
import threading
import random
import time
import json
import sys

APP_NAME = "CardOSC"
CONFIG_FILE = Path("cardosc_config.json")
DEFAULT_PORT = 9000

THEMES = ["blue", "green", "dark-blue"]
TIME_FORMATS = {
    "24-hour (HH:MM:SS)": "%H:%M:%S",
    "24-hour (HH:MM)": "%H:%M",
    "Standard (H:MM AM/PM)": "%I:%M %p",
    "Standard with seconds": "%I:%M:%S %p",
}

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class CardOSCApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("CardOSC")
        self.geometry("1080x760")
        self.minsize(980, 700)

        self.is_running = False
        self.stop_event = threading.Event()
        self.worker_thread = None
        self.client = None
        self.current_message_index = 0

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.build_ui()
        self.load_config()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.after(250, self.update_clock_preview)

    def build_ui(self):
        self.header_frame = ctk.CTkFrame(self, corner_radius=16)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        self.header_frame.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="🃏 CardOSC 🃏",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        self.title_label.grid(row=0, column=0, sticky="w", padx=16, pady=(14, 2))

        self.subtitle_label = ctk.CTkLabel(
            self.header_frame,
            text="VRChat OSC chat board with preset time formats, smart placeholders, live preview, and saved settings.",
            font=ctk.CTkFont(size=14)
        )
        self.subtitle_label.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 14))

        self.main_frame = ctk.CTkFrame(self, corner_radius=16)
        self.main_frame.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 8))
        self.main_frame.grid_columnconfigure((0, 1), weight=1, uniform="cols")
        self.main_frame.grid_rowconfigure(0, weight=1)

        self.left_panel = ctk.CTkFrame(self.main_frame, corner_radius=16)
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(12, 6), pady=12)
        self.left_panel.grid_columnconfigure(0, weight=1)

        self.right_panel = ctk.CTkFrame(self.main_frame, corner_radius=16)
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=(6, 12), pady=12)
        self.right_panel.grid_columnconfigure(0, weight=1)

        self.build_connection_section()
        self.build_message_section()
        self.build_preview_section()
        self.build_controls_section()

        self.footer_frame = ctk.CTkFrame(self, corner_radius=16)
        self.footer_frame.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 16))
        self.footer_frame.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(
            self.footer_frame,
            text="Status: Ready",
            anchor="w",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.status_label.grid(row=0, column=0, sticky="ew", padx=16, pady=12)

    def build_connection_section(self):
        section = ctk.CTkFrame(self.left_panel, corner_radius=14)
        section.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 8))
        section.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(section, text="Connection", font=ctk.CTkFont(size=20, weight="bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=14, pady=(12, 8)
        )

        ctk.CTkLabel(section, text="Target IP").grid(row=1, column=0, sticky="w", padx=14, pady=(6, 2))
        self.ip_entry = ctk.CTkEntry(section, placeholder_text="#.#.#.#")
        self.ip_entry.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 8))

        ctk.CTkLabel(section, text="Port (optional, default 9000)").grid(row=1, column=1, sticky="w", padx=14, pady=(6, 2))
        self.port_entry = ctk.CTkEntry(section, placeholder_text="9000")
        self.port_entry.grid(row=2, column=1, sticky="ew", padx=14, pady=(0, 8))

        ctk.CTkLabel(section, text="Device Preset").grid(row=3, column=0, sticky="w", padx=14, pady=(6, 2))
        self.device_menu = ctk.CTkOptionMenu(
            section,
            values=["Meta Quest 3S", "PC", "Custom"],
            command=lambda _value=None: self.update_preview()
        )
        self.device_menu.grid(row=4, column=0, sticky="ew", padx=14, pady=(0, 8))

        ctk.CTkLabel(section, text="Custom Device Name").grid(row=3, column=1, sticky="w", padx=14, pady=(6, 2))
        self.custom_device_entry = ctk.CTkEntry(section, placeholder_text="Type your device label")
        self.custom_device_entry.grid(row=4, column=1, sticky="ew", padx=14, pady=(0, 8))

        ctk.CTkLabel(section, text="Time Format").grid(row=5, column=0, sticky="w", padx=14, pady=(6, 2))
        self.time_format_menu = ctk.CTkOptionMenu(
            section,
            values=list(TIME_FORMATS.keys()),
            command=lambda _value=None: self.update_preview()
        )
        self.time_format_menu.grid(row=6, column=0, sticky="ew", padx=14, pady=(0, 8))

        ctk.CTkLabel(section, text="Color Theme").grid(row=5, column=1, sticky="w", padx=14, pady=(6, 2))
        self.theme_menu = ctk.CTkOptionMenu(
            section,
            values=THEMES,
            command=self.change_theme
        )
        self.theme_menu.grid(row=6, column=1, sticky="ew", padx=14, pady=(0, 8))

        ctk.CTkLabel(section, text="Swap Interval (Refreshes)").grid(row=7, column=0, sticky="w", padx=14, pady=(6, 2))
        self.interval_entry = ctk.CTkEntry(section, placeholder_text="5")
        self.interval_entry.grid(row=8, column=0, sticky="ew", padx=14, pady=(0, 8))

        ctk.CTkLabel(section, text="Refresh Rate (seconds)").grid(row=7, column=1, sticky="w", padx=14, pady=(6, 2))
        self.refresh_entry = ctk.CTkEntry(section, placeholder_text="4")
        self.refresh_entry.grid(row=8, column=1, sticky="ew", padx=14, pady=(0, 12))

    def build_message_section(self):
        section = ctk.CTkFrame(self.left_panel, corner_radius=14)
        section.grid(row=1, column=0, sticky="nsew", padx=14, pady=(8, 14))
        section.grid_columnconfigure(0, weight=1)
        section.grid_rowconfigure(3, weight=1)
        self.left_panel.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(section, text="Messages", font=ctk.CTkFont(size=20, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=14, pady=(12, 8)
        )

        ctk.CTkLabel(section, text="Format Template (use placeholders like {message}, {time}, {device})").grid(
            row=1, column=0, sticky="w", padx=14, pady=(0, 4)
        )
        self.template_entry = ctk.CTkEntry(section, placeholder_text="{message}\n\n⌚ {time} ⌚\n{device}")
        self.template_entry.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 8))

        self.messages_box = ctk.CTkTextbox(section, wrap="word", corner_radius=10)
        self.messages_box.grid(row=3, column=0, sticky="nsew", padx=14, pady=(0, 12))
        self.messages_box.insert("1.0", "Message1\nMessage2\nMessage3")

    def build_preview_section(self):
        section = ctk.CTkFrame(self.right_panel, corner_radius=14)
        section.grid(row=0, column=0, sticky="nsew", padx=14, pady=(14, 8))
        section.grid_columnconfigure(0, weight=1)
        section.grid_rowconfigure(2, weight=1)
        self.right_panel.grid_rowconfigure(0, weight=1)

        ctk.CTkLabel(section, text="Live Preview", font=ctk.CTkFont(size=20, weight="bold")).grid(
            row=0, column=0, sticky="ew", padx=14, pady=(12, 8)
        )

        self.clock_label = ctk.CTkLabel(
            section,
            text="Current Time: --:--:--",
            font=ctk.CTkFont(size=16, weight="bold"),
            justify="center"
        )
        self.clock_label.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 8))

        self.preview_box = ctk.CTkTextbox(section, wrap="word", corner_radius=10)
        self.preview_box.grid(row=2, column=0, sticky="nsew", padx=14, pady=(0, 12))
        self.preview_box.insert("1.0", "Preview will appear here.")
        self.preview_box.configure(state="disabled")

    def build_controls_section(self):
        section = ctk.CTkFrame(self.right_panel, corner_radius=14)
        section.grid(row=1, column=0, sticky="ew", padx=14, pady=(8, 14))
        section.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(section, text="Controls", font=ctk.CTkFont(size=20, weight="bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", padx=14, pady=(12, 8)
        )

        self.start_button = ctk.CTkButton(section, text="Start", command=self.start_sending, height=38)
        self.start_button.grid(row=1, column=0, sticky="ew", padx=(14, 6), pady=(0, 12))

        self.stop_button = ctk.CTkButton(section, text="Stop", command=self.stop_sending, height=38, state="disabled")
        self.stop_button.grid(row=1, column=1, sticky="ew", padx=6, pady=(0, 12))

        self.save_button = ctk.CTkButton(section, text="Save Config", command=self.save_config, height=38)
        self.save_button.grid(row=1, column=2, sticky="ew", padx=(6, 14), pady=(0, 12))

    def get_messages(self):
        raw = self.messages_box.get("1.0", "end").splitlines()
        return [line.strip() for line in raw if line.strip()]

    def get_device_text(self):
        preset = self.device_menu.get()
        if preset == "Meta Quest 3S":
            return "🎮 [ Meta Quest 3S ] 🎮"
        if preset == "PC":
            return "🖥️ [ PC ] 🖥️"

        custom = self.custom_device_entry.get().strip()
        if custom:
            return f"🎮 [ {custom} ] 🎮"
        return "🎮 [ Custom Device ] 🎮"

    def get_time_string(self):
        selected_format = self.time_format_menu.get()
        format_code = TIME_FORMATS.get(selected_format, "%H:%M:%S")
        time_text = datetime.now().strftime(format_code)
        if "%I" in format_code:
            time_text = time_text.lstrip("0")
        return time_text

    def build_board_message(self, text):
        template = self.template_entry.get().strip()
        if not template:
            template = "{message}\n\n⌚ {time} ⌚\n{device}"

        replacements = {
            "message": text,
            "time": self.get_time_string(),
            "device": self.get_device_text(),
            "date": datetime.now().strftime("%Y-%m-%d"),
        }

        try:
            return template.format(**replacements)
        except KeyError as exc:
            missing = str(exc).strip("'")
            return f"Template error: unknown placeholder {{{missing}}}"

    def update_clock_preview(self):
        self.clock_label.configure(text=f"Current Time: {self.get_time_string()}")
        self.update_preview()
        self.after(250, self.update_clock_preview)

    def update_preview(self):
        messages = self.get_messages()
        preview_text = messages[0] if messages else "Your first message will show here."
        formatted = self.build_board_message(preview_text)

        self.preview_box.configure(state="normal")
        self.preview_box.delete("1.0", "end")
        self.preview_box.insert("1.0", formatted)
        try:
            self.preview_box.tag_config("center", justify="center")
            self.preview_box.tag_add("center", "1.0", "end")
        except Exception:
            pass
        self.preview_box.configure(state="disabled")

    def change_theme(self, theme_name):
        ctk.set_default_color_theme(theme_name)
        self.set_status(f"Theme changed to {theme_name}")
        self.update_preview()

    def set_status(self, text):
        self.status_label.configure(text=f"Status: {text}")

    def validate_inputs(self):
        ip = self.ip_entry.get().strip()
        port_text = self.port_entry.get().strip()
        interval_text = self.interval_entry.get().strip()
        refresh_text = self.refresh_entry.get().strip()
        messages = self.get_messages()

        if not ip:
            raise ValueError("Enter a target IP address.")

        if not port_text:
            port = DEFAULT_PORT
        else:
            try:
                port = int(port_text)
            except ValueError:
                raise ValueError("Port must be a whole number.")
            if not (1 <= port <= 65535):
                raise ValueError("Port must be between 1 and 65535.")

        try:
            interval = float(interval_text)
        except ValueError:
            raise ValueError("Swap interval must be a number.")
        if interval <= 0:
            raise ValueError("Swap interval must be greater than 0.")

        try:
            refresh = float(refresh_text)
        except ValueError:
            raise ValueError("Refresh rate must be a number.")
        if refresh < 2:
            raise ValueError("Refresh rate should be 2 or higher to avoid spam timeout issues.")

        if not messages:
            raise ValueError("Add at least one message.")

        return {
            "ip": ip,
            "port": port,
            "interval": interval,
            "refresh": refresh,
            "messages": messages,
        }

    def send_vrc_chat(self, message):
        if self.client:
            self.client.send_message("/chatbox/input", [message, True, False])

    def sender_loop(self, config):
        messages = config["messages"]
        interval = config["interval"]
        refresh = config["refresh"]

        next_swap = time.time()
        current_message = random.choice(messages)

        try:
            self.send_vrc_chat("🃏CardOSC🃏")
            time.sleep(2)

            while not self.stop_event.is_set():
                now = time.time()
                if now >= next_swap:
                    current_message = random.choice(messages)
                    next_swap = now + interval

                board = self.build_board_message(current_message)
                self.send_vrc_chat(board)
                time.sleep(refresh)
        except Exception as exc:
            self.after(0, lambda: messagebox.showerror("CardOSC Error", str(exc)))
        finally:
            try:
                self.send_vrc_chat("⏸")
            except Exception:
                pass
            self.after(0, self.finish_stopping)

    def start_sending(self):
        if self.is_running:
            return

        try:
            config = self.validate_inputs()
            self.client = udp_client.SimpleUDPClient(config["ip"], config["port"])
        except Exception as exc:
            messagebox.showerror("Invalid Settings", str(exc))
            return

        self.save_config(silent=True)
        self.stop_event.clear()
        self.is_running = True
        self.current_message_index = 0

        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.set_status(f"Running -> {config['ip']}:{config['port']}")

        self.worker_thread = threading.Thread(target=self.sender_loop, args=(config,), daemon=True)
        self.worker_thread.start()

    def stop_sending(self):
        if self.is_running:
            self.set_status("Stopping...")
            self.stop_event.set()

    def finish_stopping(self):
        self.is_running = False
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.set_status("Stopped")

    def save_config(self, silent=False):
        data = {
            "ip": self.ip_entry.get().strip(),
            "port": self.port_entry.get().strip(),
            "device": self.device_menu.get(),
            "custom_device": self.custom_device_entry.get().strip(),
            "time_format": self.time_format_menu.get(),
            "theme": self.theme_menu.get(),
            "template": self.template_entry.get().strip(),
            "interval": self.interval_entry.get().strip(),
            "refresh": self.refresh_entry.get().strip(),
            "messages": self.messages_box.get("1.0", "end").rstrip("\n"),
        }

        try:
            CONFIG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
            if not silent:
                self.set_status("Config saved")
        except Exception as exc:
            messagebox.showerror("Save Error", f"Could not save config.\n\n{exc}")

    def load_config(self):
        defaults = {
            "ip": "10.0.0.245",
            "port": "",
            "device": "Meta Quest 3S",
            "custom_device": "",
            "time_format": "24-hour (HH:MM:SS)",
            "theme": "blue",
            "template": "{message}\n\n⌚ {time} ⌚\n{device}",
            "interval": "5",
            "refresh": "4",
            "messages": "Message1\nMessage2\nMessage3",
        }

        data = defaults.copy()
        if CONFIG_FILE.exists():
            try:
                loaded = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    data.update(loaded)
            except Exception:
                pass

        self.ip_entry.delete(0, "end")
        self.ip_entry.insert(0, data["ip"])

        self.port_entry.delete(0, "end")
        self.port_entry.insert(0, data["port"])

        self.device_menu.set(data["device"] if data["device"] in ["Meta Quest 3S", "PC", "Custom"] else "Meta Quest 3S")

        self.custom_device_entry.delete(0, "end")
        self.custom_device_entry.insert(0, data["custom_device"])

        self.time_format_menu.set(data["time_format"] if data["time_format"] in TIME_FORMATS else "24-hour (HH:MM:SS)")
        self.theme_menu.set(data["theme"] if data["theme"] in THEMES else "blue")
        self.change_theme(self.theme_menu.get())

        self.template_entry.delete(0, "end")
        self.template_entry.insert(0, data["template"])

        self.interval_entry.delete(0, "end")
        self.interval_entry.insert(0, data["interval"])

        self.refresh_entry.delete(0, "end")
        self.refresh_entry.insert(0, data["refresh"])

        self.messages_box.delete("1.0", "end")
        self.messages_box.insert("1.0", data["messages"])

        self.update_preview()

    def on_close(self):
        if self.is_running:
            self.stop_event.set()
            self.after(300, self.destroy)
        else:
            self.destroy()


if __name__ == "__main__":
    try:
        app = CardOSCApp()
        app.mainloop()
    except KeyboardInterrupt:
        sys.exit(0)

