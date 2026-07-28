from __future__ import annotations

import os
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .client import RouterError
from .runner import run_test


class RouterOQCGui:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Router OQC Status Tool V0.1.0")
        self.root.geometry("920x680")
        self.root.minsize(820, 600)

        self.messages: queue.Queue[tuple[str, object]] = queue.Queue()
        self.output_var = tk.StringVar(value=str(Path.cwd() / "output"))
        self.ip_var = tk.StringVar(value="192.168.1.1")
        self.protocol_var = tk.StringVar(value="https")
        self.user_var = tk.StringVar(value="admin")
        self.password_var = tk.StringVar()
        self.show_password_var = tk.BooleanVar(value=False)
        self.timeout_var = tk.StringVar(value="10")
        self.identifier_var = tk.StringVar()
        self.last_run_dir: Path | None = None

        self._build()
        self.root.after(100, self._poll_messages)

    def _build(self):
        main = ttk.Frame(self.root, padding=14)
        main.pack(fill="both", expand=True)

        title = ttk.Label(main, text="Router OQC Device Status 擷取工具", font=("Microsoft JhengHei UI", 16, "bold"))
        title.pack(anchor="w", pady=(0, 12))

        form = ttk.LabelFrame(main, text="連線與登入", padding=12)
        form.pack(fill="x")

        labels = [
            ("Router IP / Host", self.ip_var),
            ("Username", self.user_var),
            ("Password", self.password_var),
            ("Timeout (秒)", self.timeout_var),
            ("Test SN / 識別碼", self.identifier_var),
            ("Output Folder", self.output_var),
        ]

        for row, (text, variable) in enumerate(labels):
            ttk.Label(form, text=text, width=18).grid(row=row, column=0, sticky="w", padx=4, pady=5)
            show = "*" if text == "Password" else ""
            entry = ttk.Entry(form, textvariable=variable, show=show, width=62)
            entry.grid(row=row, column=1, sticky="ew", padx=4, pady=5)
            if text == "Password":
                self.password_entry = entry
                ttk.Checkbutton(
                    form, text="顯示密碼", variable=self.show_password_var,
                    command=self._toggle_password,
                ).grid(row=row, column=2, sticky="w")
            elif text == "Output Folder":
                ttk.Button(form, text="選擇", command=self._choose_output).grid(row=row, column=2, padx=4)
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="Protocol", width=18).grid(row=0, column=2, sticky="e", padx=(12, 4))
        ttk.Combobox(form, textvariable=self.protocol_var, values=["https", "http"],
                     state="readonly", width=8).grid(row=0, column=3, sticky="w")

        actions = ttk.Frame(main)
        actions.pack(fill="x", pady=10)
        self.start_btn = ttk.Button(actions, text="登入並抓取資料", command=self._start)
        self.start_btn.pack(side="left")
        ttk.Button(actions, text="開啟結果資料夾", command=self._open_output).pack(side="left", padx=8)
        ttk.Button(actions, text="清除畫面", command=self._clear).pack(side="left")

        status_frame = ttk.LabelFrame(main, text="執行狀態", padding=8)
        status_frame.pack(fill="both", expand=True)

        self.status_text = tk.Text(status_frame, height=16, wrap="word", state="disabled")
        scroll = ttk.Scrollbar(status_frame, command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=scroll.set)
        self.status_text.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        result = ttk.LabelFrame(main, text="主要結果", padding=8)
        result.pack(fill="x", pady=(10, 0))
        self.result_var = tk.StringVar(value="尚未執行")
        ttk.Label(result, textvariable=self.result_var, justify="left").pack(anchor="w")

    def _toggle_password(self):
        self.password_entry.configure(show="" if self.show_password_var.get() else "*")

    def _choose_output(self):
        folder = filedialog.askdirectory(initialdir=self.output_var.get() or str(Path.cwd()))
        if folder:
            self.output_var.set(folder)

    def _append(self, message: str):
        self.status_text.configure(state="normal")
        self.status_text.insert("end", message + "\n")
        self.status_text.see("end")
        self.status_text.configure(state="disabled")

    def _clear(self):
        self.status_text.configure(state="normal")
        self.status_text.delete("1.0", "end")
        self.status_text.configure(state="disabled")
        self.result_var.set("尚未執行")

    def _validate(self) -> tuple[bool, str]:
        if not self.ip_var.get().strip():
            return False, "Router IP不可空白"
        if not self.user_var.get().strip():
            return False, "Username不可空白"
        if not self.password_var.get():
            return False, "Password不可空白"
        try:
            timeout = float(self.timeout_var.get())
            if timeout <= 0:
                raise ValueError
        except ValueError:
            return False, "Timeout必須是大於0的數字"
        return True, ""

    def _start(self):
        valid, message = self._validate()
        if not valid:
            messagebox.showerror("輸入錯誤", message)
            return

        self.start_btn.configure(state="disabled")
        self.result_var.set("執行中...")
        self._append("開始執行。密碼、Base64密碼、Token及Cookie不會寫入一般Log。")

        args = {
            "router_ip": self.ip_var.get().strip(),
            "protocol": self.protocol_var.get(),
            "username": self.user_var.get().strip(),
            "password": self.password_var.get(),
            "timeout": float(self.timeout_var.get()),
            "output_base": Path(self.output_var.get()),
            "identifier": self.identifier_var.get().strip() or "NO_ID",
            "progress": lambda text: self.messages.put(("progress", text)),
        }

        threading.Thread(target=self._worker, kwargs=args, daemon=True).start()

    def _worker(self, **kwargs):
        try:
            run_dir, status = run_test(**kwargs)
            self.messages.put(("success", (run_dir, status)))
        except RouterError as exc:
            self.messages.put(("error", f"{exc.code}: {exc}"))
        except Exception as exc:
            self.messages.put(("error", f"UNEXPECTED_ERROR: {exc}"))

    def _poll_messages(self):
        try:
            while True:
                kind, payload = self.messages.get_nowait()
                if kind == "progress":
                    self._append(str(payload))
                elif kind == "success":
                    run_dir, status = payload
                    self.last_run_dir = run_dir
                    self.start_btn.configure(state="normal")
                    self.result_var.set(
                        "結果：PASS\n"
                        f"Device Name：{status.system.get('Device Name', '')}\n"
                        f"Serial Number：{status.system.get('Serial Number', '')}\n"
                        f"Firmware：{status.system.get('Firmware Version', '')}\n"
                        f"LAN MAC：{status.lan.get('MAC Address', '')}\n"
                        f"輸出：{run_dir}"
                    )
                    # Clear password from GUI memory after execution.
                    self.password_var.set("")
                    messagebox.showinfo("完成", f"測試完成。\n{run_dir}")
                elif kind == "error":
                    self.start_btn.configure(state="normal")
                    self.result_var.set(f"結果：FAIL\n{payload}")
                    self.password_var.set("")
                    messagebox.showerror("執行失敗", str(payload))
        except queue.Empty:
            pass
        self.root.after(100, self._poll_messages)

    def _open_output(self):
        folder = self.last_run_dir or Path(self.output_var.get())
        folder.mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(str(folder))  # Windows
        except AttributeError:
            import subprocess
            subprocess.Popen(["xdg-open", str(folder)])

    def run(self):
        self.root.mainloop()
