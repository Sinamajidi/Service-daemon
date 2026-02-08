import tkinter as tk
from tkinter import ttk
import requests

class DBVisualizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Database Visualizer")
        self.root.geometry("800x600")
        self.create_widgets()

    def create_widgets(self):
        ttk.Label(self.root, text="Database Visualizer Application", font=("Arial", 16)).pack(pady=10)

        self.filter_frame = ttk.Frame(self.root)
        self.filter_frame.pack(pady=10)
        ttk.Label(self.filter_frame, text="Filter:").grid(row=0, column=0, padx=5)
        self.filter_entry = ttk.Entry(self.filter_frame)
        self.filter_entry.grid(row=0, column=1, padx=5)
        self.filter_button = ttk.Button(self.filter_frame, text="Apply Filter", command=self.apply_filter)
        self.filter_button.grid(row=0, column=2, padx=5)

        self.table = ttk.Treeview(self.root, columns=("ID", "Data"), show="headings")
        self.table.heading("ID", text="ID")
        self.table.heading("Data", text="Data")
        self.table.pack(pady=20, fill=tk.BOTH, expand=True)

        self.update_button = ttk.Button(self.root, text="Update Data", command=self.update_data)
        self.update_button.pack(pady=10)

    def apply_filter(self):
        filter_value = self.filter_entry.get()
        # Logic to filter data based on filter_value

    def update_data(self):
        # Logic to fetch and display data from the backend API
        response = requests.get('https://api.yourbackend.com/data')
        data = response.json()
        for item in data:
            self.table.insert('', 'end', values=(item['id'], item['data']))

if __name__ == '__main__':
    root = tk.Tk()
    app = DBVisualizerApp(root)
    root.mainloop()