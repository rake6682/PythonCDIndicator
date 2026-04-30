import os
import sys
import pygame

# --- macOS-specific setup for transparent window ---
# This tells SDL (used by Pygame) to allow transparency
os.environ['SDL_VIDEO_WINDOW_POS'] = "100,100"  # Optional: set window position
os.environ['SDL_VIDEO_MAC_FULLSCREEN_SPACES'] = '1'

# Initialize Pygame
pygame.init()

# Create a window with NOFRAME (no title bar)
screen = pygame.display.set_mode((500, 300), pygame.NOFRAME)

# Set the window transparency (0.0 = fully transparent, 1.0 = opaque)
try:
    pygame.display.set_alpha(0.5)  # Semi-transparent
except Exception:
    print("Warning: Window alpha not supported on this platform.")

# Fill the screen with a transparent color
screen.fill((0, 0, 0, 0))  # RGBA: fully transparent background

# Draw something visible
pygame.draw.circle(screen, (255, 0, 0), (250, 150), 50)  # Red circle

pygame.display.flip()

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (
            event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
        ):
            running = False

pygame.quit()
sys.exit()
