"""
Ollama-powered OS Assistant - Main Script
Intelligent System Control via Natural Language
"""

import sys
import os
from ollama_agent import OllamaAgent
from system_controller import SystemController

def cli_mode():
    """Command line interface mode"""
    print("=" * 60)
    print("🤖 Ollama OS Assistant - Intelligent System Control")
    print("=" * 60)
    print("\nAvailable Commands:")
    print("- Change background: 'change background to [color]'")
    print("- Set brightness: 'set brightness to [level]%'")
    print("- Control volume: 'mute/unmute/increase/decrease volume'")
    print("- Open application: 'open [app name]'")
    print("- Show system info: 'show system information'")
    print("\nType 'gui' to open graphical interface")
    print("Type 'exit' to quit")
    print("=" * 60)
    
    agent = OllamaAgent()
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() == 'exit':
                print("Goodbye!")
                break
            
            elif user_input.lower() == 'gui':
                print("Opening graphical interface...")
                from gui import OllamaAssistantGUI
                from PyQt6.QtWidgets import QApplication
                
                app = QApplication(sys.argv)
                window = OllamaAssistantGUI()
                window.show()
                sys.exit(app.exec())
            
            elif user_input.lower() == 'info':
                info = SystemController.get_system_info()
                print("\nSystem Information:")
                for key, value in info.items():
                    print(f"  {key}: {value}")
            
            else:
                # Parse and execute command
                command = agent.parse_command(user_input)
                confidence = command.get("confidence", 0)
                
                print(f"\n[Confidence: {confidence}%]")
                
                if confidence > 50:
                    print(f"Assistant: {command.get('explanation', 'Executing...')}")
                else:
                    response = agent.chat(user_input)
                    print(f"Assistant: {response}")
        
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == '__main__':
    # Check if GUI requested
    if len(sys.argv) > 1 and sys.argv[1] == 'gui':
        from gui import OllamaAssistantGUI
        from PyQt6.QtWidgets import QApplication
        
        app = QApplication(sys.argv)
        window = OllamaAssistantGUI()
        window.show()
        sys.exit(app.exec())
else:
    cli_mode()
