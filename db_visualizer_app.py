import tkinter as tk
from tkinter import ttk
import sqlite3

class DatabaseVisualizer:
    def __init__(self, root):
        self.root = root
        self.root.title("Database Visualizer")
        
        self.create_widgets()
    
    def create_widgets(self):
        self.tree = ttk.Treeview(self.root)
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        self.scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=self.scrollbar.set)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.connect_to_database()

    def connect_to_database(self):
        conn = sqlite3.connect('your_database.db')  # Change database name as needed
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM your_table")  # Change with your SQL query as needed

        columns = [description[0] for description in cursor.description]
        self.tree["columns"] = columns
        for column in columns:
            self.tree.heading(column, text=column)
        
        for row in cursor.fetchall():
            self.tree.insert("", "end", values=row)
        
        conn.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = DatabaseVisualizer(root)
    root.mainloop()