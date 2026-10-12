# PhoneHub Voice Gateway

A PyQt6-based desktop application for managing telephony operations via serial-connected modems. Provides manual, voicemail, and AI-ready call handling with local audio storage and playback management.

## 📖 Overview
PhoneHub bridges traditional telephony hardware with modern desktop workflows. It polls a serial modem for call events (`RING`, `NO CARRIER`, `BUSY`), routes them through configurable modes, and manages local `.wav` voicemail files. The application is designed as a lightweight, standalone solution without external server dependencies.

## ✨ Features
- **Serial Modem Control:** Direct AT command execution (`ATD`, `ATA`, `ATH`) for dialing, answering, and hanging up.
- **Call Handling Modes:**
  - `Manual`: Operator-controlled answer/hangup.
  - `Voicemail`: Auto-answers after 3 rings, simulates recording, and saves to local directory.
  - `AI`: UI prepared for future AI voice processing integration.
- **Voicemail Management:** Dynamic list of received `.wav` files with play/delete functionality.
- **Thread-Safe Architecture:** Background `QThread` handles serial polling to prevent GUI freezing.
- **Real-Time Status & Alerts:** Live call indicators, ring counters, and mode switching.

## 🏗️ Architecture & Structure
The project is currently implemented as a single-file application (`app.py`) with modular internal classes:
- `PhoneHubApp` (`QMainWindow`): Main GUI, layouts, styling, and event routing.
- `ModemWorker` (`QThread`): Serial connection management, AT command execution, and signal emission.
- `AudioManager`: Placeholder class for audio playback/recording (currently prints to console).
- **Signal/Slot Flow:** `ModemWorker` emits signals (`incoming_call`, `call_answered`, `new_voicemail`, etc.) which `PhoneHubApp` connects to for UI updates.

## ⚙️ Prerequisites
- Python 3.8+
- `PyQt6`
- `pyserial`
- A serial-connected modem (USB-to-Serial or built-in COM port)

## 📦 Installation
```bash
pip install PyQt6 pyserial
```

## ⚙️ Configuration
Open `app.py` and modify the base settings at the top:
```python
SERIAL_PORT = "COM3"      # Change to your modem's port (e.g., /dev/ttyUSB0 on Linux)
BAUD_RATE = 9600          # Standard modem baud rate
VOICEMAIL_DIR = "voicemails" # Local directory for .wav storage
```

## 🚀 Usage
1. Run the application: `python app.py`
2. The interface will initialize and attempt to connect to the configured serial port.
3. Select an operation mode: `Manual`, `Voicemail`, or `AI`.
4. Use the keypad to dial numbers, or handle incoming calls via the alert banner.
5. Manage received voicemails from the bottom panel (Play/Delete).

## 📁 File Structure
```
project/
├── app.py          # Main application, GUI, and modem logic
└── voicemails/     # Auto-created directory for .wav files
```

## 🔍 Technical Notes
- **Threading:** Serial polling runs in a dedicated `QThread` with a 0.1s sleep interval to avoid blocking the main event loop.
- **AT Commands:** Uses standard Hayes commands. Caller ID parsing is currently hardcoded to `"Unknown"` pending modem-specific AT command implementation (e.g., `+CLIP`).
- **Audio Handling:** The `AudioManager` class is a placeholder. Real `.wav` playback and recording require integration with libraries like `PyAudio` or `sounddevice`.
- **AI Mode:** The UI and mode switch are implemented, but AI voice processing logic is not yet active.

## 🛠️ Development & Extension
- Implement real audio capture/playback in `AudioManager`.
- Add Caller ID parsing (`AT+CLIP?` or modem-specific equivalents).
- Integrate AI voice processing pipeline (e.g., speech-to-text, voice synthesis).
- Add comprehensive error handling and connection retry logic.
- Refactor into a multi-file package for better maintainability.

## 📄 License
License information is not provided in the source files. Please contact the project maintainer (Novin Rahkar) for licensing details.

---
*Built with PyQt6 & Python. Designed for reliable, standalone telephony management.*
