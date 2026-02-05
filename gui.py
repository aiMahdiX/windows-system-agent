import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLineEdit, QPushButton, QTextEdit, QLabel,
                             QComboBox, QSlider, QSpinBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from ollama_agent import OllamaAgent
from system_controller import SystemController
from function_executor import FunctionExecutor
import json

class OllamaWorker(QThread):
    """Worker thread for Ollama requests"""
    response_signal = pyqtSignal(str)
    
    def __init__(self, agent, user_input):
        super().__init__()
        self.agent = agent
        self.user_input = user_input
    
    def run(self):
        try:
            # Use Ollama's function executor to understand and execute the command
            result = self.agent.execute_function(self.user_input)
            
            # Check if this is a scheduled command
            if result.get("scheduled"):
                # Handle scheduled execution
                self.response_signal.emit(result.get("message", "Command scheduled"))
                
                # Schedule the actual function execution
                original_result = result.get("original_result", {})
                if "function" in original_result:
                    function_call = original_result["function"]
                    delay = result.get("delay", 0)
                    
                    # Execute the function through FunctionExecutor.execute_function
                    # But we need to pass it through schedule_action
                    SystemController.schedule_action(
                        delay,
                        FunctionExecutor.execute_function,
                        original_result
                    )
                return
            
            # Check if this is a chat response (not a function call)
            if result.get("is_chat"):
                self.response_signal.emit(result.get("message", "I'm here to help!"))
                return
            
            # Check if function was executed successfully
            if result.get("status") == "success":
                # Format the response message
                if "data" in result:
                    # System info response
                    info_text = self._format_system_info(result["data"])
                    self.response_signal.emit(f"📊 System Information:\n\n{info_text}")
                else:
                    # Regular function execution response
                    message = result.get("message", "Command executed")
                    self.response_signal.emit(f"✓ {message}")
            
            elif result.get("status") == "error":
                # Error occurred - try fallback to chat
                response = self.agent.chat(self.user_input)
                self.response_signal.emit(response)
            
            else:
                # Fallback to general chat
                response = self.agent.chat(self.user_input)
                self.response_signal.emit(response)
            
        except Exception as e:
            self.response_signal.emit(f"Error: {str(e)}")
    
    def _format_system_info(self, info: dict) -> str:
        """Format system information for display"""
        output = ""
        
        # Organize information by category
        sections = {
            "Operating System": ["System", "OS_Name", "OS_Version", "Release", "System_Type"],
            "Processor & GPU": ["Processor_Count", "Processor", "GPU"],
            "Memory": ["Total_RAM", "Available_RAM"],
            "Storage": ["Total_Disk", "Used_Disk", "Free_Disk"],
            "Other": ["Hostname", "Boot_Time", "Python_Version"]
        }
        
        for section, keys in sections.items():
            section_data = {k: info.get(k) for k in keys if k in info and info.get(k)}
            if section_data:
                output += f"\n{section}:\n"
                output += "-" * 50 + "\n"
                for key, value in section_data.items():
                    # Format key name
                    display_key = key.replace("_", " ")
                    output += f"  {display_key}: {value}\n"
        
        return output

