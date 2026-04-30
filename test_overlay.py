import sys
import platform
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt5.QtGui import QPainter, QColor, QPen, QFont
from PyQt5.QtCore import Qt, QTimer

class TransparentOverlay(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Window setup
        self.setWindowTitle("CD Indicator")
        self.setGeometry(0, 0, 1280, 720)
        
        # Make window transparent and always on top
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        # Window styling for different platforms
        if platform.system() == 'Darwin':  # macOS
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        elif platform.system() == 'Windows':
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
                'max_cooldown': 3.0
            }
        
        # Skill key mapping
        self.skill_keys = {
            Qt.Key_1: 0, Qt.Key_2: 1, Qt.Key_3: 2, Qt.Key_4: 3,
            Qt.Key_5: 4, Qt.Key_6: 5, Qt.Key_7: 6, Qt.Key_8: 7,
            Qt.Key_9: 8, Qt.Key_0: 9, Qt.Key_Minus: 10, Qt.Key_Equal: 11
        }
        
        self.currently_equipped = None
        
        # Update timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_cooldowns)
        self.timer.start(16)  # ~60 FPS
    
    def update_cooldowns(self):
        """Update cooldowns"""
        dt = 0.016  # 16ms
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
    
    def keyPressEvent(self, event):
        """Handle key presses"""
        if event.key() in self.skill_keys:
            self.currently_equipped = self.skill_keys[event.key()]
    
    def mousePressEvent(self, event):
        """Handle mouse clicks"""
        if self.currently_equipped is None:
            return
        
        skill = self.skills[self.currently_equipped]
        
        if event.button() == 1:  # Left click
            if skill['left_cooldown'] == 0:
                skill['left_cooldown'] = skill['max_cooldown']
        elif event.button() == 2:  # Right click
            if skill['right_cooldown'] == 0:
                skill['right_cooldown'] = skill['max_cooldown']
    
    def paintEvent(self, event):
        """Draw the overlay"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Constants
        rect_width = 60
        rect_height = 60
        rect_spacing = 10
        
        # Calculate starting position
        total_width = 12 * rect_width + 11 * rect_spacing
        start_x = (1280 - total_width) // 2
        start_y = 720 - rect_height - 20
        
        # Draw each skill
        for i in range(12):
            skill = self.skills[i]
            x = start_x + i * (rect_width + rect_spacing)
            y = start_y
            
            # Draw left-click rectangle
            self.draw_cooldown_rect(painter, x, y, rect_width, rect_height, 
                                   skill['left_cooldown'], skill['max_cooldown'])
            
            # Draw right-click rectangle if active
            if skill['right_cooldown'] > 0:
                self.draw_cooldown_rect(painter, x, y - rect_height - 5, rect_width, rect_height,
                                       skill['right_cooldown'], skill['max_cooldown'], is_right=True)
            
            # Draw equipped indicator
            if self.currently_equipped == i:
                pen = QPen(QColor(255, 255, 0), 3)
                painter.setPen(pen)
                painter.drawRect(x - 3, y - 3, rect_width + 6, rect_height + 6)
    
    def draw_cooldown_rect(self, painter, x, y, width, height, cooldown, max_cooldown, is_right=False):
        """Draw a rectangle with cooldown effect"""
        # Background color
        if cooldown > 0:
            color = QColor(100, 50, 200, 180)
        else:
            color = QColor(50, 150, 255, 180)
        
        # Draw main rectangle
        painter.fillRect(x, y, width, height, color)
        
        # Draw cooldown shrinking bar (height only)
        if cooldown > 0:
            cooldown_percentage = cooldown / max_cooldown
            shrink_height = int(height * cooldown_percentage)
            shrink_y = y + height - shrink_height
            
            cooldown_color = QColor(150, 100, 50, 180)
            painter.fillRect(x, shrink_y, width, shrink_height, cooldown_color)
        
        # Draw border
        pen = QPen(QColor(255, 255, 255, 100), 2)
        painter.setPen(pen)
        painter.drawRect(x, y, width, height)
        
        # Draw indicator for right-click
        if is_right:
            pen = QPen(QColor(255, 100, 100, 150), 2)
            painter.setPen(pen)
            painter.drawEllipse(x + width - 16, y + 8, 10, 10)

def main():
    app = QApplication(sys.argv)
    overlay = TransparentOverlay()
    overlay.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
