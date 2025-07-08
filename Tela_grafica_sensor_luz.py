"""
radar_lux_webcam.py – Radar visual para um “sensor de luz” que usa a webcam do
notebook como fonte de intensidade.

Como funciona
-------------
• Cada vez que o feixe rotativo (estilo radar) avança, lemos um frame da câmera
  (cv2.VideoCapture).  Calculamos o valor médio de luminância (0–255) e o
  convertemos em lux no intervalo 0–Amplitude.
• A intensidade obtida é colocada no buffer de 360 posições – uma por grau – e o
  ponto é plotado no raio proporcional + cor verde proporcional, tal e qual na
  versão simulada.
• Painel de controle (Tkinter) mantém todos os parâmetros ajustáveis + botões
  Start/Stop/Reset.

Dependências
------------
> pip install opencv-python numpy

Tkinter já vem com o Python padrão em Windows/macOS.  Em algumas distros Linux
pode ser preciso instalar o pacote python3‑tk.

Execute com:
    python radar_lux_webcam.py
"""

import math
import time
import tkinter as tk
from tkinter import ttk

import cv2                 # OpenCV para capturar webcam
import numpy as np

# ─── Constantes de layout ───────────────────────────────────
SIZE   = 480           # Lado da janela (px)
MARGEM = 12            # Margem até o círculo externo
RAIO   = (SIZE // 2) - MARGEM
RINGS  = 4             # Círculos concêntricos

class RadarLuxCam(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Radar – Lux via Webcam")
        self.resizable(False, False)

        # ── Variáveis de parâmetros ─────────────────────────
        self.amplitude_var = tk.IntVar(value=1000)   # lux máximo
        self.sweep_var     = tk.IntVar(value=2)      # deg por passo
        self.interval_var  = tk.IntVar(value=60)     # ms entre quadros

        # ── Estado interno ─────────────────────────────────
        self.readings = [0.0] * 360
        self.angle    = 0
        self.running  = False

        # OpenCV – abre câmera 0
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW if hasattr(cv2, 'CAP_DSHOW') else 0)
        if not self.cap.isOpened():
            raise RuntimeError("Não foi possível abrir a webcam (device 0)")

        # UI
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ───────────────────────────────────────────────────────
    def _build_ui(self):
        ctrl = ttk.Frame(self)
        ctrl.pack(side=tk.TOP, fill=tk.X, padx=4, pady=4)

        ttk.Label(ctrl, text="Amplitude (lux máx):").grid(row=0, column=0, sticky="w")
        ttk.Scale(ctrl, from_=100, to=5000, variable=self.amplitude_var,
                  orient="horizontal", length=140).grid(row=0, column=1, padx=4)

        ttk.Label(ctrl, text="Sweep (°/passo):").grid(row=0, column=2, sticky="w")
        ttk.Scale(ctrl, from_=1, to=10, variable=self.sweep_var,
                  orient="horizontal", length=120).grid(row=0, column=3, padx=4)

        ttk.Label(ctrl, text="Intervalo (ms):").grid(row=0, column=4, sticky="w")
        ttk.Scale(ctrl, from_=20, to=200, variable=self.interval_var,
                  orient="horizontal", length=100).grid(row=0, column=5, padx=4)

        ttk.Button(ctrl, text="Start", command=self.start).grid(row=0, column=6, padx=6)
        ttk.Button(ctrl, text="Stop",  command=self.stop).grid(row=0, column=7, padx=6)
        ttk.Button(ctrl, text="Reset", command=self.reset).grid(row=0, column=8, padx=6)

        self.lux_label = ttk.Label(ctrl, text="-- lux", font=("Helvetica", 14, "bold"))
        self.lux_label.grid(row=0, column=9, padx=10)

        # Canvas Radar
        self.canvas = tk.Canvas(self, width=SIZE, height=SIZE, bg="black", highlightthickness=0)
        self.canvas.pack()
        self._draw_grid()

    # ───────────────────────────────────────────────────────
    def _draw_grid(self):
        cx = cy = SIZE // 2
        step = RAIO // RINGS
        for r in range(step, RAIO + 1, step):
            self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline="#003300")
        self.canvas.create_line(cx, cy - RAIO, cx, cy + RAIO, fill="#003300")
        self.canvas.create_line(cx - RAIO, cy, cx + RAIO, cy, fill="#003300")

    # ── Leitura da webcam ───────────────────────────────────
    def _read_lux_from_camera(self):
        ret, frame = self.cap.read()
        if not ret:
            return 0.0
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mean_intensity = float(np.mean(gray))  # 0–255
        amp = self.amplitude_var.get()
        lux = (mean_intensity / 255.0) * amp
        return lux

    # ───────────────────────────────────────────────────────
    def start(self):
        if not self.running:
            self.running = True
            self._schedule_next()

    def stop(self):
        self.running = False

    def reset(self):
        self.readings = [0.0] * 360
        self.canvas.delete("dynamic")
        self.angle = 0

    # ───────────────────────────────────────────────────────
    def _schedule_next(self):
        if self.running:
            self.after(self.interval_var.get(), self._update)

    def _update(self):
        if not self.running:
            return

        lux_val = self._read_lux_from_camera()
        self.readings[self.angle] = lux_val
        self.lux_label.configure(text=f"{lux_val:4.0f} lux")

        # Redesenho
        self.canvas.delete("dynamic")
        self._draw_points()
        self._draw_beam()

        # Avança ângulo
        self.angle = (self.angle + self.sweep_var.get()) % 360

        self._schedule_next()

    # ───────────────────────────────────────────────────────
    def _lux_to_color(self, lux):
        amp = self.amplitude_var.get()
        g = int(50 + 205 * lux / amp)
        g = max(0, min(255, g))
        return f"#00{g:02x}00"

    def _draw_points(self):
        cx = cy = SIZE // 2
        amp = self.amplitude_var.get()
        for ang, lux in enumerate(self.readings):
            if lux <= 0:
                continue
            r = (lux / amp) * RAIO
            theta = math.radians(ang)
            x = cx + r * math.cos(theta)
            y = cy - r * math.sin(theta)
            color = self._lux_to_color(lux)
            self.canvas.create_oval(x-2, y-2, x+2, y+2, fill=color, outline=color, tags="dynamic")

    def _draw_beam(self):
        cx = cy = SIZE // 2
        theta = math.radians(self.angle)
        x = cx + RAIO * math.cos(theta)
        y = cy - RAIO * math.sin(theta)
        self.canvas.create_line(cx, cy, x, y, fill="#00ff00", width=2, tags="dynamic")

    # ───────────────────────────────────────────────────────
    def _on_close(self):
        self.stop()
        if self.cap.isOpened():
            self.cap.release()
        self.destroy()


if __name__ == "__main__":
    RadarLuxCam().mainloop()
