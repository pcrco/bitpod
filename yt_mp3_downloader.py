#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import threading
import os

class YouTubeToMP3App:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube to MP3 Downloader")
        self.root.geometry("600x400")
        self.root.resizable(True, True)

        # Variables
        self.url_var = tk.StringVar()
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar(value="Ready")
        self.download_path = tk.StringVar(value=os.path.expanduser("~/Music"))

        # Create GUI elements
        self.create_widgets()

    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # URL input
        ttk.Label(main_frame, text="YouTube URL:").grid(row=0, column=0, sticky=tk.W, pady=5)
        url_entry = ttk.Entry(main_frame, textvariable=self.url_var, width=50)
        url_entry.grid(row=0, column=1, columnspan=2, padx=(5, 0), pady=5, sticky=(tk.W, tk.E))

        # Download path
        ttk.Label(main_frame, text="Download Path:").grid(row=1, column=0, sticky=tk.W, pady=5)
        path_entry = ttk.Entry(main_frame, textvariable=self.download_path, width=40)
        path_entry.grid(row=1, column=1, padx=(5, 0), pady=5, sticky=(tk.W, tk.E))
        ttk.Button(main_frame, text="Browse", command=self.browse_folder).grid(row=1, column=2, padx=(5, 0), pady=5)

        # Download button
        self.download_btn = ttk.Button(
            main_frame,
            text="Download MP3",
            command=self.start_download
        )
        self.download_btn.grid(row=2, column=0, columnspan=3, pady=20)

        # Progress bar
        self.progress_bar = ttk.Progressbar(
            main_frame,
            variable=self.progress_var,
            maximum=100,
            length=500
        )
        self.progress_bar.grid(row=3, column=0, columnspan=3, pady=10, sticky=(tk.W, tk.E))

        # Status label
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var)
        self.status_label.grid(row=4, column=0, columnspan=3, pady=5)

        # Log text area
        self.log_text = tk.Text(main_frame, height=12, state=tk.DISABLED)
        self.log_text.grid(row=5, column=0, columnspan=3, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Scrollbar for log
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.grid(row=5, column=3, sticky=(tk.N, tk.S))
        self.log_text.configure(yscrollcommand=scrollbar.set)

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(5, weight=1)

    def browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.download_path.get())
        if folder:
            self.download_path.set(folder)

    def start_download(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL")
            return

        # Validate yt-dlp installation
        try:
            subprocess.run(['yt-dlp', '--version'], check=True, stdout=subprocess.DEVNULL)
        except (subprocess.CalledProcessError, FileNotFoundError):
            messagebox.showerror(
                "Error",
                "yt-dlp is not installed or not found in system PATH.\n"
                "Install with: pip install yt-dlp"
            )
            return

        # Disable UI during download
        self.download_btn.config(state=tk.DISABLED)
        self.progress_var.set(0)
        self.clear_log()

        # Start download in separate thread
        thread = threading.Thread(target=self.download_worker, args=(url,))
        thread.start()

    def download_worker(self, url):
        try:
            self.status_var.set("Downloading...")
            cmd = [
                'yt-dlp',
                '-x',  # Extract audio
                '--audio-format', 'mp3',
                '--audio-quality', '0',  # Best quality
                '--embed-thumbnail',
                '--add-metadata',
                '-o', f'{self.download_path.get()}/%(title)s.%(ext)s',
                '--progress',
                url
            ]

            # Run yt-dlp and capture output
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )

            # Process output in real-time
            for line in iter(process.stdout.readline, ''):
                self.root.after(0, self.update_log, line.rstrip())
                
                # Extract progress percentage
                if '%' in line:
                    try:
                        percent = float(line.split('%')[0].split()[-1])
                        self.root.after(0, self.progress_var.set, percent)
                    except (ValueError, IndexError):
                        pass

            process.wait()
            if process.returncode == 0:
                self.root.after(0, self.on_download_complete)
            else:
                self.root.after(0, self.on_download_error, f"yt-dlp exited with code {process.returncode}")
        except Exception as e:
            self.root.after(0, self.on_download_error, str(e))

    def update_log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + '\n')
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def clear_log(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

    def on_download_complete(self):
        self.status_var.set("Download completed successfully!")
        self.progress_var.set(100)
        self.download_btn.config(state=tk.NORMAL)
        messagebox.showinfo("Success", "Download completed successfully!")

    def on_download_error(self, error_msg):
        self.status_var.set(f"Error: {error_msg}")
        self.download_btn.config(state=tk.NORMAL)
        messagebox.showerror("Download Error", error_msg)

if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeToMP3App(root)
    root.mainloop()