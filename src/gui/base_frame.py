# src/gui/base_frame.py

import tkinter as tk

class BaseFrame(tk.Frame):
    """
    Kelas dasar untuk frame-frame GUI.
    Menyediakan referensi ke main_app dan metode untuk membersihkan frame.
    """
    def __init__(self, parent, main_app):
        """
        Inisialisasi BaseFrame.

        Args:
            parent: Widget parent (biasanya jendela root atau frame kontainer).
            main_app: Referensi ke instance kelas MainApp (untuk navigasi antar frame).
        """
        super().__init__(parent)
        self.main_app = main_app
        self.parent = parent

    def show(self):
        """Menampilkan frame ini."""
        self.pack(expand=True, fill='both')

    def hide(self):
        """Menyembunyikan frame ini."""
        self.pack_forget()

    def clear_widgets(self):
        """Menghapus semua widget dari frame ini."""
        for widget in self.winfo_children():
            widget.destroy()

    # Metode placeholder untuk inisialisasi UI spesifik frame turunan
    def create_widgets(self):
        """Metode placeholder untuk membuat widget spesifik frame turunan."""
        pass
