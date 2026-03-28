#!/usr/bin/env python3
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

SCRIPT_DIR = Path(__file__).parent
PYTHON = SCRIPT_DIR / ".venv" / "bin" / "python"


def run_upscale(input_path, output_path, scale, texture_strength,
                face_enhance, face_weight, log_cb, done_cb):
    cmd = [
        str(PYTHON), str(SCRIPT_DIR / "upscale.py"),
        input_path, output_path,
        "--scale", str(scale),
    ]
    if texture_strength > 0:
        cmd += ["--texture-strength", f"{texture_strength:.1f}"]
    if face_enhance:
        cmd += ["--face-enhance", "--face-weight", f"{face_weight:.2f}"]

    def worker():
        try:
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1,
            )
            for line in proc.stdout:
                log_cb(line.rstrip())
            proc.wait()
            done_cb(proc.returncode == 0)
        except Exception as e:
            log_cb(f"Error: {e}")
            done_cb(False)

    threading.Thread(target=worker, daemon=True).start()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Image Enhance")
        self.resizable(False, False)
        self._build()

    def _build(self):
        root = ttk.Frame(self, padding=16)
        root.grid(sticky="nsew")

        # Input
        ttk.Label(root, text="Input").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        self.input_var = tk.StringVar()
        ttk.Entry(root, textvariable=self.input_var, width=44).grid(row=0, column=1, padx=8, pady=6)
        ttk.Button(root, text="Browse…", command=self._pick_input).grid(row=0, column=2, padx=4)

        # Output
        ttk.Label(root, text="Output").grid(row=1, column=0, sticky="w", padx=8, pady=6)
        self.output_var = tk.StringVar(value="(auto)")
        ttk.Entry(root, textvariable=self.output_var, width=44).grid(row=1, column=1, padx=8, pady=6)
        ttk.Button(root, text="Browse…", command=self._pick_output).grid(row=1, column=2, padx=4)

        # Scale
        ttk.Label(root, text="Scale").grid(row=2, column=0, sticky="w", padx=8, pady=6)
        self.scale_var = tk.IntVar(value=2)
        sf = ttk.Frame(root)
        sf.grid(row=2, column=1, sticky="w", padx=8)
        ttk.Radiobutton(sf, text="2×", variable=self.scale_var, value=2).pack(side="left")
        ttk.Radiobutton(sf, text="4×", variable=self.scale_var, value=4).pack(side="left", padx=12)

        # Texture strength
        ttk.Label(root, text="Texture strength").grid(row=3, column=0, sticky="w", padx=8, pady=6)
        tf = ttk.Frame(root)
        tf.grid(row=3, column=1, sticky="w", padx=8)
        self.texture_var = tk.DoubleVar(value=1.0)
        self._texture_lbl = ttk.Label(tf, text="1.0", width=4)
        ttk.Scale(tf, from_=0.0, to=2.0, variable=self.texture_var, length=220,
                  command=lambda v: self._texture_lbl.config(text=f"{float(v):.1f}")).pack(side="left")
        self._texture_lbl.pack(side="left", padx=6)
        ttk.Label(tf, text="(0 = off, 1.0 = recommended)", foreground="gray").pack(side="left", padx=4)

        # Advanced toggle
        self._adv_open = tk.BooleanVar(value=False)
        ttk.Checkbutton(root, text="Advanced", variable=self._adv_open,
                        command=self._toggle_adv).grid(row=4, column=0, columnspan=3, sticky="w", padx=8, pady=(10, 0))

        # Advanced frame (hidden by default)
        self._adv = ttk.LabelFrame(root, text="Advanced", padding=10)
        self.face_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self._adv, text="Face enhance — sharpens facial features (may over-smooth skin)",
                        variable=self.face_var, command=self._toggle_face).grid(row=0, column=0, columnspan=3, sticky="w")

        ttk.Label(self._adv, text="Face weight").grid(row=1, column=0, sticky="w", pady=(8, 0))
        wf = ttk.Frame(self._adv)
        wf.grid(row=1, column=1, sticky="w", pady=(8, 0))
        self.face_weight_var = tk.DoubleVar(value=0.3)
        self._fw_lbl = ttk.Label(wf, text="0.30", width=4)
        self._fw_scale = ttk.Scale(wf, from_=0.0, to=1.0, variable=self.face_weight_var, length=160,
                                   command=lambda v: self._fw_lbl.config(text=f"{float(v):.2f}"))
        self._fw_scale.pack(side="left")
        self._fw_lbl.pack(side="left", padx=6)
        ttk.Label(wf, text="(lower = more original texture)", foreground="gray").pack(side="left", padx=4)
        self._toggle_face()

        # Run button
        self._run_btn = ttk.Button(root, text="Run", command=self._run)
        self._run_btn.grid(row=6, column=0, columnspan=3, pady=14)

        # Log
        log_frame = ttk.Frame(root)
        log_frame.grid(row=7, column=0, columnspan=3, padx=8, pady=(0, 4), sticky="ew")
        self._log = tk.Text(log_frame, height=9, width=66, state="disabled",
                            font=("Menlo", 11), background="#1e1e1e", foreground="#d4d4d4")
        sb = ttk.Scrollbar(log_frame, command=self._log.yview)
        self._log.config(yscrollcommand=sb.set)
        self._log.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    def _toggle_adv(self):
        if self._adv_open.get():
            self._adv.grid(row=5, column=0, columnspan=3, sticky="ew", padx=8, pady=4)
        else:
            self._adv.grid_remove()

    def _toggle_face(self):
        self._fw_scale.config(state="normal" if self.face_var.get() else "disabled")

    def _pick_input(self):
        path = filedialog.askopenfilename(
            filetypes=[("Images", "*.png *.jpg *.jpeg *.tif *.tiff *.webp"), ("All files", "*.*")])
        if path:
            self.input_var.set(path)
            if self.output_var.get() in ("(auto)", ""):
                p = Path(path)
                self.output_var.set(str(p.parent / f"{p.stem}_upscaled.png"))

    def _pick_output(self):
        path = filedialog.asksaveasfilename(defaultextension=".png",
                                            filetypes=[("PNG", "*.png"), ("All files", "*.*")])
        if path:
            self.output_var.set(path)

    def _write_log(self, text):
        self._log.config(state="normal")
        self._log.insert("end", text + "\n")
        self._log.see("end")
        self._log.config(state="disabled")

    def _run(self):
        input_path = self.input_var.get().strip()
        if not input_path:
            self._write_log("Select an input image first.")
            return

        output_path = self.output_var.get().strip()
        if not output_path or output_path == "(auto)":
            p = Path(input_path)
            output_path = str(p.parent / f"{p.stem}_upscaled.png")
            self.output_var.set(output_path)

        self._run_btn.config(state="disabled", text="Running…")
        self._write_log(f"Input:  {input_path}")
        self._write_log(f"Output: {output_path}")

        run_upscale(
            input_path, output_path,
            scale=self.scale_var.get(),
            texture_strength=self.texture_var.get(),
            face_enhance=self.face_var.get(),
            face_weight=self.face_weight_var.get(),
            log_cb=lambda msg: self.after(0, self._write_log, msg),
            done_cb=lambda ok: self.after(0, self._finish, ok, output_path),
        )

    def _finish(self, success, output_path):
        self._run_btn.config(state="normal", text="Run")
        if success:
            self._write_log(f"\nDone! Saved to:\n{output_path}")
        else:
            self._write_log("\nFailed. See log above.")


if __name__ == "__main__":
    App().mainloop()
