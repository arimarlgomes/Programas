"""
dashboard_temp.py  ──────────
Interface em Tkinter que:
  • Lê uma temperatura a cada X s (pode ser sensor real ou simulated)
  • Atualiza um rótulo com o valor atual
  • Mantém um gráfico em tempo real (matplotlib embedado)
Para rodar: python dashboard_temp.py
"""

import random            # troque por leitura do seu sensor
import threading
import time
from collections import deque

import tkinter as tk
from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


# ────────── PARÂMETROS BÁSICOS ────────── #
INTERVALO_S = 1          # segundos entre leituras
MAX_PONTOS  = 120        # quantos pontos manter no gráfico


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Monitor de Temperatura")
        self.geometry("720x480")
        self.resizable(False, False)

        # buffer circular para histórico
        self.temps = deque(maxlen=MAX_PONTOS)
        self.times = deque(maxlen=MAX_PONTOS)
        self.start_time = time.time()

        # === Widgets básicos ===
        self.valor_lbl = ttk.Label(self, text="-- °C",
                                   font=("Helvetica", 48, "bold"))
        self.valor_lbl.pack(pady=10)

        # === Figura matplotlib ===
        fig = Figure(figsize=(7, 3), dpi=100)
        self.ax = fig.add_subplot(111)
        self.ax.set_title("Temperatura (°C) vs Tempo (s)")
        self.ax.set_xlabel("t (s)")
        self.ax.set_ylabel("Temp (°C)")
        self.line, = self.ax.plot([], [], lw=2)

        self.canvas = FigureCanvasTkAgg(fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Inicia thread de aquisição
        threading.Thread(target=self.aquisicao,
                         daemon=True).start()

        # Inicia ciclo de refresh da GUI
        self.after(200, self.update_gui)

    # --------------------------------------------------------
    def aquisicao(self):
        """Thread que lê a temperatura periodicamente."""
        while True:
            temp = self.ler_sensor()          # troque por leitura real
            t = time.time() - self.start_time
            self.temps.append(temp)
            self.times.append(t)
            time.sleep(INTERVALO_S)

    # --------------------------------------------------------
    def ler_sensor(self):
        """
        Substitua este método pelo código que lê o sensor verdadeiro:
        - via porta serial (pyserial)
        - via I2C (smbus2)
        - via HTTP/REST, etc.
        Aqui, sorteamos um valor entre 24 °C e 30 °C.
        """
        return round(random.uniform(24, 30), 1)

    # --------------------------------------------------------
    def update_gui(self):
        """Atualiza rótulo e gráfico."""
        if self.temps:
            temp_atual = self.temps[-1]
            self.valor_lbl.config(text=f"{temp_atual:.1f} °C")

            # Atualiza dados do gráfico
            self.line.set_data(self.times, self.temps)
            self.ax.relim()
            self.ax.autoscale_view(True, True, True)
            self.canvas.draw_idle()

        # agenda próxima atualização
        self.after(500, self.update_gui)


if __name__ == "__main__":
    App().mainloop()
