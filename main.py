import sys
import json
import os
import platform
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QGuiApplication
from PyQt5.QtCore import Qt, QTimer, QRect, QElapsedTimer
from pynput import mouse, keyboard

# Platform-specific window detection
if platform.system() == 'Darwin':
    import AppKit
elif platform.system() == 'Windows':
    try:
        import win32gui
        import win32process
    except ImportError:
        pass

# Load configuration
def load_config():
    """Load configuration from config.json"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'r') as f:
        return json.load(f)

CONFIG = load_config()

# Extract configuration values
WINDOW_WIDTH = CONFIG['window']['width']
WINDOW_HEIGHT = CONFIG['window']['height']
WINDOW_TITLE = CONFIG['window']['title']

RECT_WIDTH = CONFIG['rectangles']['width']
RECT_HEIGHT = CONFIG['rectangles']['height']
RECT_SPACING = CONFIG['rectangles']['spacing']
RECT_BOTTOM_OFFSET = CONFIG['rectangles']['bottom_offset']
START_X = CONFIG['rectangles']['start_x']
START_Y = CONFIG['rectangles']['start_y']

TEXT_CONFIG = CONFIG['text']
COLORS = CONFIG['colors']
TIMERS = CONFIG['timers']
VISIBILITY_CONFIG = CONFIG['visibility']

# Build skill settings from config
SKILL_SETTINGS = {}
for skill_id, data in CONFIG['skills'].items():
    SKILL_SETTINGS[int(skill_id)] = {
        'left': data['left'],
        'right': data['right'],
        'modifier': data.get('modifier', 0)
    }

def get_active_window_title():
    """Get the title of the currently active window"""
    try:
        if platform.system() == 'Darwin':  # macOS
            app = AppKit.NSWorkspace.sharedWorkspace()
            active_app = app.activeApplication()
            return active_app.get('NSApplicationName', '')
        elif platform.system() == 'Windows':
            hwnd = win32gui.GetForegroundWindow()
            return win32gui.GetWindowText(hwnd)
    except:
        pass
    return ''
def get_pixel_brightness(screen, x, y):
    color = screen.grabWindow(0, x, y, 1, 1).toImage().pixelColor(0, 0)
    return (color.red() + color.green() + color.blue()) / 3.0

def is_roblox_active():
    """Check if Roblox is the active window"""
    title = get_active_window_title()
    return VISIBILITY_CONFIG['roblox_window_name'] in title

class TransparentOverlay(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Window setup
        self.setWindowTitle(WINDOW_TITLE)
        self.setGeometry(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
        
        # Make window transparent and always on top
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        # Central widget
        self.widget = QWidget()
        self.setCentralWidget(self.widget)
        
        # Skills data
        self.skills = {}
        self.skill_timers = {}
        for i in range(12):
            self.skills[i] = {
                'left_cooldown': 0.0,
                'right_cooldown': 0.0,
                'left_max_cooldown': SKILL_SETTINGS[i]['left'],
                'right_max_cooldown': SKILL_SETTINGS[i]['right'],
                'modifier': SKILL_SETTINGS[i]['modifier'],
                'left_pending': False,
                'right_pending': False
            }
            # Timer for modifier 1 spam-click detection
            self.skill_timers[i] = {
                'last_click_timer': None
            }
        
        self.currently_equipped = None
        
        # Visibility state
        self.overlay_visible = False
        self.manual_visibility = None  # None = auto (follow Roblox), True = always on, False = always off
        
        # Update timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_cooldowns)
        self.timer.start(TIMERS['update_interval_ms'])  # From config
        
        # Roblox detection timer
        self.roblox_timer = QTimer()
        self.roblox_timer.timeout.connect(self.check_roblox_window)
        self.roblox_timer.start(TIMERS['roblox_check_interval_ms'])  # From config

        # Skill equip detection timer
        if CONFIG.get('equip_detection', {}).get('enabled', True):
            self.equip_timer = QTimer()
            self.equip_timer.timeout.connect(self.update_equipped_skill)
            self.equip_timer.start(TIMERS['equip_check_interval_ms']) 

        # Global mouse listener
        self.mouse_listener = mouse.Listener(on_click=self.on_mouse_click)
        self.mouse_listener.start()
        
        # Global keyboard listener
        self.keyboard_listener = keyboard.Listener(on_press=self.on_key_press)
        self.keyboard_listener.start()
    
    def on_key_press(self, key):
        """Handle global key presses"""
        try:
            # Handle special keys; Enter to force show, Esc to toggle, / to force hide
            # L to reset cooldowns (for testing)
            if key == keyboard.Key.enter:
                self.manual_visibility = True
                return
            elif key == keyboard.Key.esc:
                if self.manual_visibility is None:
                    self.manual_visibility = not self.overlay_visible
                else:
                    self.manual_visibility = not self.manual_visibility
                return

            # Handle / key
            if hasattr(key, 'char') and key.char == '/':
                self.manual_visibility = False
                return

            # Handle L key (reset cooldowns and equipped skill for testing)
            if hasattr(key, 'char') and key.char == 'l':
                for skill in self.skills.values():
                    skill['left_cooldown'] = 0
                    skill['right_cooldown'] = 0
                    skill['left_pending'] = False
                    skill['right_pending'] = False
                for timer_state in self.skill_timers.values():
                    timer_state['last_click_timer'] = None
                self.currently_equipped = None
                return
        # Handles equips based on key inputs; only if equip detection is disabled 
            # Map pynput keys to skill indices
            # key_map = {
            #     '1': 0, '2': 1, '3': 2, '4': 3, '5': 4, '6': 5, '7': 6, '8': 7, '9': 8, '0': 9, '-': 10, '=': 11
            # }
            
            # if hasattr(key, 'char') and key.char in key_map: 
            #     skill_index = key_map[key.char]
            #     if self.manual_visibility == True or (self.manual_visibility is None and self.overlay_visible):
            #         # Toggle: if already equipped, unequip; otherwise equip; only when not hidden 
            #         if self.currently_equipped == skill_index:
            #             self.currently_equipped = None
            #         else:
            #             self.currently_equipped = skill_index
        except AttributeError:
            pass
    
    def check_roblox_window(self):
        """Check if Roblox is active and update visibility"""
        if self.manual_visibility is not None:
            # Manual override is active
            self.overlay_visible = self.manual_visibility
        else:
            # Auto mode - follow Roblox window
            self.overlay_visible = is_roblox_active()

        # Always hide if no roblox
        # if not is_roblox_active():
        #     self.overlay_visible = False
        self.update()
    
    def on_mouse_click(self, x, y, button, pressed):
        if not pressed or self.currently_equipped is None:
            return

        skill = self.skills[self.currently_equipped]

        if skill['modifier'] == 0:
            if button == mouse.Button.left and skill['left_cooldown'] == 0:
                skill['left_cooldown'] = skill['left_max_cooldown']
            elif button == mouse.Button.right and skill['right_cooldown'] == 0:
                skill['right_cooldown'] = skill['right_max_cooldown']

        elif skill['modifier'] == 1:
            timer = self.skill_timers[self.currently_equipped]['last_click_timer']
            if timer is None:
                timer = QElapsedTimer()
                self.skill_timers[self.currently_equipped]['last_click_timer'] = timer
            timer.restart()

            if button == mouse.Button.left:
                skill['left_pending'] = True
            elif button == mouse.Button.right:
                skill['right_pending'] = True 

    # Handles equips based on brightness
    def update_equipped_skill(self):
        if not self.overlay_visible or not CONFIG.get('equip_detection', {}).get('enabled', True):
            self.currently_equipped = None
            return

        screen = QGuiApplication.primaryScreen()
        if screen is None:
            self.currently_equipped = None
            return

        detect_cfg = CONFIG['equip_detection']
        offset_x = detect_cfg.get('sample_offset_x', RECT_WIDTH // 2)
        offset_y = detect_cfg.get('sample_offset_y', RECT_HEIGHT // 2)
        start_x = START_X
        start_y = START_Y - RECT_BOTTOM_OFFSET

        best_index = None
        best_brightness = -1

        for i in range(12):
            x = start_x + i * (RECT_WIDTH + RECT_SPACING) + offset_x
            y = start_y - RECT_HEIGHT + offset_y
            brightness = get_pixel_brightness(screen, x, y)

            if brightness > best_brightness:
                best_brightness = brightness
                best_index = i

        self.currently_equipped = best_index 
    
    def update_cooldowns(self):
        dt = TIMERS['update_interval_ms'] / 1000.0

        for i, skill in self.skills.items():
            # Checks if we still spamming clicks; if we stopped, then start the cd
            if skill['modifier'] == 1:
                timer = self.skill_timers[i]['last_click_timer']
                if timer is not None and timer.isValid():
                    if timer.elapsed() >= TIMERS['modifier_1_no_click_time_ms']:
                        if skill['left_pending'] and skill['left_cooldown'] == 0:
                            skill['left_cooldown'] = skill['left_max_cooldown']
                            skill['left_pending'] = False

                        if skill['right_pending'] and skill['right_cooldown'] == 0:
                            skill['right_cooldown'] = skill['right_max_cooldown']
                            skill['right_pending'] = False

                        self.skill_timers[i]['last_click_timer'] = None
            # Standard cd timer
            if skill['left_cooldown'] > 0:
                skill['left_cooldown'] -= dt
                if skill['left_cooldown'] < 0:
                    skill['left_cooldown'] = 0

            if skill['right_cooldown'] > 0:
                skill['right_cooldown'] -= dt
                if skill['right_cooldown'] < 0:
                    skill['right_cooldown'] = 0

        self.update()
    
    def paintEvent(self, event):
        """Draw the overlay"""
        # Only draw if overlay is visible
        if not self.overlay_visible:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Constants from config
        rect_width = RECT_WIDTH
        rect_height = RECT_HEIGHT
        rect_spacing = RECT_SPACING
        
        start_x = START_X
        start_y = START_Y - RECT_BOTTOM_OFFSET
        
        # Draw each skill
        for i in range(12):
            skill = self.skills[i]
            x = start_x + i * (rect_width + rect_spacing)
            
            # Draw equipped indicator (highlight the skill if equipped)
            if self.currently_equipped == i:
                pen = QPen(QColor(COLORS['equipped_indicator'][0], COLORS['equipped_indicator'][1], 
                                 COLORS['equipped_indicator'][2]), COLORS['equipped_indicator_width'])
                painter.setPen(pen)
                painter.drawRect(x - 3, start_y - rect_height - 3, rect_width + 6, rect_height + 6)
            # Draw left/right click text with "/" separator
            self.draw_skill_text(painter, x, start_y, rect_width, rect_height, skill)
        
        # Debug brightness sampling points for equip detection
        detect_cfg = CONFIG.get('equip_detection', {})
        offset_x = detect_cfg.get('sample_offset_x', RECT_WIDTH // 2)
        offset_y = detect_cfg.get('sample_offset_y', RECT_HEIGHT // 2)

        if detect_cfg.get('enabled', False):
            painter.setPen(QPen(QColor(0, 255, 255, 200), 2))
            painter.setBrush(Qt.NoBrush)

            for i in range(12):
                sample_x = start_x + i * (rect_width + rect_spacing) + offset_x
                sample_y = start_y - rect_height + offset_y
                painter.drawEllipse(sample_x - 4, sample_y - 4, 8, 8)
    
    def draw_skill_text(self, painter, x, y, width, height, skill):
        if skill['left_cooldown'] > 0:
            left_text = f"{skill['left_cooldown']:.1f}"
            left_color = QColor(
            TEXT_CONFIG['left_click_color'][0],
            TEXT_CONFIG['left_click_color'][1],
            TEXT_CONFIG['left_click_color'][2],
            TEXT_CONFIG['left_click_alpha']
        )
        else:
            left_text = "RDY"
            left_color = QColor(
                TEXT_CONFIG['left_ready_color'][0],
                TEXT_CONFIG['left_ready_color'][1],
                TEXT_CONFIG['left_ready_color'][2],
                TEXT_CONFIG['left_ready_alpha']
            )

        if skill['right_cooldown'] > 0:
            right_text = f"{skill['right_cooldown']:.1f}"
            right_color = QColor(
            TEXT_CONFIG['right_click_color'][0],
            TEXT_CONFIG['right_click_color'][1],
            TEXT_CONFIG['right_click_color'][2],
            TEXT_CONFIG['right_click_alpha']
        )
        else:
            right_text = "RDY"
            right_color = QColor(
                TEXT_CONFIG['right_ready_color'][0],
                TEXT_CONFIG['right_ready_color'][1],
                TEXT_CONFIG['right_ready_color'][2],
                TEXT_CONFIG['right_ready_alpha']
            )

        font = QFont(TEXT_CONFIG['font_family'], TEXT_CONFIG['font_size'])
        font.setBold(True)
        painter.setFont(font)

        metrics = painter.fontMetrics()
        left_w = metrics.horizontalAdvance(left_text)
        sep_w = metrics.horizontalAdvance("/")
        right_w = metrics.horizontalAdvance(right_text)
        total_w = left_w + sep_w + right_w

        text_y = y - height
        left_x = x + (width - total_w) // 2
        baseline_y = text_y + height + 5 

        painter.setPen(left_color)
        painter.drawText(left_x, baseline_y, left_text)

        painter.setPen(QColor(255, 255, 255, 200))
        painter.drawText(left_x + left_w, baseline_y, "/")

        painter.setPen(right_color)
        painter.drawText(left_x + left_w + sep_w, baseline_y, right_text) 
    

def main():
    app = QApplication(sys.argv)
    overlay = TransparentOverlay()
    overlay.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
