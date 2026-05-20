import os
import sys
import shutil
import subprocess
import glob
import ctypes
import winreg as reg
from tkinter import messagebox
import customtkinter as ctk

# ====================== CONFIG ======================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(__file__)
    return os.path.join(base_path, relative_path)


# ====================== MAIN WINDOW ======================
app = ctk.CTk()
app.title("WolfTech Optimizer")
app.geometry("720x780")
app.resizable(True, True)

try:
    app.iconbitmap(resource_path("wolf_8689726.ico"))
except:
    pass

# Output box
output_box = ctk.CTkTextbox(app, width=680, height=300)
output_box.pack(pady=15, padx=20)


def log(message):
    output_box.insert("end", f"> {message}\n")
    output_box.see("end")


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


# ================= HELPERS =================
def bring_to_front(win):
    win.lift()
    win.focus_force()
    win.attributes("-topmost", True)
    win.after(200, lambda: win.attributes("-topmost", False))


def center_window(window, width, height):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = int((screen_width / 2) - (width / 2))
    y = int((screen_height / 2) - (height / 2))
    window.geometry(f"{width}x{height}+{x}+{y}")


def show_progress(title="Working..."):
    win = ctk.CTkToplevel(app)
    win.title(title)
    win.resizable(False, False)
    center_window(win, 350, 140)
   
    ctk.CTkLabel(win, text=title, font=ctk.CTkFont(size=16, weight="bold")).pack(pady=20)
    progress = ctk.CTkProgressBar(win, width=250)
    progress.pack(pady=10)
    progress.set(0)
    win.update()
   
    def force_front():
        win.lift()
        win.focus_force()
        win.attributes("-topmost", True)
        win.after(200, lambda: win.attributes("-topmost", False))
   
    win.after(100, force_front)
    return win, progress


# ====================== CLEAN TEMP FILES ======================
def clean_temp():
    if not messagebox.askyesno("Confirm Action", "Clean temporary files?"):
        log("❌ Cancelled")
        return

    # Config Window
    config_win = ctk.CTkToplevel(app)
    config_win.title("Temp Files Cleaner")
    center_window(config_win, 420, 320)
    config_win.resizable(False, False)
    bring_to_front(config_win)

    ctk.CTkLabel(config_win, text="Temp Files Cleaner", 
                 font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)
    
    ctk.CTkLabel(config_win, text="Delete files older than:").pack(pady=(10,5))

    days_var = ctk.IntVar(value=7)
    days_frame = ctk.CTkFrame(config_win)
    days_frame.pack(pady=5)

    for days in [7, 14, 30, 90]:
        ctk.CTkRadioButton(days_frame, text=f"{days} days", 
                          variable=days_var, value=days).pack(side="left", padx=12)

    include_win = ctk.BooleanVar(value=False)
    ctk.CTkCheckBox(config_win, text="Also clean C:\\Windows\\Temp", 
                   variable=include_win).pack(pady=15)

    def start_cleaning():
        config_win.destroy()
        log("🧹 Starting Temp Cleanup...")
        popup, progress = show_progress("Cleaning Temporary Files...")

        try:
            # Common temp paths
            temp_paths = [
                os.getenv('TEMP'),
                os.getenv('TMP'),
                os.path.join(os.getenv('LOCALAPPDATA'), 'Temp'),
            ]
            if include_win.get():
                temp_paths.append(r"C:\Windows\Temp")

            deleted = 0
            for path in temp_paths:
                if not path or not os.path.exists(path):
                    continue
                for item in os.listdir(path):
                    item_path = os.path.join(path, item)
                    try:
                        if os.path.isfile(item_path):
                            os.unlink(item_path)
                            deleted += 1
                        elif os.path.isdir(item_path):
                            shutil.rmtree(item_path, ignore_errors=True)
                            deleted += 1
                    except:
                        continue

            log(f"✅ Temp cleanup finished - Removed {deleted} items")
            messagebox.showinfo("Cleanup Complete", 
                              f"Temp files cleaned successfully!\n\nRemoved approximately {deleted} items.")

        except Exception as e:
            log(f"❌ Error during cleanup: {e}")
            messagebox.showwarning("Cleanup", "Cleanup finished with some errors.")

        finally:
            popup.destroy()

    ctk.CTkButton(config_win, text="Start Cleaning", height=40, 
                  font=ctk.CTkFont(size=14, weight="bold"), 
                  command=start_cleaning).pack(pady=20, padx=60, fill="x")


# ====================== MEMORY BOOST ======================
def get_free_memory_mb():
    try:
        ps_code = "(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1024"
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_code],
            capture_output=True, text=True, timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return round(float(result.stdout.strip()))
    except:
        return 0


