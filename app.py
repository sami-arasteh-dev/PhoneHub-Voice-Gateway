import sys
import os
import time
import serial
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QFrame, QLabel, QPushButton, QLineEdit, 
                             QMessageBox, QGroupBox, QListWidget, QListWidgetItem)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal

# ==================== تنظیمات پایه ====================
# پورت مودم خود را در اینجا وارد کنید (مثلاً "COM3" در ویندوز یا "/dev/ttyUSB0" در لینوکس)
SERIAL_PORT = "COM3"  
BAUD_RATE = 9600
VOICEMAIL_DIR = "voicemails"

# اطمینان از وجود پوشه ذخیره پیام‌های صوتی
if not os.path.exists(VOICEMAIL_DIR):
    os.makedirs(VOICEMAIL_DIR)

# ==================== مدیریت صدا ====================
class AudioManager:
    """کلاس مدیریت پخش و ضبط صدای مودم (نیازمند تکمیل بر اساس پکیج‌های صوتی شما مانند PyAudio)"""
    def play_wav_file(self, path):
        # در اینجا می‌توانید کدهای پخش صدای خود را قرار دهید
        print(f"Playing audio file: {path}")

# ==================== پردازشگر مودم ====================
class ModemWorker(QThread):
    """مدیریت ارتباطات سریال مودم در پس‌زمینه برای جلوگیری از هنگ کردن برنامه"""
    incoming_call = pyqtSignal(str, int)       # شماره تماس گیرنده، تعداد زنگ
    call_answered = pyqtSignal(str)            # پیام پاسخگویی
    call_ended = pyqtSignal(str)               # پیام قطع تماس
    status_update = pyqtSignal(str)            # پیام وضعیت کلی
    voicemail_started = pyqtSignal(str)        # شروع ضبط پیام
    new_voicemail = pyqtSignal()               # اعلان دریافت پیام جدید

    def __init__(self, port, baud_rate):
        super().__init__()
        self.port = port
        self.baud_rate = baud_rate
        self.answer_mode = 'manual' # 'manual', 'voicemail', 'ai'
        self.is_running = True
        self.serial_conn = None
        self.audio_manager = AudioManager()
        
        try:
            self.serial_conn = serial.Serial(self.port, self.baud_rate, timeout=1)
            self.status_update.emit("مودم با موفقیت متصل شد.")
        except Exception as e:
            print(f"Modem connection error: {e}")

    def run(self):
        ring_count = 0
        while self.is_running:
            if self.serial_conn and self.serial_conn.is_open:
                try:
                    line = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        if "RING" in line:
                            ring_count += 1
                            self.incoming_call.emit("ناشناس", ring_count) # در صورت داشتن CallerID آن را جایگزین کنید
                            
                            # اگر روی حالت پیغام‌گیر است و 3 بار زنگ خورد:
                            if self.answer_mode == 'voicemail' and ring_count >= 3:
                                self.answer_call(is_ai=False)
                                self.voicemail_started.emit("ناشناس")
                                time.sleep(2) # شبیه‌سازی ضبط پیام
                                # در اینجا می‌توانید کدهای ذخیره فایل صوتی را اضافه کنید
                                self.new_voicemail.emit()
                                self.hangup()
                                ring_count = 0
                                
                        elif "NO CARRIER" in line or "BUSY" in line:
                            self.call_ended.emit("تماس پایان یافت / مشغول.")
                            ring_count = 0
                except Exception as e:
                    pass
            time.sleep(0.1)

    def make_call(self, number):
        self.status_update.emit(f"در حال تماس با {number}...")
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.write(f"ATD{number};\r".encode())

    def answer_call(self, is_ai=False):
        msg = "تماس توسط هوش مصنوعی پاسخ داده شد." if is_ai else "تماس پاسخ داده شد."
        self.call_answered.emit(msg)
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.write(b"ATA\r")

    def hangup(self):
        self.call_ended.emit("تماس قطع شد.")
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.write(b"ATH\r")

    def stop(self):
        self.is_running = False
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()

