# CD Indicator

A cooldown indicator program for video games, displaying 12 skill slots with separate left and right-click cooldowns.

## Features

- **12 Skill Slots**: Mapped to keys 1-9, 0, -, and =
- **Separate Cooldowns**: Each skill has independent left-click and right-click cooldowns
- **Smooth Animation**: Rectangles shrink smoothly as cooldown progresses
- **Dual-Click Display**: When both left and right clicks are used, the right-click cooldown appears above the left-click indicator
- **Visual Feedback**: 
  - Yellow border shows which skill is currently equipped
  - Red indicator dot on right-click rectangles for identification
  - Color changes during cooldown

## Controls

| Key | Action |
|-----|--------|
| 1-9, 0, -, = | Equip corresponding skill |
| Left Mouse Button | Use left-click version of equipped skill |
| Right Mouse Button | Use right-click version of equipped skill |

## How to Use

1. Press a key (1-9, 0, -, =) to equip a skill
2. Left-click to use the left-click version (starts left cooldown)
3. Right-click to use the right-click version (starts right cooldown)
4. Watch as the rectangles shrink during cooldown
5. Once cooldown completes, the rectangle returns to full size and can be used again

## Installation

Install the required dependency:

```bash
pip install PyQt5
pip install pynput
```

## Running

```bash
python main.py
```

## Cooldown Settings

By default, each skill has a 3-second cooldown. To adjust this, modify the `COOLDOWN_TIME` constant in `main.py`:

```python
COOLDOWN_TIME = 3.0  # Change this value in seconds
```

## Visual Design

- Rectangles are semi-transparent with smooth shrinking effect
- Darker color indicates active cooldown
- Original blue color shows ready state
- Left-click rectangles are positioned at the bottom
- Right-click rectangles pop up above when both are active
