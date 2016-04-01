import tkinter as tk
from tkinter .filedialog import askdirectory
from tkinter import ttk


class Gui:
    def __init__(self):
        self.root = tk.Tk()
        self.make_gui()

    def make_gui(self):
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(expand=True, fill=tk.BOTH, pady=10, padx=10)

        # Make the username label and box
        ttk.Label(self.main_frame, text='Username:').grid(row=0, column=2)

        self.username = tk.StringVar()
        self.username_box = ttk.Entry(self.main_frame, 
                textvariable=self.username)
        self.username_box.grid(row=0, column=3, sticky='nsew')

        # Make the password label and box
        ttk.Label(self.main_frame, text='Password:').grid(row=1, column=2)

        self.password = tk.StringVar()
        self.password_box = ttk.Entry(self.main_frame, 
                textvariable=self.password)
        self.password_box.grid(row=1, column=3, sticky='nsew')

        # Make the savefile label and box
        self.savefile_btn = ttk.Button(self.main_frame, text='Browse',
                command=self.ask_find_directory)
        self.savefile_btn.grid(row=2, column=2)

        self.savefile = tk.StringVar()
        self.savefile_box = ttk.Entry(self.main_frame, 
                textvariable=self.savefile)
        self.savefile_box.grid(row=2, column=3, sticky='nsew')

        # Make the "GO" button
        self.go_button = ttk.Button(self.main_frame, text='Start',
                command=self.start)
        self.go_button.grid(row=4, column=3, sticky='es')

        # Set up the column weightings
        self.main_frame.columnconfigure(3, weight=1)
        self.main_frame.columnconfigure(0, weight=5)
        self.main_frame.rowconfigure(3, weight=1)

        # Make the listbox (and scrollbar) for selecting units
        self.unit_box = tk.Listbox(self.main_frame, relief=tk.SUNKEN)
        self.unit_box.grid(row=0, column=0, 
                rowspan=5, columnspan=2, 
                sticky='nsew')

        scrollbar = tk.Scrollbar(self.main_frame)
        scrollbar.config(command=self.unit_box.yview)
        self.unit_box.config(yscrollcommand=scrollbar.set)

        scrollbar.grid(row=0, column=1, rowspan=5, sticky='nsew')

    def start(self):
        pass

    def ask_find_directory(self):
        save_location = askdirectory()
        self.savefile.set(save_location)

    def mainloop(self):
        self.root.mainloop()

    def quit(self):
        self.root.destroy()


if __name__ == "__main__":
    g = Gui()
    g.mainloop()
