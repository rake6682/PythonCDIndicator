
import AppKit
import objc
from Cocoa import NSColor, NSFont, NSBezierPath, NSAttributedString, NSForegroundColorAttributeName, NSFontAttributeName

class OverlayContentView(AppKit.NSView):
    def initWithFrame_(self, frame):
        self = objc.super(OverlayContentView, self).initWithFrame_(frame)
        if self:
            self.shapes = []
        return self

    def drawRect_(self, rect):
        for item in self.shapes:
            color = item.get('color', NSColor.redColor())
            color.set()
            if item['type'] == 'rect':
                NSBezierPath.fillRect_(item['rect'])
            elif item['type'] == 'text':
                text = item['text']
                font_size = item.get('font_size', 24)
                font = NSFont.systemFontOfSize_(font_size)
                attr = {NSFontAttributeName: font, NSForegroundColorAttributeName: color}
                ns_text = NSAttributedString.alloc().initWithString_attributes_(text, attr)
                ns_text.drawAtPoint_(item['rect'][:2])

    def add_box(self, x, y, width, height, color=NSColor.redColor()):
        self.shapes.append({'type': 'rect', 'rect': ((x, y), (width, height)), 'color': color})
        self.setNeedsDisplay_(True)

    def add_text(self, x, y, text, font_size=24, color=NSColor.redColor()):
        self.shapes.append({'type': 'text', 'rect': (x, y, 0, 0), 'text': text, 'font_size': font_size, 'color': color})
        self.setNeedsDisplay_(True)


class OverlayWindow(AppKit.NSWindow):
    def initWithFullScreenFrame_(self, frame):
        self = objc.super(OverlayWindow, self).initWithContentRect_styleMask_backing_defer_(
            frame,
            AppKit.NSWindowStyleMaskBorderless,
            AppKit.NSBackingStoreBuffered,
            False
        )
        if self:
            self.setLevel_(AppKit.NSStatusWindowLevel)
            self.setOpaque_(False)
            self.setBackgroundColor_(NSColor.clearColor())
            self.setIgnoresMouseEvents_(True)

            self.content_view = OverlayContentView.alloc().initWithFrame_(frame)
            self.setContentView_(self.content_view)
        return self

    def add_box(self, x, y, width, height, color=NSColor.redColor()):
        self.content_view.add_box(x, y, width, height, color)

    def add_text(self, x, y, text, font_size=24, color=NSColor.redColor()):
        self.content_view.add_text(x, y, text, font_size, color)


# Get main screen frame
screen = AppKit.NSScreen.mainScreen()
frame = screen.frame()

window = OverlayWindow.alloc().initWithFullScreenFrame_(frame)
window.makeKeyAndOrderFront_(None)

# Example shapes
window.add_box(100, 100, 300, 150)
window.add_text(150, 300, "Full Screen Overlay", font_size=48)

# Run app
AppKit.NSApp = AppKit.NSApplication.sharedApplication()
AppKit.NSApp.run()