# ==================== رابط کاربری (GUI) ====================
class PhoneHubApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("هاب تلفنی صوتی | نوین راهکار")
        self.setFixedSize(420, 780)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        # استایل‌های سراسری برنامه
        self.setStyleSheet("""
            QMainWindow { background-color: #f8f9fa; }
            QWidget { font-family: 'Tahoma', 'Segoe UI', sans-serif; font-size: 14px; }
            
            QFrame#AppContainer {
                background-color: #ffffff;
                border-radius: 18px;
            }
            QLabel#HeaderTitle {
                background-color: #2c3e50;
                color: white;
                font-size: 18px;
                font-weight: bold;
                padding: 18px;
                border-top-left-radius: 18px;
                border-top-right-radius: 18px;
            }
            QPushButton.ModeBtn {
                background: transparent;
                border: none;
                border-bottom: 3px solid transparent;
                color: #7f8c8d;
                padding: 12px;
                font-weight: normal;
                border-radius: 0px;
            }
            QPushButton.ModeBtn:checked {
                color: #2c3e50;
                font-weight: bold;
                background: white;
                border-bottom: 3px solid #3498db;
            }
            QLineEdit#DialScreen {
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                color: #2c3e50;
                background: white;
                font-size: 24px;
                font-family: monospace;
                letter-spacing: 2px;
            }
            QLineEdit#DialScreen:focus { border: 2px solid #3498db; }
            
            QPushButton.KeypadBtn {
                background: #f1f3f5;
                border: 1px solid #e0e0e0;
                border-radius: 12px;
                font-size: 22px;
                font-family: monospace;
                color: #2c3e50;
            }
            QPushButton.KeypadBtn:pressed { background: #e9ecef; }
            
            QPushButton.ActionBtn {
                color: white;
                border-radius: 10px;
                font-weight: bold;
                font-size: 15px;
            }
        """)

        # مقداردهی ارتباطات مودم
        self.modem_worker = ModemWorker(SERIAL_PORT, BAUD_RATE)
        self.setup_signals()
        self.modem_worker.start()

        self.init_ui()
        self.load_voicemails()

    def setup_signals(self):
        self.modem_worker.incoming_call.connect(self.on_incoming_call)
        self.modem_worker.call_answered.connect(self.on_call_answered)
        self.modem_worker.call_ended.connect(self.on_call_ended)
        self.modem_worker.status_update.connect(self.update_status)
        self.modem_worker.voicemail_started.connect(self.on_voicemail_started)
        self.modem_worker.new_voicemail.connect(self.load_voicemails)

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)

        self.app_container = QFrame()
        self.app_container.setObjectName("AppContainer")
        container_layout = QVBoxLayout(self.app_container)
        container_layout.setContentsMargins(0, 0, 0, 15)
        container_layout.setSpacing(0)

        # --- هدر ---
        header_label = QLabel("هاب تلفنی نوین راهکار")
        header_label.setObjectName("HeaderTitle")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(header_label)

        # --- آلارم تماس ---
        self.alert_frame = QFrame()
        self.alert_frame.setStyleSheet("background-color: #e67e22; color: white;")
        self.alert_frame.setVisible(False)
        alert_layout = QVBoxLayout(self.alert_frame)
        self.alert_label = QLabel("📞 تماس ورودی...")
        self.alert_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.alert_label.setStyleSheet("font-weight: bold; font-size: 15px;")
        alert_layout.addWidget(self.alert_label)
        container_layout.addWidget(self.alert_frame)
        
        self.alert_timer = QTimer(self)
        self.alert_timer.timeout.connect(self.toggle_alert_color)
        self.alert_toggle = False

        # --- باکس هوش مصنوعی ---
        self.ai_frame = QFrame()
        self.ai_frame.setStyleSheet("background-color: #8e44ad; color: white;")
        self.ai_frame.setVisible(False)
        ai_layout = QVBoxLayout(self.ai_frame)
        self.ai_label = QLabel("🤖 حالت هوش مصنوعی فعال است\nصدای تماس‌گیرنده پخش می‌شود")
        self.ai_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ai_layout.addWidget(self.ai_label)
        container_layout.addWidget(self.ai_frame)

        # --- انتخابگر حالت ---
        mode_frame = QFrame()
        mode_frame.setStyleSheet("background: #ecf0f1; border-bottom: 1px solid #e0e0e0;")
        mode_layout = QHBoxLayout(mode_frame)
        mode_layout.setContentsMargins(0, 0, 0, 0)
        mode_layout.setSpacing(0)

        self.btn_mode_manual = QPushButton("اپراتور")
        self.btn_mode_vm = QPushButton("پیغام‌گیر")
        self.btn_mode_ai = QPushButton("هوش مصنوعی")
        
        for btn, mode in [(self.btn_mode_manual, 'manual'), (self.btn_mode_vm, 'voicemail'), (self.btn_mode_ai, 'ai')]:
            btn.setCheckable(True)
            btn.setProperty("class", "ModeBtn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, m=mode: self.change_mode(m))
            mode_layout.addWidget(btn)
            
        self.btn_mode_manual.setChecked(True)
        container_layout.addWidget(mode_frame)

        # --- کانتینر محتوای داخلی ---
        inner_content = QWidget()
        inner_layout = QVBoxLayout(inner_content)
        inner_layout.setContentsMargins(20, 20, 20, 10)
        inner_layout.setSpacing(15)

        # نمایشگر شماره
        self.dial_input = QLineEdit()
        self.dial_input.setObjectName("DialScreen")
        self.dial_input.setReadOnly(True)
        self.dial_input.setFixedHeight(55)
        self.dial_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.dial_input.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        inner_layout.addWidget(self.dial_input)

        # کی‌پد
        keypad_layout = QVBoxLayout()
        keypad_layout.setSpacing(10)
        keys = [['1', '2', '3'], ['4', '5', '6'], ['7', '8', '9'], ['*', '0', '#']]
        
        for row in keys:
            row_layout = QHBoxLayout()
            row_layout.setSpacing(10)
            row_layout.setDirection(QVBoxLayout.Direction.LeftToRight) # رفع مشکل معکوس شدن اعداد
            
            for key in row:
                btn = QPushButton(key)
                btn.setProperty("class", "KeypadBtn")
                btn.setFixedHeight(55)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.clicked.connect(lambda checked, k=key: self.append_number(k))
                row_layout.addWidget(btn)
            keypad_layout.addLayout(row_layout)
        
        inner_layout.addLayout(keypad_layout)

        # دکمه‌های عملیاتی
        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)
        
        self.btn_call = QPushButton("تماس")
        self.btn_call.setProperty("class", "ActionBtn")
        self.btn_call.setStyleSheet("background: #27ae60; padding: 15px;")
        self.btn_call.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_call.clicked.connect(self.make_call)
        
        self.btn_answer = QPushButton("پاسخ دادن")
        self.btn_answer.setProperty("class", "ActionBtn")
        self.btn_answer.setStyleSheet("background: #f39c12; padding: 15px;")
        self.btn_answer.setVisible(False)
        self.btn_answer.clicked.connect(lambda: self.modem_worker.answer_call(is_ai=False))
        
        self.btn_hangup = QPushButton("قطع تماس")
        self.btn_hangup.setProperty("class", "ActionBtn")
        self.btn_hangup.setStyleSheet("background: #e74c3c; padding: 15px;")
        self.btn_hangup.setVisible(False)
        self.btn_hangup.clicked.connect(self.modem_worker.hangup)
        
        btn_clear = QPushButton("پاک")
        btn_clear.setProperty("class", "ActionBtn")
        btn_clear.setStyleSheet("background: #95a5a6; padding: 15px;")
        btn_clear.setFixedWidth(70)
        btn_clear.clicked.connect(lambda: self.dial_input.setText(""))
        
        action_layout.addWidget(self.btn_call)
        action_layout.addWidget(self.btn_answer)
        action_layout.addWidget(self.btn_hangup)
        action_layout.addWidget(btn_clear)
        inner_layout.addLayout(action_layout)

        # متن وضعیت
        self.status_label = QLabel("سیستم آماده است — حالت فعلی: اپراتور")
        self.status_label.setStyleSheet("color: #7f8c8d; font-size: 13px; border-top: 1px solid #e0e0e0; padding-top: 10px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inner_layout.addWidget(self.status_label)

        container_layout.addWidget(inner_content)
        
        # --- لیست پیغام‌گیر ---
        self.vm_group = QGroupBox("پیام‌های صوتی دریافتی")
        self.vm_group.setStyleSheet("""
            QGroupBox { font-weight: bold; color: #7f8c8d; border-top: 1px solid #e0e0e0; margin-top: 10px; padding-top: 15px;}
            QGroupBox::title { subcontrol-origin: margin; top: -5px; }
        """)
        vm_layout = QVBoxLayout(self.vm_group)
        vm_layout.setContentsMargins(15, 0, 15, 0)
        
        self.vm_list = QListWidget()
        self.vm_list.setStyleSheet("""
            QListWidget { border: none; background: transparent; outline: none; }
            QListWidget::item { border-bottom: 1px solid #f1f3f5; padding: 5px 0; }
        """)
        vm_layout.addWidget(self.vm_list)
        container_layout.addWidget(self.vm_group)

        main_layout.addWidget(self.app_container)

    # ==================== متدهای اجرایی رابط کاربری ====================
    def change_mode(self, mode):
        self.modem_worker.answer_mode = mode
        
        for btn in [self.btn_mode_manual, self.btn_mode_vm, self.btn_mode_ai]:
            btn.setChecked(False)
            
        if mode == 'manual':
            self.btn_mode_manual.setChecked(True)
        elif mode == 'voicemail':
            self.btn_mode_vm.setChecked(True)
        elif mode == 'ai':
            self.btn_mode_ai.setChecked(True)
            
        mode_names = {'manual': 'اپراتور', 'voicemail': 'پیغام‌گیر', 'ai': 'هوش مصنوعی'}
        self.update_status(f"سیستم آماده است — حالت فعلی: {mode_names[mode]}")
        
        if mode != 'ai':
            self.ai_frame.setVisible(False)

    def append_number(self, num):
        self.dial_input.setText(self.dial_input.text() + num)

    def make_call(self):
        number = self.dial_input.text()
        if not number:
            QMessageBox.warning(self, "خطا", "لطفاً ابتدا شماره را وارد کنید.")
            return
        self.modem_worker.make_call(number)

    def update_status(self, msg):
        self.status_label.setText(msg)

    def toggle_alert_color(self):
        self.alert_toggle = not self.alert_toggle
        color = "#d35400" if self.alert_toggle else "#e67e22"
        self.alert_frame.setStyleSheet(f"background-color: {color}; color: white;")

    def on_incoming_call(self, caller_id, ring_count):
        self.update_status(f"تماس ورودی... (زنگ {ring_count})")
        
        if self.modem_worker.answer_mode == 'manual':
            self.alert_label.setText(f"📞 تماس از: {caller_id} (زنگ {ring_count})")
            self.alert_frame.setVisible(True)
            self.alert_timer.start(500)
            self.btn_call.setVisible(False)
            self.btn_answer.setVisible(True)
            self.btn_hangup.setVisible(True)

    def on_call_answered(self, msg):
        self.update_status(msg)
        self.alert_timer.stop()
        self.alert_frame.setVisible(False)
        
        if self.modem_worker.answer_mode == 'ai':
            self.ai_frame.setVisible(True)
            
        self.btn_call.setVisible(False)
        self.btn_answer.setVisible(False)
        self.btn_hangup.setVisible(True)

    def on_call_ended(self, msg):
        self.update_status(msg)
        self.alert_timer.stop()
        self.alert_frame.setVisible(False)
        self.ai_frame.setVisible(False)
        
        self.btn_call.setVisible(True)
        self.btn_answer.setVisible(False)
        self.btn_hangup.setVisible(False)

    def on_voicemail_started(self, caller_id):
        self.update_status(f"در حال ضبط پیام از: {caller_id}")
        self.alert_timer.stop()
        self.alert_frame.setVisible(False)
        self.btn_call.setVisible(False)
        self.btn_answer.setVisible(False)
        self.btn_hangup.setVisible(True)

    def load_voicemails(self):
        self.vm_list.clear()
        if not os.path.exists(VOICEMAIL_DIR): return
        
        files = [f for f in sorted(os.listdir(VOICEMAIL_DIR), reverse=True) if f.endswith('.wav')]
        
        if not files:
            item = QListWidgetItem("پیامی وجود ندارد")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.vm_list.addItem(item)
            return

        for f in files:
            parts = f.split('_')
            caller = parts[1] if len(parts) > 1 else "ناشناس"
            time_str = f"{parts[0][:4]}/{parts[0][4:6]}/{parts[0][6:8]} {parts[1][:2]}:{parts[1][2:4]}" if len(parts) > 1 else ""
            
            item_widget = QWidget()
            item_layout = QHBoxLayout(item_widget)
            item_layout.setContentsMargins(0, 0, 0, 0)
            
            info_label = QLabel(f"{caller}\n<span style='color:#7f8c8d; font-size:11px;'>{time_str}</span>")
            info_label.setTextFormat(Qt.TextFormat.RichText)
            
            btn_play = QPushButton("▶ پخش")
            btn_play.setStyleSheet("background: #3498db; color: white; border-radius: 6px; padding: 6px 12px; font-size: 12px;")
            btn_play.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_play.clicked.connect(lambda checked, filename=f: self.play_vm(filename))
            
            btn_del = QPushButton("حذف")
            btn_del.setStyleSheet("background: #e74c3c; color: white; border-radius: 6px; padding: 6px 12px; font-size: 12px;")
            btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_del.clicked.connect(lambda checked, filename=f: self.delete_vm(filename))
            
            item_layout.addWidget(info_label)
            item_layout.addStretch()
            item_layout.addWidget(btn_play)
            item_layout.addWidget(btn_del)
            
            list_item = QListWidgetItem()
            list_item.setSizeHint(item_widget.sizeHint())
            
            self.vm_list.addItem(list_item)
            self.vm_list.setItemWidget(list_item, item_widget)

    def play_vm(self, filename):
        path = os.path.join(VOICEMAIL_DIR, filename)
        self.update_status("در حال پخش پیام...")
        self.modem_worker.audio_manager.play_wav_file(path)

    def delete_vm(self, filename):
        reply = QMessageBox.question(self, 'تایید', 'آیا از حذف این پیام مطمئن هستید؟',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            path = os.path.join(VOICEMAIL_DIR, filename)
            if os.path.exists(path):
                os.remove(path)
                self.load_voicemails()
                self.update_status("پیام حذف شد.")

    def closeEvent(self, event):
        self.modem_worker.stop()
        self.modem_worker.wait()
        event.accept()

# ==================== نقطه شروع اجرای برنامه ====================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion") # استفاده از استایل فیوژن برای نمایش بهتر روی تمام ویندوزها
    
    window = PhoneHubApp()
    window.show()
    
    sys.exit(app.exec())
