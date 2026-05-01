# CD Indicator

A cooldown indicator program for rogue lineage, displaying 12 skill slots with separate left and right-click cooldowns.

## Features

- **12 Skill Slots**: Mapped to keys 1-9, 0, -, and =
- **Separate Cooldowns**: Each skill has independent left-click and right-click cooldowns
- **Dual-Click Display**: When both left and right clicks are used, the right-click cooldown appears beside the left click indicator
- **Visual Feedback**: 
  - Yellow border shows which skill is currently equipped
  - Text shows RDY when skill is ready
  - Color changes during cooldown or mode

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
5. Once cooldown completes, skill can be re-used
6. Configure to your heart's content in config.py

## Installation

Install the required dependencies:

```bash
pip install PyQt5
pip install pynput
```

## Running

```bash
python main.py
```

## Cooldown Settings
- Modifer 0 to start cd on press, modifier 1 to start cd after you stop clicking(for moves that you usually spam like flock/grapple/shadowrush)
- Mode is for moves like bane; the mode timer will run, then the cd timer will run

## Visual Settings

- Change window size and height to be as big as you want; window is invisible anyways
- Adjust start_x and start_y so that the equip indicator lines up with your hotbar
- Adjust rectangle size and spacing so that indicator lines up correctly
- Adjust bottom offset if its too close to the bottom of your screen (or just adjust start_y)
- Left_click_color and right_click_color are the colors and alphas while the move is on cd
- left_ready color and right_ready color are the colors and alphas while move is off cd
- mode color and alpha is the color/alpha while the mode of the skill is active
- 

## Other Features
- equip detection attempts to use brightness to automatically tell what you have equipped (doesn't work well atm)
- Adjust timers to update the intervals the program uses to update cds/check if roblox is running/waits for you to stop clicking for modifier 1 skills
