import sys
import json
import os
import platform
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt5.QtGui import QPainter, QColor, QPen
from PyQt5.QtCore import Qt, QTimer
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
RECT_START_X = CONFIG['rectangles'].get('start_x', None)
RECT_START_Y = CONFIG['rectangles'].get('start_y', None)

COLORS = CONFIG['colors']
TIMERS = CONFIG['timers']
VISIBILITY_CONFIG = CONFIG['visibility']

# Build skill cooldowns from config
SKILL_COOLDOWNS = {}
for skill_id, cooldowns in CONFIG['skills'].items():
    SKILL_COOLDOWNS[int(skill_id)] = {
        'left': cooldowns['left'],
        'right': cooldowns['right']
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
        for i in range(12):
            self.skills[i] = {
                'left_cooldown': 0.0,
                'right_cooldown': 0.0,
                'left_max_cooldown': SKILL_COOLDOWNS[i]['left'],
                'right_max_cooldown': SKILL_COOLDOWNS[i]['right']
            }
        
        # Skill key mapping (Qt keys - no longer used, replaced with global keyboard listener)
        # Kept for reference
        self.skill_keys = {
            Qt.Key_1: 0, Qt.Key_2: 1, Qt.Key_3: 2, Qt.Key_4: 3,
            Qt.Key_5: 4, Qt.Key_6: 5, Qt.Key_7: 6, Qt.Key_8: 7,
            Qt.Key_9: 8, Qt.Key_0: 9, Qt.Key_Minus: 10, Qt.Key_Equal: 11
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
                self.currently_equipped = None
                return
            
            # Map pynput keys to skill indices
            key_map = {
                '1': 0, '2': 1, '3': 2, '4': 3, '5': 4, '6': 5, '7': 6, '8': 7, '9': 8, '0': 9, '-': 10, '=': 11
            }
            
            if hasattr(key, 'char') and key.char in key_map:
                skill_index = key_map[key.char]
                if self.manual_visibility == True or (self.manual_visibility is None and self.overlay_visible):
                    # Toggle: if already equipped, unequip; otherwise equip; only when not hidden 
                    if self.currently_equipped == skill_index:
                        self.currently_equipped = None
                    else:
                        self.currently_equipped = skill_index
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
        self.update()
    
    def on_mouse_click(self, x, y, button, pressed):
        """Handle global mouse clicks"""
        if not pressed or self.currently_equipped is None:
            return
        
        skill = self.skills[self.currently_equipped]
        
        if button == mouse.Button.left:
            if skill['left_cooldown'] == 0:
                skill['left_cooldown'] = skill['left_max_cooldown']
        elif button == mouse.Button.right:
            if skill['right_cooldown'] == 0:
                skill['right_cooldown'] = skill['right_max_cooldown']
    
    def update_cooldowns(self):
        """Update cooldowns"""
        dt = TIMERS['update_interval_ms'] / 1000.0  # Convert to seconds from config
        for skill in self.skills.values():
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
        
        start_x = RECT_START_X 
        start_y = RECT_START_Y 
        
        # Draw each skill
        for i in range(12):
            skill = self.skills[i]
            x = start_x + i * (rect_width + rect_spacing)
            y = start_y
            
            # Draw left-click rectangle
            self.draw_cooldown_rect(painter, x, y, rect_width, rect_height, 
                                   skill['left_cooldown'], skill['left_max_cooldown'])
            
            # Draw right-click rectangle if active
            if skill['right_cooldown'] > 0:
                self.draw_cooldown_rect(painter, x, y - rect_height - 5, rect_width, rect_height,
                                       skill['right_cooldown'], skill['right_max_cooldown'], is_right=True)
            
            # Draw equipped indicator
            if self.currently_equipped == i:
                pen = QPen(QColor(COLORS['equipped_indicator'][0], COLORS['equipped_indicator'][1], 
                                 COLORS['equipped_indicator'][2]), COLORS['equipped_indicator_width'])
                painter.setPen(pen)
                painter.drawRect(x - 3, y - 3, rect_width + 6, rect_height + 6)
    
    def draw_cooldown_rect(self, painter, x, y, width, height, cooldown, max_cooldown, is_right=False):
        """Draw a rectangle with cooldown effect"""
        # Background color from config
        if cooldown > 0:
            color = QColor(COLORS['rect_cooldown'][0], COLORS['rect_cooldown'][1], 
                          COLORS['rect_cooldown'][2], COLORS['rect_cooldown_alpha'])
        else:
            color = QColor(COLORS['rect_ready'][0], COLORS['rect_ready'][1], 
                          COLORS['rect_ready'][2], COLORS['rect_ready_alpha'])
        
        # Draw main rectangle
        painter.fillRect(x, y, width, height, color)
        
        # Draw cooldown shrinking bar (height only)
        if cooldown > 0:
            cooldown_percentage = cooldown / max_cooldown
            shrink_height = int(height * cooldown_percentage)
            shrink_y = y + height - shrink_height
            
            cooldown_color = QColor(COLORS['rect_cooldown_bar'][0], COLORS['rect_cooldown_bar'][1],
                                   COLORS['rect_cooldown_bar'][2], COLORS['rect_cooldown_bar_alpha'])
            painter.fillRect(x, shrink_y, width, shrink_height, cooldown_color)
        
        # Draw border from config
        pen = QPen(QColor(COLORS['rect_border'][0], COLORS['rect_border'][1], 
                         COLORS['rect_border'][2], COLORS['rect_border_alpha']), 
                  COLORS['rect_border_width'])
        painter.setPen(pen)
        painter.drawRect(x, y, width, height)
        
        # Draw indicator for right-click
        if is_right:
            pen = QPen(QColor(COLORS['right_click_indicator'][0], COLORS['right_click_indicator'][1],
                             COLORS['right_click_indicator'][2], COLORS['right_click_indicator_alpha']), 2)
            painter.setPen(pen)
            indicator_size = COLORS['right_click_indicator_size']
            painter.drawEllipse(x + width - indicator_size - 6, y + 8, indicator_size, indicator_size)

def main():
    app = QApplication(sys.argv)
    overlay = TransparentOverlay()
    overlay.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
