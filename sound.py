import os
import sys
from pygame import mixer


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


# --- Sound Effects Initialization ---
mixer.init()

rock_slide_sound = mixer.Sound(get_resource_path("sounds/rock_metal_slide_1.wav"))
door_open_sound = mixer.Sound(get_resource_path("sounds/qubodup-DoorOpen01.flac"))
coin_sound = mixer.Sound(get_resource_path("sounds/coin.flac"))
select_sound = mixer.Sound(get_resource_path("sounds/Select.wav"))
damage_sound = mixer.Sound(get_resource_path("sounds/06._damage_grunt_male.wav"))
teleport_sound = mixer.Sound(get_resource_path("sounds/172206__fins__teleport.wav"))
wrong_choice_sound = mixer.Sound(get_resource_path("sounds/wrong_choice_sound.wav"))
victory_sound = mixer.Sound(get_resource_path("sounds/Victory!.wav"))

rock_slide_sound.set_volume(0.6)
door_open_sound.set_volume(0.7)
coin_sound.set_volume(0.5)
select_sound.set_volume(0.5)
damage_sound.set_volume(0.6)
teleport_sound.set_volume(0.6)
wrong_choice_sound.set_volume(0.5)
victory_sound.set_volume(0.6)


def play_music(music_file="sounds/dungeon_theme.flac"):
    if not os.path.isabs(music_file):
        resolved_path = get_resource_path(music_file)
    else:
        resolved_path = music_file
    mixer.music.load(resolved_path)
    mixer.music.play(loops=-1)


def stop_music():
    mixer.music.stop()