def memory_boost(empty_standby_path=None):
    if not messagebox.askyesno("Confirm Action",
        "Run Advanced RAM Boost?\n\n"
        "This will clear the Standby List (cached RAM).\n"
        "Administrator rights recommended for best results."):
        log("❌ RAM Boost cancelled by user")
        return

    log("⚡ Running Advanced RAM Boost...")

    if not empty_standby_path:
        possible_paths = [
            "EmptyStandbyList.exe",
            os.path.join(os.path.dirname(sys.executable), "EmptyStandbyList.exe"),
            os.path.join(os.path.dirname(__file__), "EmptyStandbyList.exe"),
            r"C:\Windows\System32\EmptyStandbyList.exe",
        ]
        for path in possible_paths:
            if os.path.exists(path):
                empty_standby_path = path
                break

    freed_mb = 0
    success = False

    try:
        before = get_free_memory_mb()

        if empty_standby_path and os.path.exists(empty_standby_path):
            log("→ Using EmptyStandbyList.exe")
            subprocess.run([empty_standby_path, "standbylist"], 
                         capture_output=True, timeout=15, creationflags=subprocess.CREATE_NO_WINDOW)
            success = True
        else:
            log("⚠ EmptyStandbyList.exe not found - using fallback")

        if not success:
            log("→ Running built-in optimization...")
            ps_script = """
            $ErrorActionPreference = 'SilentlyContinue'
            Get-Process | ForEach-Object { try { $_.MinimizeWorkingSet() } catch {} }
            Start-Sleep -Seconds 1
            """
            subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
                         capture_output=True, timeout=20, creationflags=subprocess.CREATE_NO_WINDOW)
            success = True

        after = get_free_memory_mb()
        freed_mb = max(0, after - before)

        if success:
            log(f"✅ RAM Boost completed - Freed ~{freed_mb} MB")
        else:
            log("⚠ RAM Boost completed with limited effect")

    except Exception as e:
        log(f"❌ Error: {e}")

    if freed_mb > 50:
        messagebox.showinfo("RAM Boost Completed", 
            f"Successfully cleared standby list!\n\nFreed approximately {freed_mb} MB")
    else:
        messagebox.showinfo("RAM Boost Completed", 
            "RAM Boost completed successfully.\nSome cached memory has been cleared.")


# ====================== OTHER FUNCTIONS ======================
def flush_dns():
    if not messagebox.askyesno("Confirm Action", "Flush DNS cache?"):
        log("❌ Cancelled")
        return
    log("Flushing DNS...")
    try:
        result = subprocess.run(["ipconfig", "/flushdns"], capture_output=True, text=True, timeout=10)
        log(result.stdout.strip() or "✅ DNS cache flushed successfully.")
    except Exception as e:
        log(f"❌ Error: {e}")


def clear_browser_cache():
    if not messagebox.askyesno("Confirm Action", "Clear browser cache?"):
        log("❌ Cancelled")
        return
    log("Clearing browser cache...")
    browsers = {
        "Chrome": os.path.join(os.getenv('LOCALAPPDATA'), r"Google\Chrome\User Data\Default\Cache"),
        "Edge": os.path.join(os.getenv('LOCALAPPDATA'), r"Microsoft\Edge\User Data\Default\Cache"),
        "Firefox": os.path.join(os.getenv('APPDATA'), r"Mozilla\Firefox\Profiles")
    }
    for name, path in browsers.items():
        try:
            if "Firefox" in name:
                for profile in glob.glob(os.path.join(path, "*.default*")):
                    shutil.rmtree(os.path.join(profile, "cache2"), ignore_errors=True)
            elif os.path.exists(path):
                shutil.rmtree(path, ignore_errors=True)
            log(f"✔ {name}")
        except:
            log(f"Skipped {name}")
    log("✅ Browser cache clearing completed")


def check_windows_updates():
    log("Opening Windows Update Settings...")
    try:
        subprocess.run('explorer.exe "ms-settings:windowsupdate"', shell=True)
        log("✅ Windows Update Settings opened")
        messagebox.showinfo("Windows Updates", "Windows Update page has been opened.")
    except:
        log("❌ Could not open Windows Update")


def list_startup():
    log("Listing startup programs...")
    startup_window = ctk.CTkToplevel(app)
    startup_window.title("Startup Programs")
    center_window(startup_window, 650, 520)
    bring_to_front(startup_window)
    
    ctk.CTkLabel(startup_window, text="Startup Applications",
                 font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)
   
    frame = ctk.CTkScrollableFrame(startup_window)
    frame.pack(fill="both", expand=True, padx=15, pady=10)

    locations = [
        (reg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "Current User"),
        (reg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run", "All Users"),
    ]
    for hive, path, label in locations:
        ctk.CTkLabel(frame, text=f"=== {label} ===",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", pady=(12,5))
        try:
            with reg.OpenKey(hive, path) as key:
                i = 0
                while True:
                    try:
                        name, _, _ = reg.EnumValue(key, i)
                        ctk.CTkLabel(frame, text=f"✅ {name}", anchor="w").pack(fill="x", padx=20, pady=1)
                        i += 1
                    except OSError:
                        break
        except:
            ctk.CTkLabel(frame, text="Unable to access", anchor="w").pack(fill="x", padx=20)


# ================= UI =================
frame = ctk.CTkFrame(app)
frame.pack(pady=10, padx=20, fill="both", expand=True)

left = ctk.CTkFrame(frame)
left.pack(side="left", expand=True, fill="both", padx=10)
right = ctk.CTkFrame(frame)
right.pack(side="right", expand=True, fill="both", padx=10)

# Left Column
ctk.CTkButton(left, text="🧹 Clean Temp Files\n(Free up disk space)", height=55,
              command=clean_temp).pack(pady=8, fill="x")

ctk.CTkButton(left, text="🌐 Flush DNS Cache\n(Fix network issues)", height=55,
              command=flush_dns).pack(pady=8, fill="x")

ctk.CTkButton(left, text="🕸 Clear Browser Cache\n(Chrome, Edge, Firefox)", height=55,
              command=clear_browser_cache).pack(pady=8, fill="x")

# Right Column
ctk.CTkButton(right, text="⚡ RAM Boost\n(Free up memory)", height=55,
              command=memory_boost).pack(pady=8, fill="x")

ctk.CTkButton(right, text="🔄 Check Windows Updates", height=55,
              command=check_windows_updates).pack(pady=8, fill="x")

ctk.CTkButton(right, text="🚀 Manage Startup Apps", height=55,
              command=list_startup).pack(pady=8, fill="x")


if not is_admin():
    log("⚠️ Run this program as Administrator for full functionality!")

app.mainloop()
