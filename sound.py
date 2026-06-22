from pygame import mixer

# --- Sound Effects Initialization ---
mixer.init()

rock_slide_sound = mixer.Sound("sounds/rock_metal_slide_1.wav")
door_open_sound = mixer.Sound("sounds/qubodup-DoorOpen01.flac")
coin_sound = mixer.Sound("sounds/coin.flac")
select_sound = mixer.Sound("sounds/Select.wav")
damage_sound = mixer.Sound("sounds/06._damage_grunt_male.wav")
teleport_sound = mixer.Sound("sounds/172206__fins__teleport.wav")
wrong_choice_sound = mixer.Sound("sounds/wrong_choice_sound.wav")

rock_slide_sound.set_volume(0.6)
door_open_sound.set_volume(0.7)
coin_sound.set_volume(0.5)
select_sound.set_volume(0.5)
damage_sound.set_volume(0.6)
teleport_sound.set_volume(0.6)
wrong_choice_sound.set_volume(0.5)


def play_music(music_file="sounds/dungeon_theme.flac"):
    mixer.music.load(music_file)
    mixer.music.play(loops=-1)


def stop_music():
    mixer.music.stop()