class OllamaAssistantGUI(QMainWindow):
    """GUI for Ollama OS Assistant"""
    
    def __init__(self):
        super().__init__()
        self.agent = OllamaAgent()
        self.system = SystemController()
        self.init_ui()
        self.setWindowTitle("Ollama OS Assistant - Intelligent System Control")
        self.setGeometry(100, 100, 900, 700)
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; }
            QLabel { color: #ffffff; }
            QLineEdit { 
                padding: 8px; 
                border: 2px solid #0d7377; 
                border-radius: 5px;
                font-size: 12px;
                background-color: #2d2d2d;
                color: #ffffff;
            }
            QPushButton { 
                padding: 8px 16px; 
                background-color: #0d7377; 
                color: #ffffff;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #14919b; }
            QPushButton:pressed { background-color: #0a5a62; }
            QTextEdit { 
                background-color: #2d2d2d; 
                border: 1px solid #0d7377;
                border-radius: 5px;
                padding: 8px;
                color: #ffffff;
            }
            QComboBox {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 2px solid #0d7377;
                border-radius: 5px;
                padding: 5px;
            }
        """)
    
    def init_ui(self):
        """Initialize user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        
        title = QLabel("🤖 Ollama OS Assistant")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        main_layout.addWidget(title)
        
        # Model selector
        model_layout = QHBoxLayout()
        model_label = QLabel("📦 Model:")
        self.model_dropdown = QComboBox()
        self.model_dropdown.currentTextChanged.connect(self.on_model_changed)
        
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_dropdown)
        model_layout.addStretch()
        main_layout.addLayout(model_layout)
        
        # Chat display
        chat_layout = QVBoxLayout()
        chat_label = QLabel("Messages:")
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setMinimumHeight(300)
        chat_layout.addWidget(chat_label)
        chat_layout.addWidget(self.chat_display)
        main_layout.addLayout(chat_layout)
        
        # Input area
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Enter your command... (example: change background to blue)")
        self.input_field.returnPressed.connect(self.send_command)
        
        send_button = QPushButton("Send ✉️")
        send_button.clicked.connect(self.send_command)
        
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(send_button)
        main_layout.addLayout(input_layout)
        
        # Quick actions
        actions_label = QLabel("Quick Actions:")
        main_layout.addWidget(actions_label)
        
        actions_layout = QHBoxLayout()
        
        bg_button = QPushButton("🎨 Change Background")
        bg_button.clicked.connect(self.quick_background)
        
        bright_button = QPushButton("💡 Adjust Brightness")
        bright_button.clicked.connect(self.quick_brightness)
        
        app_button = QPushButton("📂 Open Application")
        app_button.clicked.connect(self.quick_app)
        
        info_button = QPushButton("ℹ️ System Information")
        info_button.clicked.connect(self.show_system_info)
        
        clear_button = QPushButton("🗑️ Clear")
        clear_button.clicked.connect(self.clear_chat)
        
        actions_layout.addWidget(bg_button)
        actions_layout.addWidget(bright_button)
        actions_layout.addWidget(app_button)
        actions_layout.addWidget(info_button)
        actions_layout.addWidget(clear_button)
        main_layout.addLayout(actions_layout)
        
        central_widget.setLayout(main_layout)
        
        # Load available models AFTER UI is fully initialized
        self.load_available_models()
    
    def load_available_models(self):
        """Load available models from Ollama into dropdown"""
        models = self.agent.get_available_models()
        
        if models:
            self.model_dropdown.blockSignals(True)  # Prevent triggering on_model_changed during load
            self.model_dropdown.clear()
            self.model_dropdown.addItems(models)
            
            # Set current model if it exists in the list
            index = self.model_dropdown.findText(self.agent.model_name)
            if index >= 0:
                self.model_dropdown.setCurrentIndex(index)
            
            self.model_dropdown.blockSignals(False)
            self.append_message("System", f"✓ Loaded {len(models)} model(s). Current: {self.agent.model_name}")
        else:
            self.model_dropdown.addItem("No models available")
            self.append_message("System", "⚠️ No models found. Please install a model in Ollama first.\nRun: ollama pull mistral")
    
    def on_model_changed(self, model_name: str):
        """Handle model selection change"""
        if model_name and model_name != "No models available":
            if self.agent.set_model(model_name):
                self.append_message("System", f"🔄 Switched to model: {model_name}")
            else:
                self.append_message("System", f"❌ Failed to switch to model: {model_name}")
    
    def send_command(self):
        """Send command to agent"""
        user_input = self.input_field.text().strip()
        
        if not user_input:
            return
        
        # Display user message
        self.append_message("You", user_input)
        self.input_field.clear()
        
        # Send to worker thread
        self.worker = OllamaWorker(self.agent, user_input)
        self.worker.response_signal.connect(self.on_response)
        self.worker.start()
    
    def on_response(self, response):
        """Handle response from agent"""
        self.append_message("Assistant", response)
    
    def append_message(self, sender, message):
        """Append message to chat display"""
        self.chat_display.append(f"<b>{sender}:</b> {message}\n")
    
    def quick_background(self):
        """Quick background color selector"""
        self.input_field.setText("change background to blue")
        self.send_command()
    
    def quick_brightness(self):
        """Quick brightness selector"""
        self.input_field.setText("set brightness to 70%")
        self.send_command()
    
    def quick_app(self):
        """Quick app opener"""
        self.input_field.setText("open notepad")
        self.send_command()
    
    def show_system_info(self):
        """Show system information"""
        info = SystemController.get_system_info()
        info_text = "\n".join([f"{k}: {v}" for k, v in info.items()])
        self.append_message("System", f"System Information:\n{info_text}")
    
    def clear_chat(self):
        """Clear chat display"""
        self.chat_display.clear()
        self.agent.conversation_history = []

def main():
    app = QApplication(sys.argv)
    window = OllamaAssistantGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
