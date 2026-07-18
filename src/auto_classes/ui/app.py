import customtkinter as ctk


class App(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Auto Classes")
        self.geometry("900x600")


def run() -> None:
    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")
    app = App()
    app.mainloop()
