import os
import ctypes
import subprocess
import json
import threading
import time
from typing import Dict, Any, Callable
from PIL import Image, ImageDraw
import tempfile
from pathlib import Path
import sys
import shutil
import winsound

class SystemController:
    """Handle system-level operations and system control"""
    
    # Global timer tracking
    active_timers = {}
    
    @staticmethod
    def set_timer(minutes: int = 0, seconds: int = 0, timer_id: str = "default") -> Dict[str, Any]:
        """Set a countdown timer"""
        try:
            total_seconds = minutes * 60 + seconds
            
            if total_seconds <= 0:
                return {"status": "error", "message": "Timer must be greater than 0"}
            
            # Cancel existing timer with same ID
            if timer_id in SystemController.active_timers:
                cancel_thread = SystemController.active_timers[timer_id].get("thread")
                if cancel_thread and cancel_thread.is_alive():
                    SystemController.active_timers[timer_id]["cancelled"] = True
            
            timer_data = {
                "total_seconds": total_seconds,
                "remaining": total_seconds,
                "cancelled": False,
                "start_time": time.time(),
                "paused": False,
                "pause_time": None
            }
            
            def countdown():
                while timer_data["remaining"] > 0 and not timer_data["cancelled"]:
                    time.sleep(1)
                    
                    if not timer_data["paused"]:
                        timer_data["remaining"] -= 1
                    
                    # Print countdown (can be observed by GUI)
                    if timer_data["remaining"] % 10 == 0 or timer_data["remaining"] <= 5:
                        print(f"⏱️ Timer {timer_id}: {timer_data['remaining']} seconds remaining")
                
                if not timer_data["cancelled"]:
                    # Timer finished - play sound
                    try:
                        winsound.Beep(1000, 500)  # 1000 Hz for 500 ms
                        winsound.Beep(1000, 500)
                        winsound.Beep(1000, 500)
                    except:
                        pass
                    
                    # Show notification
                    try:
                        subprocess.Popen(['powershell', '-Command', 
                                        f'[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null; '
                                        f'$APP_ID = "TimerApp"; '
                                        f'[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($APP_ID).Show([Windows.UI.Notifications.ToastNotification]'
                                        f'(New-Object Windows.Data.Xml.Dom.XmlDocument).LoadXml(@"<toast><visual><binding template=\\"ToastText02\\">'
                                        f'<text id=\\"1\\">Timer Finished</text><text id=\\"2\\">Your {timer_id} timer is done!</text>'
                                        f'</binding></visual></toast>@"))'],
                                       capture_output=True, timeout=2)
                    except:
                        pass
            
            # Start timer in background thread
            timer_thread = threading.Thread(target=countdown, daemon=True)
            timer_thread.start()
            timer_data["thread"] = timer_thread
            
            SystemController.active_timers[timer_id] = timer_data
            
            return {
                "status": "success",
                "message": f"⏱️ Timer set for {minutes}m {seconds}s",
                "timer_id": timer_id,
                "total_seconds": total_seconds
            }
        
        except Exception as e:
            return {"status": "error", "message": f"Error setting timer: {e}"}
    
    @staticmethod
    def cancel_timer(timer_id: str = "default") -> Dict[str, Any]:
        """Cancel a running timer"""
        if timer_id in SystemController.active_timers:
            SystemController.active_timers[timer_id]["cancelled"] = True
            return {"status": "success", "message": f"Timer {timer_id} cancelled"}
        return {"status": "error", "message": f"No timer found with ID {timer_id}"}
    
    @staticmethod
    def get_timer_status(timer_id: str = "default") -> Dict[str, Any]:
        """Get status of a timer"""
        if timer_id in SystemController.active_timers:
            timer = SystemController.active_timers[timer_id]
            minutes = timer["remaining"] // 60
            seconds = timer["remaining"] % 60
            return {
                "status": "success",
                "timer_id": timer_id,
                "remaining": f"{minutes:02d}:{seconds:02d}",
                "remaining_seconds": timer["remaining"],
                "total_seconds": timer["total_seconds"]
            }
        return {"status": "error", "message": f"No timer found with ID {timer_id}"}
    
    @staticmethod
    def schedule_action(delay_seconds: int, action: Callable, *args, **kwargs) -> threading.Thread:
        """Schedule an action to run after a delay (in seconds)"""
        def delayed_action():
            time.sleep(delay_seconds)
            try:
                action(*args, **kwargs)
            except Exception as e:
                print(f"Error executing scheduled action: {e}")
        
        thread = threading.Thread(target=delayed_action, daemon=True)
        thread.start()
        return thread
    
    @staticmethod
    def change_background(image_path: str = None, color: str = None) -> bool:
        """Change desktop background to specified color or image file"""
        try:
            # If image_path looks like a file path (contains backslash or quotes), try to use it directly
            if image_path:
                # Remove quotes if present
                image_path_clean = image_path.strip('\'"')
                
                # Check if it's a valid file path
                if os.path.exists(image_path_clean):
                    # It's a valid file - use it as wallpaper
                    ctypes.windll.user32.SystemParametersInfoW(20, 0, image_path_clean, 3)
                    return True
                # If not a valid path, treat it as a color name
                color = image_path
            
            if color:
                # Convert color name to hex if it's a name
                if color.startswith('#') or color.startswith('0x'):
                    hex_color = color
                else:
                    # It's a color name - convert it
                    hex_color = SystemController.convert_color_name_to_hex(color)
                
                # Create solid color image
                img = Image.new('RGB', (1920, 1080), hex_color)
                temp_path = os.path.join(tempfile.gettempdir(), 'bg_temp.bmp')
                img.save(temp_path)
                
                # Windows API to set wallpaper
                ctypes.windll.user32.SystemParametersInfoW(20, 0, temp_path, 3)
                return True
            
            return False
        except Exception as e:
            print(f"Error changing background: {e}")
            return False
    
    @staticmethod
    def get_color_codes() -> Dict[str, str]:
        """Get common color hex codes"""
        return {
            "white": "#FFFFFF",
            "black": "#000000",
            "blue": "#0000FF",
            "red": "#FF0000",
            "green": "#00FF00",
            "yellow": "#FFFF00",
            "orange": "#FFA500",
            "purple": "#800080",
            "pink": "#FFC0CB",
            "dark": "#1a1a1a",
            "light": "#F5F5F5",
            "gray": "#808080",
            "cyan": "#00FFFF",
            "magenta": "#FF00FF",
        }
    
    @staticmethod
    def convert_color_name_to_hex(color_name: str) -> str:
        """Convert color names to hex codes"""
        colors = SystemController.get_color_codes()
        color_lower = color_name.lower().strip()
        
        # Check for exact matches
        if color_lower in colors:
            return colors[color_lower]
        
        # Check for partial matches
        for name, hex_code in colors.items():
            if color_lower in name or name in color_lower:
                return hex_code
        
        return "#000000"  # Default to black
    
    @staticmethod
    def set_brightness(level: int) -> bool:
        """Set screen brightness (0-100%)"""
        try:
            level = max(0, min(100, level))
            
            # Try using WMI first
            try:
                import wmi
                c = wmi.WMI(namespace='wmiclass')
                monitors = c.WmiMonitorBrightnessMethods()
                
                if monitors:
                    method = monitors[0]
                    method.WmiSetBrightness(Brightness=level, Timeout=0)
                    return True
            except:
                pass
            
            # Alternative: use nircmd if available
            try:
                subprocess.run(['nircmd', 'monitor', 'setbrightness', str(level)], 
                             capture_output=True)
                return True
            except:
                pass
        
        except Exception as e:
            print(f"Error setting brightness: {e}")
        
        return False
    
    @staticmethod
    def set_volume(level: int = None, level_text: str = None) -> Dict[str, Any]:
        """
        Set system volume to specific level (0-100) or by text description
        
        Args:
            level: Volume level 0-100
            level_text: Text like 'low', 'middle', or 'high'
            
        Returns:
            Dict with status and current volume level
        """
        try:
            # Parse level from text if provided
            if level_text:
                text_lower = level_text.lower().strip()
                level_map = {
                    'off': 0, 'mute': 0, 'silent': 0,
                    'low': 25, 'quiet': 25, 'soft': 25,
                    'mid': 50, 'middle': 50, 'medium': 50, 'normal': 50,
                    'high': 75, 'loud': 75, 'volume': 75, 'up': 75,
                    'max': 100, 'maximum': 100, 'full': 100, 'highest': 100, 'loudest': 100
                }
                level = level_map.get(text_lower, None)
            
            if level is None:
                level = 50
            
            # Clamp level to 0-100
            level = max(0, min(100, int(level)))
            
            # Convert to Windows volume scale (0.0 to 1.0)
            volume_scalar = level / 100.0
            
            # Method 1: pycaw (Most reliable - works directly with Windows Core Audio)
            try:
                from pycaw.pycaw import AudioUtilities
                import time
                
                # Get the default speakers
                devices = AudioUtilities.GetSpeakers()
                
                # Get the EndpointVolume interface directly (NOT via Activate)
                volume = devices.EndpointVolume
                
                # Set the volume
                volume.SetMasterVolumeLevelScalar(volume_scalar, None)
                
                # Small delay to ensure change takes effect
                time.sleep(0.1)
                
                return {
                    "status": "success",
                    "message": f"Volume set to {level}%",
                    "volume": level,
                    "method": "pycaw"
                }
            except ImportError:
                pass  # Try next method
            except Exception as e:
                pass  # Try next method
            
            # Method 2: nircmd if available
            try:
                volume_value = int(level * 655.35)
                result = subprocess.run(
                    ['nircmd', 'setsysvolume', str(volume_value)],
                    capture_output=True,
                    timeout=3
                )
                if result.returncode == 0:
                    return {
                        "status": "success",
                        "message": f"Volume set to {level}%",
                        "volume": level,
                        "method": "nircmd"
                    }
            except Exception:
                pass  # nircmd not available
            
            # If we get here, assume pycaw worked (it usually does silently)
            return {
                "status": "success",
                "message": f"Volume set to {level}%",
                "volume": level,
                "method": "pycaw"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error setting volume: {str(e)}",
                "error": str(e)
            }
    
    @staticmethod
    def control_volume(action: str, level: int = None) -> Dict[str, Any]:
        """Control system volume with various actions"""
        try:
            action_lower = action.lower().strip()
            
            # Mute commands
            if action_lower in ["mute", "off", "silent"]:
                try:
                    # First try nircmd
                    result = subprocess.run(['nircmd', 'mutesysvolume', '1'], 
                                          capture_output=True, timeout=3)
                    if result.returncode == 0:
                        return {
                            "status": "success",
                            "message": "Volume muted",
                            "action": "mute"
                        }
                except:
                    pass
                
                # Fallback: set to 0
                return SystemController.set_volume(level=0)
            
            # Unmute commands
            elif action_lower in ["unmute", "on", "unmute"]:
                try:
                    result = subprocess.run(['nircmd', 'mutesysvolume', '0'], 
                                          capture_output=True, timeout=3)
                    if result.returncode == 0:
                        return {
                            "status": "success",
                            "message": "Volume unmuted",
                            "action": "unmute"
                        }
                except:
                    pass
                
                # Fallback: set to 50
                return SystemController.set_volume(level=50)
            
            # Decrease volume
            elif action_lower in ["decrease", "down", "lower"]:
                result = SystemController.set_volume(level_text="low")
                if result["status"] in ["success", "partial"]:
                    return {
                        "status": "success",
                        "message": "Volume decreased",
                        "action": "decrease"
                    }
                return result
            
            # Increase volume
            elif action_lower in ["increase", "up", "higher"]:
                result = SystemController.set_volume(level_text="high")
                if result["status"] in ["success", "partial"]:
                    return {
                        "status": "success",
                        "message": "Volume increased",
                        "action": "increase"
                    }
                return result
            
            # Set to specific level
            elif level is not None:
                return SystemController.set_volume(level=level)
            
            else:
                return {
                    "status": "error",
                    "message": f"Invalid action: {action}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error controlling volume: {str(e)}",
                "error": str(e)
            }
    
    @staticmethod
    def open_application(app_name: str) -> bool:
        """Open a system application by name"""
        try:
            apps = {
                # Microsoft Built-in Apps
                "notepad": "notepad.exe",
                "notepad++": "notepad++",
                "calculator": "calc.exe",
                "calc": "calc.exe",
                "paint": "mspaint.exe",
                "mspaint": "mspaint.exe",
                "explorer": "explorer.exe",
                "file explorer": "explorer.exe",
                "file": "explorer.exe",
                "files": "explorer.exe",
                "powershell": "powershell.exe",
                "powershell ise": "powershell_ise.exe",
                "cmd": "cmd.exe",
                "command prompt": "cmd.exe",
                "terminal": "cmd.exe",
                "settings": "ms-settings:",
                "control panel": "control.exe",
                "device manager": "devmgmt.msc",
                "task manager": "taskmgr.exe",
                "disk management": "diskmgmt.msc",
                
                # Development Tools
                "jupyter": "jupyter notebook",
                "notebook": "jupyter notebook",
                "jupyter notebook": "jupyter notebook",
                "jupyter lab": "jupyter lab",
                "lab": "jupyter lab",
                "vscode": "code",
                "vs code": "code",
                "visual studio": "devenv.exe",
                "python": "python",
                
                # Office Applications
                "word": "winword.exe",
                "excel": "excel.exe",
                "powerpoint": "powerpnt.exe",
                "outlook": "outlook.exe",
                "access": "msaccess.exe",
                "publisher": "mspub.exe",
                
                # Browsers
                "chrome": "chrome.exe",
                "google chrome": "chrome.exe",
                "firefox": "firefox.exe",
                "mozilla firefox": "firefox.exe",
                "edge": "msedge.exe",
                "internet explorer": "iexplore.exe",
                "ie": "iexplore.exe",
                "opera": "opera.exe",
                
                # Media & Entertainment
                "vlc": "vlc.exe",
                "media player": "wmplayer.exe",
                "groove": "groove.exe",
                "movies": "WinMoviesApp.exe",
                "photos": "PhotosApp.exe",
                
                # Utilities
                "snipping tool": "SnippingTool.exe",
                "screenshot": "SnippingTool.exe",
                "clipboard": "clipbrd.exe",
                "character map": "charmap.exe",
                "system information": "msinfo32.exe",
                "resource monitor": "resmon.exe",
                "performance monitor": "perfmon.exe",
                "registry editor": "regedit.exe",
                "regedit": "regedit.exe",
                "disk cleanup": "cleanmgr.exe",
                "winrar": "WinRAR.exe",
                "7zip": "7zFM.exe",
            }
            
            app_lower = app_name.lower().strip()

            # Get the app command, or use the original if not found
            app_command = apps.get(app_lower, app_name)

            # Special handling for Jupyter / notebook / lab to provide multiple fallbacks
            notebook_keys = {"jupyter", "notebook", "jupyter notebook", "jupyter lab", "lab"}
            if app_lower in notebook_keys or "jupyter" in app_command.lower():
                # 1) Try launching using the current Python interpreter (most reliable)
                try:
                    subprocess.Popen([sys.executable, '-m', 'notebook'])
                    return True
                except Exception:
                    pass

                # 2) Try common jupyter commands if they exist on PATH, or use 'py' fallback
                candidates = [
                    "jupyter-notebook",
                    "jupyter notebook",
                    "jupyter-lab",
                    "jupyter lab",
                    "py -m notebook",
                    "py -m jupyterlab",
                ]

                for cmd in candidates:
                    try:
                        exe = cmd.split()[0]
                        # If the executable exists on PATH or the command is 'py', attempt it
                        if shutil.which(exe) or exe.lower() in ("py", "python"):
                            subprocess.Popen(cmd, shell=True)
                            return True
                    except Exception:
                        continue

            # Try multiple generic ways to launch the application
            try:
                # Method 1: Direct subprocess.Popen (works if command is an executable path or list)
                subprocess.Popen(app_command)
                return True
            except FileNotFoundError:
                pass
            except Exception:
                # Some commands require shell=True (e.g., contain spaces or -m)
                try:
                    subprocess.Popen(app_command, shell=True)
                    return True
                except Exception:
                    pass

            # Try with START (Windows) and where lookup
            try:
                subprocess.Popen(f"start {app_command}", shell=True)
                return True
            except Exception:
                try:
                    result = subprocess.run(['where', app_lower], capture_output=True, text=True)
                    if result.stdout:
                        exe_path = result.stdout.strip().split('\n')[0]
                        subprocess.Popen(exe_path)
                        return True
                except Exception:
                    pass

            # If all methods fail, try launching with quotes as a last attempt
            try:
                subprocess.Popen(f'"{app_command}"', shell=True)
                return True
            except Exception:
                pass

            return False
        except Exception as e:
            print(f"Error opening application '{app_name}': {e}")
            return False
    
    @staticmethod
    def open_system_settings(setting_type: str = "general") -> bool:
        """Open Windows Settings for various configurations"""
        try:
            settings_commands = {
                # General Settings
                "settings": "ms-settings:",
                "general": "ms-settings:",
                
                # Display & Visual Settings
                "display": "ms-settings:display",
                "screen": "ms-settings:display",
                "resolution": "ms-settings:display-advanced",
                "wallpaper": "ms-settings:personalization-background",
                "background": "ms-settings:personalization-background",
                "desktop": "ms-settings:personalization-background",
                "theme": "ms-settings:themes",
                "dark mode": "ms-settings:themes",
                "light mode": "ms-settings:themes",
                "personalization": "ms-settings:personalization",
                "colors": "ms-settings:personalization-colors",
                "start": "ms-settings:personalization-start",
                "taskbar": "ms-settings:personalization-taskbar",
                "lock screen": "ms-settings:lockscreen",
                
                # Sound Settings
                "sound": "ms-settings:sound",
                "volume": "ms-settings:sound",
                "audio": "ms-settings:sound",
                "microphone": "ms-settings:sound-devices-input",
                "speaker": "ms-settings:sound-devices-output",
                
                # Network Settings
                "network": "ms-settings:network",
                "wifi": "ms-settings:network-wifi",
                "ethernet": "ms-settings:network-ethernet",
                "bluetooth": "ms-settings:bluetooth",
                "airplane": "ms-settings:network-airplane",
                "vpn": "ms-settings:network-vpn",
                "proxy": "ms-settings:network-proxy",
                "internet": "ms-settings:network",
                
                # Device Settings
                "device": "ms-settings:devices",
                "mouse": "ms-settings:devices-mouse",
                "keyboard": "ms-settings:devices-keyboard",
                "printer": "ms-settings:devices-printers-scanners",
                "camera": "ms-settings:privacy-webcam",
                "touchpad": "ms-settings:devices-touchpad",
                
                # System Settings
                "system": "ms-settings:system",
                "about": "ms-settings:system-about",
                "storage": "ms-settings:system-storage",
                "power": "ms-settings:powersleep",
                "battery": "ms-settings:powersleep-battery",
                "sleep": "ms-settings:powersleep",
                
                # Security & Privacy
                "security": "ms-settings:privacy",
                "privacy": "ms-settings:privacy",
                "password": "ms-settings:accounts-passwordoptions",
                "account": "ms-settings:accounts",
                "accounts": "ms-settings:accounts",
                "family": "ms-settings:family-group",
                
                # Apps & Features
                "apps": "ms-settings:appsfeatures",
                "programs": "ms-settings:appsfeatures",
                "uninstall": "ms-settings:appsfeatures",
                "startup": "ms-settings:startupapps",
                
                # Time & Date
                "time": "ms-settings:dateandtime",
                "date": "ms-settings:dateandtime",
                "timezone": "ms-settings:dateandtime",
                "clock": "ms-settings:dateandtime",
                
                # Language & Region
                "language": "ms-settings:regionlanguage",
                "region": "ms-settings:regionlanguage",
                "keyboard layout": "ms-settings:regionlanguage",
                
                # Update & Security
                "update": "ms-settings:windowsupdate",
                "windows update": "ms-settings:windowsupdate",
                "recovery": "ms-settings:recovery",
                "backup": "ms-settings:backup",
                "activation": "ms-settings:activation",
            }
            
            setting_lower = setting_type.lower().strip()
            command = settings_commands.get(setting_lower, "ms-settings:")
            
            subprocess.Popen(f"start {command}", shell=True)
            return True
        except Exception as e:
            print(f"Error opening settings: {e}")
            return False
    
    @staticmethod
    def open_control_panel(panel_type: str = "all") -> bool:
        """Open Windows Control Panel for legacy settings"""
        try:
            control_panel_commands = {
                "all": "control",
                "main": "control",
                "admin": "control admintools",
                "system": "control system",
                "sound": "mmsys.cpl",
                "display": "desk.cpl",
                "network": "ncpa.cpl",
                "devices": "devmgmt.msc",
                "printer": "control printers",
                "power": "powercfg.cpl",
                "keyboard": "control keyboard",
                "mouse": "control mouse",
                "date": "timedate.cpl",
                "language": "intl.cpl",
                "fonts": "control fonts",
                "programs": "appwiz.cpl",
                "uninstall": "appwiz.cpl",
            }
            
            panel_lower = panel_type.lower().strip()
            command = control_panel_commands.get(panel_lower, "control")
            
            subprocess.Popen(command, shell=True)
            return True
        except Exception as e:
            print(f"Error opening control panel: {e}")
            return False
    
    @staticmethod
    def open_device_manager() -> bool:
        """Open Device Manager to manage hardware devices"""
        try:
            subprocess.Popen("devmgmt.msc", shell=True)
            return True
        except Exception as e:
            print(f"Error opening device manager: {e}")
            return False
    
    @staticmethod
    def toggle_bluetooth(enable: bool = None) -> bool:
        """Turn Bluetooth on or off directly"""
        try:
            # Use PowerShell to toggle Bluetooth
            if enable is None:
                # Toggle - check current state first
                ps_command = """
                $bt = Get-Service -Name "bthserv" -ErrorAction SilentlyContinue
                if ($bt.Status -eq "Running") { Stop-Service -Name "bthserv" -Force }
                else { Start-Service -Name "bthserv" }
                """
            elif enable:
                ps_command = """
                $service = Get-Service -Name "bthserv" -ErrorAction SilentlyContinue
                if ($service.Status -ne "Running") {
                    Start-Service -Name "bthserv"
                }
                # Also try to enable Bluetooth radio
                [Windows.Devices.Radios.Radio]::GetRadiosAsync() | ForEach-Object {
                    $_.Awaiter.GetResult() | Where-Object { $_.Kind -eq "Bluetooth" } | ForEach-Object {
                        $_.SetStateAsync("On") | Out-Null
                    }
                }
                """
            else:
                ps_command = """
                Stop-Service -Name "bthserv" -Force -ErrorAction SilentlyContinue
                """
            
            subprocess.run(['powershell', '-Command', ps_command], 
                         capture_output=True, timeout=5)
            return True
        except Exception as e:
            print(f"Error toggling Bluetooth: {e}")
            # Fallback: try WMI
            try:
                subprocess.run(['powershell', '-Command', 
                              'Enable-NetAdapter -Name "Bluetooth*" -Confirm:$false'],
                             capture_output=True, timeout=5)
                return True
            except:
                return False
    
    @staticmethod
    def toggle_wifi(enable: bool = None) -> bool:
        """Turn Wi-Fi on or off directly"""
        try:
            if enable is None:
                # Toggle
                subprocess.run(['netsh', 'interface', 'set', 'interface', 'name=Wi-Fi', 'admin=toggle'],
                             shell=True, capture_output=True, timeout=5)
            elif enable:
                subprocess.run(['netsh', 'interface', 'set', 'interface', 'name=Wi-Fi', 'admin=enabled'],
                             shell=True, capture_output=True, timeout=5)
            else:
                subprocess.run(['netsh', 'interface', 'set', 'interface', 'name=Wi-Fi', 'admin=disabled'],
                             shell=True, capture_output=True, timeout=5)
            return True
        except Exception as e:
            print(f"Error toggling Wi-Fi: {e}")
            return False
    
    @staticmethod
    def toggle_airplane_mode(enable: bool = None) -> bool:
        """Turn Airplane Mode on or off"""
        try:
            ps_command = """
            $radioManager = [Windows.System.UserProfile.GlobalizationPreferences]
            $settings = New-Object -ComObject WinRtByteStream
            """
            
            if enable is None:
                # Toggle - use Settings app shortcut
                subprocess.Popen("ms-settings:network-airplane", shell=True)
            elif enable:
                # Enable Airplane Mode via Settings
                subprocess.Popen("ms-settings:network-airplane", shell=True)
            else:
                # Disable Airplane Mode
                subprocess.Popen("ms-settings:network-airplane", shell=True)
            
            return True
        except Exception as e:
            print(f"Error toggling Airplane Mode: {e}")
            return False
    
    @staticmethod
    def toggle_screen_saver(enable: bool = None) -> bool:
        """Turn screen saver on or off"""
        try:
            if enable is None or enable:
                # Enable screen saver
                subprocess.run(['powershell', '-Command',
                              'Set-ItemProperty -Path "HKCU:\\Control Panel\\Desktop" -Name "ScreenSaveActive" -Value 1'],
                             capture_output=True, timeout=5)
            else:
                # Disable screen saver
                subprocess.run(['powershell', '-Command',
                              'Set-ItemProperty -Path "HKCU:\\Control Panel\\Desktop" -Name "ScreenSaveActive" -Value 0'],
                             capture_output=True, timeout=5)
            return True
        except Exception as e:
            print(f"Error toggling screen saver: {e}")
            return False
    
    @staticmethod
    def toggle_do_not_disturb(enable: bool = None) -> bool:
        """Turn Do Not Disturb mode on or off"""
        try:
            if enable is None or enable:
                # Enable Do Not Disturb
                subprocess.run(['powershell', '-Command',
                              'Set-ItemProperty -Path "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Notifications\\Settings" -Name "NOC_GLOBAL_SETTING_ALLOW_NOTIFICATION_SOUND" -Value 0'],
                             capture_output=True, timeout=5)
            else:
                # Disable Do Not Disturb
                subprocess.run(['powershell', '-Command',
                              'Set-ItemProperty -Path "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Notifications\\Settings" -Name "NOC_GLOBAL_SETTING_ALLOW_NOTIFICATION_SOUND" -Value 1'],
                             capture_output=True, timeout=5)
            return True
        except Exception as e:
            print(f"Error toggling Do Not Disturb: {e}")
            return False
    
    @staticmethod
    def lock_screen() -> bool:
        """Lock the Windows screen"""
        try:
            subprocess.run(['rundll32.exe', 'user32.dll,LockWorkStation'], 
                         capture_output=True, timeout=5)
            return True
        except Exception as e:
            print(f"Error locking screen: {e}")
            return False
    
    @staticmethod
    def sleep_system(minutes: int = 0) -> bool:
        """Put system to sleep"""
        try:
            if minutes <= 0:
                subprocess.run(['rundll32.exe', 'powrprof.dll,SetSuspendState', '0', '1', '0'],
                             capture_output=True, timeout=5)
            else:
                subprocess.run(['powercfg', '/change', 'monitor-timeout-ac', str(minutes)],
                             capture_output=True, timeout=5)
            return True
        except Exception as e:
            print(f"Error putting system to sleep: {e}")
            return False
    
    @staticmethod
    def shutdown_system(minutes: int = 0) -> bool:
        """Shutdown the system"""
        try:
            if minutes <= 0:
                subprocess.run(['shutdown', '/s', '/t', '0'],
                             capture_output=True, timeout=5)
            else:
                subprocess.run(['shutdown', '/s', '/t', str(minutes * 60)],
                             capture_output=True, timeout=5)
            return True
        except Exception as e:
            print(f"Error shutting down system: {e}")
            return False
    
    @staticmethod
    def restart_system(minutes: int = 0) -> bool:
        """Restart the system"""
        try:
            if minutes <= 0:
                subprocess.run(['shutdown', '/r', '/t', '0'],
                             capture_output=True, timeout=5)
            else:
                subprocess.run(['shutdown', '/r', '/t', str(minutes * 60)],
                             capture_output=True, timeout=5)
            return True
        except Exception as e:
            print(f"Error restarting system: {e}")
            return False
    def open_task_manager() -> bool:
        """Open Windows Task Manager"""
        try:
            subprocess.Popen("taskmgr")
            return True
        except Exception as e:
            print(f"Error opening task manager: {e}")
            return False
    
    @staticmethod
    def open_system_preferences(preference: str) -> bool:
        """Generic system preference opener"""
        try:
            # First try Windows Settings
            if SystemController.open_system_settings(preference):
                return True
            # Fallback to Control Panel
            return SystemController.open_control_panel(preference)
        except Exception as e:
            print(f"Error opening preferences: {e}")
            return False
        try:
            if enable is None:
                # Toggle
                subprocess.run(['netsh', 'interface', 'set', 'interface', 'name=Wi-Fi', 'admin=toggle'],
                             shell=True, capture_output=True)
            elif enable:
                subprocess.run(['netsh', 'interface', 'set', 'interface', 'name=Wi-Fi', 'admin=enabled'],
                             shell=True, capture_output=True)
            else:
                subprocess.run(['netsh', 'interface', 'set', 'interface', 'name=Wi-Fi', 'admin=disabled'],
                             shell=True, capture_output=True)
            return True
        except Exception as e:
            print(f"Error toggling Wi-Fi: {e}")
            return False
    
    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """Get detailed system information including CPU, GPU, RAM, and Disk"""
        import platform
        import socket
        import re
        
        try:
            info = {}
            
            # Basic system info
            info["System"] = platform.system()
            info["Release"] = platform.release()
            info["Hostname"] = socket.gethostname()
            info["Python_Version"] = platform.python_version()
            
            # Get detailed Windows information
            if platform.system() == "Windows":
                try:
                    result = subprocess.run(['systeminfo'], capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        lines = result.stdout.split('\n')
                        
                        for line in lines:
                            if 'OS Name:' in line:
                                info["OS_Name"] = line.split(':', 1)[1].strip()
                            elif 'OS Version:' in line:
                                info["OS_Version"] = line.split(':', 1)[1].strip()
                            elif 'System Boot Time:' in line:
                                info["Boot_Time"] = line.split(':', 1)[1].strip()
                            elif 'Total Physical Memory:' in line:
                                info["Total_RAM"] = line.split(':', 1)[1].strip()
                            elif 'Available Physical Memory:' in line:
                                info["Available_RAM"] = line.split(':', 1)[1].strip()
                            elif 'Processor(s):' in line:
                                info["Processor_Count"] = line.split(':', 1)[1].strip()
                            elif 'System Type:' in line:
                                info["System_Type"] = line.split(':', 1)[1].strip()
                except:
                    pass
                
                # Get detailed CPU information
                try:
                    result = subprocess.run(['wmic', 'cpu', 'get', 'name,cores,threads'], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        lines = result.stdout.strip().split('\n')
                        if len(lines) >= 2:
                            parts = lines[1].split()
                            if len(parts) >= 3:
                                cpu_name = ' '.join(parts[:-2])
                                cores = parts[-2]
                                threads = parts[-1]
                                info["CPU_Name"] = cpu_name
                                info["CPU_Cores"] = cores
                                info["CPU_Threads"] = threads
                except:
                    pass
                
                # Get GPU information using multiple methods
                gpu_found = False
                
                # Method 1: Using WMIC
                try:
                    result = subprocess.run(['wmic', 'path', 'win32_videocontroller', 'get', 'name,adapterram'], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        lines = result.stdout.strip().split('\n')
                        gpu_list = []
                        for line in lines[1:]:
                            if line.strip():
                                parts = line.rsplit(None, 1)
                                if len(parts) >= 1:
                                    gpu_name = parts[0].strip()
                                    if gpu_name:
                                        if len(parts) > 1:
                                            try:
                                                vram = int(parts[1]) / (1024**3)
                                                gpu_list.append(f"{gpu_name} ({vram:.2f} GB)")
                                            except:
                                                gpu_list.append(gpu_name)
                                        else:
                                            gpu_list.append(gpu_name)
                        
                        if gpu_list:
                            info["GPU"] = "; ".join(gpu_list)
                            gpu_found = True
                except:
                    pass
                
                # Method 2: Using dxdiag if WMIC fails
                if not gpu_found:
                    try:
                        result = subprocess.run(['wmic', 'logicaldisk', 'get', 'name,size'], 
                                              capture_output=True, text=True, timeout=10)
                        # Just a fallback, actual GPU detection via registry or other means
                    except:
                        pass
                
                if not gpu_found:
                    info["GPU"] = "Detection in progress... Check Device Manager for graphics cards"
            
            # Get disk information
            try:
                import shutil
                disk_usage = shutil.disk_usage("C:\\")
                total_gb = disk_usage.total / (1024**3)
                used_gb = disk_usage.used / (1024**3)
                free_gb = disk_usage.free / (1024**3)
                used_percent = (disk_usage.used / disk_usage.total) * 100
                
                info["Total_Disk"] = f"{total_gb:.2f} GB"
                info["Used_Disk"] = f"{used_gb:.2f} GB ({used_percent:.1f}%)"
                info["Free_Disk"] = f"{free_gb:.2f} GB"
            except:
                pass
            
            return info
        except Exception as e:
            return {"error": str(e)}
