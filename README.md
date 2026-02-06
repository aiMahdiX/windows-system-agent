# Windows System Agent

> An intelligent AI-powered system control assistant for Windows using natural language commands powered by Ollama


![Uploading Screenshot 2026-02-06 151516.png…]()

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows-green.svg)

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Configuration](#configuration)
- [Architecture](#architecture)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)
- [Author](#author)

## 🎯 Overview

**Windows System Agent** is a cutting-edge AI assistant that bridges the gap between natural language and system operations. Powered by Ollama's local AI models, it enables intuitive control over your Windows system through simple, conversational commands. Whether you're managing your desktop, adjusting settings, or launching applications, Windows System Agent understands your intent and executes commands seamlessly.

### Key Highlights

- **100% Local Processing**: All AI operations run locally on your machine - no cloud dependencies
- **Natural Language Understanding**: Give commands in plain English
- **Instant Execution**: Get instant system responses to your commands
- **Dual Interface**: Choose between GUI and CLI based on your preference
- **Highly Extensible**: Easy to add new system controls and features
- **Privacy-First**: Your data never leaves your machine

## ✨ Features

### Core Capabilities

- **🎨 Desktop Background Control**
  - Change background color instantly
  - Support for multiple color options
  - Easy customization

- **☀️ Brightness Management**
  - Adjust screen brightness
  - Preset brightness levels (25%, 50%, 75%, 100%)
  - Real-time brightness control

- **🔊 Volume Control**
  - Mute and unmute system audio
  - Increase or decrease volume
  - Precise volume adjustments

- **🚀 Application Launcher**
  - Open applications with voice or text commands
  - Support for built-in and custom applications
  - Quick application access

- **📊 System Information**
  - Display comprehensive system specs
  - CPU, RAM, disk usage information
  - Real-time system monitoring

### Interface Options

- **GUI (Graphical User Interface)**
  - Modern PyQt6-based interface
  - User-friendly design
  - Command history
  - Real-time response display

- **CLI (Command-Line Interface)**
  - Terminal-based interaction
  - Advanced users' preference
  - Lightweight and fast
  - Scripting support

### Advanced Features

- **Command Scheduling**: Schedule commands to execute after a delay
- **Multi-Model Support**: Choose between different Ollama models
- **Conversation History**: Maintain context across multiple commands
- **Auto-Confirm Mode**: Optional automatic command execution
- **Extensible Architecture**: Add custom system controls easily

## 📦 Requirements

| Component | Version | Purpose |
|-----------|---------|---------|
| **Ollama** | Latest | AI model runtime |
| **Python** | 3.8+ | Core runtime environment |
| **Windows** | 10/11 | Operating system |
| **PyQt6** | Latest | GUI framework (included in requirements.txt) |

### System Requirements

- **RAM**: Minimum 4GB (8GB+ recommended)
- **Disk Space**: 2GB free for Ollama models
- **GPU**: Optional (NVIDIA with CUDA support for better performance)

## 🚀 Installation

### Step 1: Install Ollama

1. Visit [https://ollama.ai](https://ollama.ai)
2. Download the Windows installer
3. Run the installer and follow the setup wizard
4. Verify installation by opening Command Prompt and running:
   ```bash
   ollama --version
   ```

### Step 2: Clone or Download the Repository

```bash
# Using git
git clone https://github.com/aiMahdiX/windows-system-agent.git
cd windows-system-agent

# Or download the ZIP file and extract it
```

### Step 3: Install Python Dependencies

```bash
# Create a virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### Step 4: Download Ollama Models

Open a new Command Prompt or PowerShell and run:

```bash
# Download a model (choose one or multiple)
ollama pull mistral          # Recommended - fast and efficient
ollama pull llama2           # Alternative - larger model
ollama pull neural-chat      # Alternative - optimized for chat
```

### Step 5: Start Ollama Service

```bash
# In a dedicated terminal window, keep this running
ollama serve
```

This starts the Ollama server on `http://localhost:11434`. Keep this window open while using Windows System Agent.

## 🎮 Quick Start

### Launch GUI Application

```bash
# Method 1: Direct GUI launch
python gui.py

# Method 2: GUI from main.py
python main.py gui
```

### Launch CLI Application

```bash
# From main.py
python main.py

# You will see the interactive CLI interface
```

## 📖 Usage

### GUI Usage

1. Launch the application: `python gui.py`
2. Type your command in the text input field
3. Press Enter or click "Send"
4. The assistant responds with executed results or explanations
5. View command history in the message area

### CLI Usage

```bash
python main.py
```

Example commands:

```
You: change background to blue
Assistant: [Confidence: 95%] Background changed to blue color

You: set brightness to 50%
Assistant: [Confidence: 92%] Brightness set to 50%

You: mute volume
Assistant: [Confidence: 98%] Volume muted

You: open notepad
Assistant: [Confidence: 96%] Launching Notepad...

You: show system information
Assistant: [Displays detailed system information]

You: exit
Goodbye!
```

### Example Commands

#### Background Control
```
change background to red
set background to green
background blue
```

#### Brightness Control
```
set brightness to 75%
increase brightness to maximum
dim the screen to 30%
set brightness 50
```

#### Volume Control
```
mute volume
unmute audio
increase volume
decrease sound
set volume to 60%
```

#### Application Launching
```
open notepad
launch calculator
open file explorer
start excel
```

#### System Information
```
show system information
display system specs
what's my cpu?
check disk space
```

#### Scheduled Commands
```
change background to blue after 5 seconds
open notepad in 2 minutes
mute volume after 30 seconds
```

## ⚙️ Configuration

### config.json

The application configuration is managed through `config.json`:

```json
{
  "ollama": {
    "model": "mistral",
    "base_url": "http://localhost:11434",
    "temperature": 0.7,
    "timeout": 60
  },
  "system": {
    "language": "en",
    "auto_confirm": false,
    "max_history": 50
  },
  "features": {
    "background_change": true,
    "brightness_control": true,
    "volume_control": true,
    "app_launcher": true
  }
}
```

### Configuration Options

| Setting | Type | Description |
|---------|------|-------------|
| `ollama.model` | string | Ollama model name (mistral, llama2, neural-chat) |
| `ollama.base_url` | string | Ollama server URL |
| `ollama.temperature` | float | Model creativity (0.0-1.0) |
| `system.language` | string | Interface language (en, fa) |
| `system.auto_confirm` | boolean | Auto-execute commands without confirmation |

### Changing the Ollama Model

Edit `config.json` or programmatically:

```python
from ollama_agent import OllamaAgent

# Use a specific model
agent = OllamaAgent(model_name="llama2")
```

## 🏗️ Architecture

### Project Structure

```
windows-system-agent/
├── main.py                  # Main entry point
├── gui.py                   # PyQt6 GUI interface
├── ollama_agent.py          # Ollama integration & NLU
├── system_controller.py     # System control operations
├── tool_caller.py           # Function calling mechanism
├── streaming_handler.py     # Response streaming
├── state_manager.py         # State management
├── schema_validator.py      # Schema validation
├── function_executor.py     # Command execution
├── config.json              # Configuration file
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

### Component Overview

#### OllamaAgent
- Communicates with Ollama AI model
- Parses natural language commands
- Manages conversation history
- Maintains system state

#### SystemController
- Executes system operations
- Manages background changes
- Controls brightness and volume
- Launches applications
- Retrieves system information

#### GUI (OllamaAssistantGUI)
- PyQt6-based user interface
- Thread-safe command execution
- Real-time response display
- Command history management

#### Supporting Modules
- **StreamingHandler**: Manages streaming responses
- **StateManager**: Maintains application state
- **SchemaValidator**: Validates command schemas
- **FunctionExecutor**: Executes system functions

## 🔧 Troubleshooting

### Cannot Connect to Ollama

**Problem**: "Cannot establish connection to Ollama"

**Solutions**:
1. Verify Ollama is running:
   ```bash
   ollama serve
   ```
2. Check if port 11434 is accessible
3. Ensure no firewall is blocking the connection
4. Verify Ollama installation: `ollama --version`

### PyQt6 Installation Issues

**Problem**: "ModuleNotFoundError: No module named 'PyQt6'"

**Solutions**:
1. Upgrade pip: `python -m pip install --upgrade pip`
2. Reinstall PyQt6: `pip install --force-reinstall PyQt6`
3. Use a fresh virtual environment

### Model Download Issues

**Problem**: "Cannot download Ollama model"

**Solutions**:
1. Check internet connection
2. Verify sufficient disk space (models are 4-7GB)
3. Try a smaller model: `ollama pull orca-mini`
4. Check Ollama logs for detailed errors

### Background Change Not Working

**Problem**: "Background fails to change"

**Solutions**:
1. Run application with administrator privileges
2. Ensure image files are in BMP or PNG format
3. Check Windows image settings aren't locked
4. Verify desktop is not using group policy restrictions

### GUI Window Doesn't Appear

**Problem**: "GUI launches but no window visible"

**Solutions**:
1. Check multiple monitors for window placement
2. Run in compatibility mode for older Windows versions
3. Update display drivers
4. Try windowed mode explicitly

### Brightness Control Not Working

**Problem**: "Brightness control fails"

**Solutions**:
1. Verify graphics drivers are updated
2. Check if brightness is controlled by keyboard shortcuts
3. Try running as administrator
4. Check monitor brightness settings (some external monitors have physical locks)

### Volume Control Issues

**Problem**: "Volume changes not registered"

**Solutions**:
1. Check if volume is muted at system level
2. Verify audio device is properly installed
3. Update audio drivers
4. Check for application-level volume locks

## 📝 API Reference

### OllamaAgent

```python
from ollama_agent import OllamaAgent

# Initialize agent
agent = OllamaAgent(model_name="mistral")

# Parse and execute command
result = agent.execute_function("change background to blue")

# Chat mode
response = agent.chat("What's the weather like?")

# Get available models
models = agent.get_available_models()

# Set model
agent.set_model("llama2")
```

### SystemController

```python
from system_controller import SystemController

# System info
info = SystemController.get_system_info()

# Background control
SystemController.change_background_color("blue")

# Brightness control
SystemController.set_brightness(50)

# Volume control
SystemController.set_volume(75)
SystemController.mute()
SystemController.unmute()

# Application launcher
SystemController.open_application("notepad")

# Scheduled execution
SystemController.schedule_action(5, some_function, args)
```

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Report Issues**: Open an issue with detailed information
2. **Feature Requests**: Suggest new features or improvements
3. **Submit PRs**: Follow the contribution guidelines
4. **Documentation**: Improve or translate documentation

### Contribution Guidelines

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Code Standards

- Follow PEP 8 Python style guide
- Add docstrings to all functions
- Include unit tests for new features
- Update documentation

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

```
MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction...
```

## 👨‍💻 Author

**aiMahdiX**

- 📧 Email: [aimahdix120@outlook.com](mailto:aimahdix120@outlook.com)
- 🐙 GitHub: [@aiMahdiX](https://github.com/aiMahdiX)
- 💼 LinkedIn: [Connect](https://linkedin.com)

### Project Information

- **Project Name**: Windows System Agent
- **Version**: 1.0.0
- **Release Date**: February 2026
- **Status**: Active Development

---

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai) - For providing the excellent local AI model runtime
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/intro) - For the GUI framework
- [Python Community](https://www.python.org) - For the amazing language and ecosystem

---

## 📞 Support

### Getting Help

1. **Documentation**: Check this README and code comments
2. **Issues**: Open an issue on GitHub with details
3. **Email**: Contact aimahdix120@outlook.com
4. **Community**: Join discussions for community support

### Reporting Issues

When reporting issues, please include:

- Windows version
- Python version
- Ollama model being used
- Complete error message
- Steps to reproduce

---

<div align="center">

Made with ❤️ for Windows users

[⭐ Star us on GitHub](https://github.com/aiMahdiX/windows-system-agent)

</div>
