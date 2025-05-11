# src/gui/user_profile_frame.py

import tkinter as tk
from tkinter import ttk, messagebox
from src.database.user_dao import update_user_profile, get_user_profile

class UserProfileFrame(ttk.Frame):
    def __init__(self, parent, controller, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.controller = controller
        self.user_id = None
        self.create_widgets()

    def set_user_id(self, user_id):
        """Set the user ID and load profile data"""
        self.user_id = user_id
        self.load_profile()

    def create_widgets(self):
        # Main container
        self.main_container = ttk.Frame(self)
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Profile form frame
        form_frame = ttk.LabelFrame(self.main_container, text="My Profile", padding=10)
        form_frame.pack(fill="x", pady=10)
        
        # Full Name
        ttk.Label(form_frame, text="Full Name:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.full_name_var = tk.StringVar()
        self.full_name_entry = ttk.Entry(form_frame, textvariable=self.full_name_var)
        self.full_name_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        # NIM/NIP
        ttk.Label(form_frame, text="NIM/NIP:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.nim_nip_var = tk.StringVar()
        self.nim_nip_entry = ttk.Entry(form_frame, textvariable=self.nim_nip_var)
        self.nim_nip_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        
        # Email
        ttk.Label(form_frame, text="Email:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.email_var = tk.StringVar()
        self.email_entry = ttk.Entry(form_frame, textvariable=self.email_var)
        self.email_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        
        # Update button
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        ttk.Button(
            btn_frame, 
            text="Update Profile", 
            command=self.update_profile
        ).pack(side="left", padx=5)
        
        ttk.Button(
            btn_frame,
            text="Back",
            command=lambda: self.controller.show_main_app_frame(self.controller.user_data)
        ).pack(side="left", padx=5)
        
        # Configure grid weights
        form_frame.columnconfigure(1, weight=1)

    def load_profile(self):
        """Load user profile data"""
        if self.user_id:
            profile = get_user_profile(self.user_id)
            if profile:
                self.full_name_var.set(profile['FullName'])
                self.nim_nip_var.set(profile['NIM_NIP'])
                self.email_var.set(profile['Email'])

    def update_profile(self):
        """Update user profile"""
        if not self.user_id:
            return
            
        full_name = self.full_name_var.get().strip()
        nim_nip = self.nim_nip_var.get().strip()
        email = self.email_var.get().strip()
        
        if not all([full_name, nim_nip, email]):
            messagebox.showwarning("Input Error", "All fields are required!")
            return
            
        if update_user_profile(
            user_id=self.user_id,
            full_name=full_name,
            nim_nip=nim_nip,
            email=email
        ):
            messagebox.showinfo("Success", "Profile updated successfully!")
        else:
            messagebox.showerror("Error", "Failed to update profile")

    def show(self):
        """Show the frame"""
        self.pack(fill="both", expand=True)
        self.load_profile()

    def hide(self):
        """Hide the frame"""
        self.pack_forget()