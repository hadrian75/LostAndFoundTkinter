# src/gui/admin_panel_user_frame.py

import tkinter as tk
from tkinter import ttk, messagebox
from src.database.user_dao import get_all_users, toggle_admin_status, delete_user
from .base_frame import BaseFrame

class AdminPanelUserFrame(BaseFrame):
    def __init__(self, parent, main_app):
        super().__init__(parent, main_app)
        self.parent = parent
        # Create widgets once during initialization
        self._create_widgets() # Renamed and called from init

    def _create_widgets(self):
        """Internal method to create all GUI widgets."""
        # Header
        header_frame = tk.Frame(self, bg='#333', padx=10, pady=10)
        header_frame.pack(fill='x')

        tk.Label(
            header_frame,
            text="User Management",
            font=('Arial', 16, 'bold'),
            fg='white',
            bg='#333'
        ).pack(side='left')

        # Table Frame
        table_frame = tk.Frame(self, padx=10, pady=10, bg='#f0f0f0')
        table_frame.pack(fill='both', expand=True)

        # Treeview with scrollbars
        self.tree = ttk.Treeview(
            table_frame,
            columns=('ID', 'Username', 'FullName', 'NIM_NIP', 'Email', 'IsAdmin'),
            show='headings',
            selectmode='browse'
        )

        # Define columns
        self.tree.heading('ID', text='ID', anchor='w')
        self.tree.heading('Username', text='Username', anchor='w')
        self.tree.heading('FullName', text='Full Name', anchor='w')
        self.tree.heading('NIM_NIP', text='NIM/NIP', anchor='w')
        self.tree.heading('Email', text='Email', anchor='w')
        self.tree.heading('IsAdmin', text='Is Admin', anchor='w')

        # Column widths
        self.tree.column('ID', width=50, minwidth=50)
        self.tree.column('Username', width=120, minwidth=120)
        self.tree.column('FullName', width=150, minwidth=150)
        self.tree.column('NIM_NIP', width=100, minwidth=100)
        self.tree.column('Email', width=200, minwidth=200)
        self.tree.column('IsAdmin', width=80, minwidth=80)

        # Add scrollbars
        y_scroll = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        x_scroll = ttk.Scrollbar(table_frame, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        # Grid layout
        self.tree.grid(row=0, column=0, sticky='nsew')
        y_scroll.grid(row=0, column=1, sticky='ns')
        x_scroll.grid(row=1, column=0, sticky='ew')

        # Configure grid weights
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # Button Frame
        button_frame = tk.Frame(self, bg='#f0f0f0', padx=10, pady=10)
        button_frame.pack(fill='x')

        self.toggle_admin_btn = tk.Button(
            button_frame,
            text="Toggle Admin Status",
            command=self.toggle_admin,
            bg='#4CAF50',
            fg='white',
            padx=10,
            pady=5,
            state='disabled'
        )
        self.toggle_admin_btn.pack(side='left', padx=5)

        self.delete_user_btn = tk.Button(
            button_frame,
            text="Delete User",
            command=self.delete_user,
            bg='#f44336',
            fg='white',
            padx=10,
            pady=5,
            state='disabled'
        )
        self.delete_user_btn.pack(side='left', padx=5)

        # Add the "Kembali ke Halaman Utama" button
        back_button = tk.Button(
            button_frame,
            text="Kembali ke Halaman Utama",
            command=lambda: self.main_app.show_main_app_frame(self.main_app.user_data),
            bg='#607D8B', # A different color for distinction
            fg='white',
            padx=10,
            pady=5
        )
        back_button.pack(side='right', padx=5) # Pack on the right side

        refresh_btn = tk.Button(
            button_frame,
            text="Refresh",
            command=self.load_users,
            bg='#2196F3',
            fg='white',
            padx=10,
            pady=5
        )
        refresh_btn.pack(side='right', padx=5) # Pack on the right side

        # Bind selection event
        self.tree.bind('<<TreeviewSelect>>', self.on_user_select)

    def load_users(self):
        """Load all users into the table"""
        # Clear existing data
        for item in self.tree.get_children():
            self.tree.delete(item)

        users = get_all_users()
        if users is None:
            messagebox.showerror("Error", "Failed to load users from database")
            return

        for user in users:
            self.tree.insert('', 'end', values=(
                user['UserID'],
                user['Username'],
                user['FullName'],
                user['NIM_NIP'],
                user['Email'],
                'Yes' if user['IsAdmin'] else 'No'
            ))

    def on_user_select(self, event):
        """Handle user selection from the table"""
        selected_item = self.tree.focus()
        if selected_item:
            self.toggle_admin_btn.config(state='normal')
            self.delete_user_btn.config(state='normal')
        else:
            self.toggle_admin_btn.config(state='disabled')
            self.delete_user_btn.config(state='disabled')

    def toggle_admin(self):
        """Toggle admin status of selected user"""
        selected_item = self.tree.focus()
        if not selected_item:
            return

        user_id = self.tree.item(selected_item)['values'][0]

        current_user_id = self.main_app.user_data.get('UserID') if self.main_app.user_data else None

        if user_id is not None and current_user_id is not None and user_id == current_user_id:
            messagebox.showwarning("Warning", "You cannot change your own admin status")
            return

        new_status = toggle_admin_status(user_id)
        if new_status is not None:
            self.load_users()
            messagebox.showinfo("Success", f"Admin status updated to {'Admin' if new_status else 'Regular user'}")
        else:
            messagebox.showerror("Error", "Failed to update admin status")

    def delete_user(self):
        """Delete selected user"""
        selected_item = self.tree.focus()
        if not selected_item:
            return

        user_id = self.tree.item(selected_item)['values'][0]
        username = self.tree.item(selected_item)['values'][1]

        current_user_id = self.main_app.user_data.get('UserID') if self.main_app.user_data else None

        if user_id is not None and current_user_id is not None and user_id == current_user_id:
            messagebox.showwarning("Warning", "You cannot delete your own account")
            return

        if messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete user '{username}'?\nThis action cannot be undone."
        ):
            if delete_user(user_id):
                self.load_users()
                messagebox.showinfo("Success", "User deleted successfully")
            else:
                messagebox.showerror("Error", "Failed to delete user")

    def show(self):
        """Show this frame and load initial data after access check."""
        is_admin = self.main_app.user_data.get('IsAdmin', False) if self.main_app.user_data else False
        if not is_admin:
            messagebox.showwarning("Akses Ditolak", "Anda tidak memiliki izin untuk mengakses halaman ini.")
            self.main_app.show_main_app_frame(self.main_app.user_data) # Redirect non-admins
            return

        super().show()
        self.load_users()
