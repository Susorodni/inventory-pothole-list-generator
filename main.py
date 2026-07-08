# -*- coding: utf-8 -*-
"""
Created on Mon Jun 15 09:45:17 2026

TO COMPILE:

USE: pyinstaller --clean --onefile --noconsole --collect-all matplotlib main.py

@author: c10265
"""

import os
import tkinter as tk
from tkinter import Tk, filedialog, messagebox

import pandas as pd

from src.asset_builder import mark_to_pothole_sample
from src.constants import SUPPORTED_FILE_EXTENSIONS


class App:
    """

    The main app object that will run inside the Tkinter environment.
    """

    def __init__(self, root: Tk) -> None:
        """

        Initializes the app object class.

        Args:
            root (Tk): the root Tkinter object

        Returns:
            None
        """

        # Initialize Tkinter window
        self.root = root
        self.root.title("Inventory Pothole List Generator vA")
        self.root.geometry("350x125")

        # Pop the window to the top
        self.root.attributes("-topmost", True)
        self.root.lift()
        self.root.attributes("-topmost", False)

        # initialize dataframe object
        self.df = None

        # Populate the window to show whether the file has been selected,
        # and the button to select the file
        self.file_label = tk.Label(root, text="No file selected")
        self.file_label.pack(padx=10, pady=5)
        self.file_button = tk.Button(
            root, text="Choose file...", command=self.load_file
        )
        self.file_button.pack(padx=10, pady=5)

        # once the file has been properly selected, the user can
        # import the assets into the asset builder
        self.run_button = tk.Button(
            root, text="Process Assets", command=self.run_import
        )
        self.run_button.pack(padx=10, pady=15)

    def load_file(self) -> None:
        """

        Prompts the user for a proper file to be loaded into the program,
        then reads and converts the data into a pandas DataFrame. Informs the
        user if the reading of the file had an error.

        Returns:
            None
        """
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("All supported filetypes", SUPPORTED_FILE_EXTENSIONS),
                ("Excel Files", SUPPORTED_FILE_EXTENSIONS[0:-1]),
                ("CSV Files", SUPPORTED_FILE_EXTENSIONS[-1]),
            ]
        )

        # grabs the extension of the selected file to later check if it
        # is a compatible filetype
        ext = os.path.splitext(file_path)[1].lower()

        # end the file loading if no file was selected
        if not file_path:
            return

        # depending on the filetype, pandas has to read the file
        # with different commands. If not compatible, an error is thrown.
        try:
            if ext in [".xlsx", ".xls"]:
                self.df = pd.read_excel(file_path)
            elif ext == ".csv":
                self.df = pd.read_csv(file_path)
        except Exception as e:
            messagebox.showerror("Reading Error", str(e))
            return

        # updates the label with the file path to show the user that the file
        # was properly selected.
        self.file_label.config(text=file_path)

    def run_import(self) -> None:
        """

        Executed when the user clicks the "Import Assets" button. Sends the
        DataFrame to the asset_builder, then filters out any assets that have
        invalid conditions as defined in the constants file. Once completed,
        prompts the user to save the resulting file.

        Returns:
            None
        """

        # does not proceed if no file was selected already
        if self.df is None:
            messagebox.showwarning("Warning", "Load an Excel or CSV file first!")
            return

        try:

            # since we are using a dynamic loop, a seperate list is used
            self.processed_df = mark_to_pothole_sample(self.df)

            save_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel Files", SUPPORTED_FILE_EXTENSIONS[0:-1])],
                title="Save File",
            )

            if not save_path:
                messagebox.showwarning(
                    "No file location saved", "Please try again and save to a location."
                )
                return

            # to properly save the assets as an Excel file, they first must
            # be put into a dictionary so that it can be handled by pandas
            self.processed_df.to_excel(save_path, index=False)

            messagebox.showinfo("Success", f"{len(self.processed_df)} assets imported.")

        except Exception as e:
            messagebox.showerror("Asset Building Error", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)

    # Properly close the app if prompted to
    def on_closing():
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
