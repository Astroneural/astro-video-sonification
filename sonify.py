import os
import cv2
import pretty_midi
import time
import numpy as np
from midi2audio import FluidSynth
from moviepy.editor import VideoFileClip, AudioFileClip

folder_path = "/Path/To/file_frames" # outputted by capture_video.py
file_list = os.listdir(folder_path)
frame_number = len(file_list)

# Variables to tinker: min_object_sizes, brightness_threshold, triggered_box_size, cooldown_period, circle_radius

fps = 25 # as of this version, must be manually checked

circle_radius = 300

min_object_size = 20

brightness_threshold = 150

frames_with_circles = []

frames_with_boxes = []

twinkle_notes = [60, 62, 64, 66, 68, 70, 72, 74, 76, 78, 80, 82, 84, 86, 88, 90, 92, 94]  # C wholetone

midi = pretty_midi.PrettyMIDI()

instrument_harp = pretty_midi.Instrument(program=pretty_midi.instrument_name_to_program('Ocarina'))  # list available at https://github.com/craffel/pretty-midi/blob/main/pretty_midi/constants.py
instrument_strings = pretty_midi.Instrument(program=pretty_midi.instrument_name_to_program('Pad 4 (choir)'))

triggered_box_size = 5
cooldown_period = 0.3
triggered_regions = []

for i in range(frame_number): # loop through each frame
    filename = os.path.join(folder_path, f"frame_{i:04d}.jpg")
    image = cv2.imread(filename)
    
    if image is None:
        continue
    
    circle_center = (image.shape[1] // 2, image.shape[0] // 2) # draw a circle
    cv2.circle(image, circle_center, circle_radius, (0, 50, 0), 2)
    
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, threshold_image = cv2.threshold(gray_image, brightness_threshold, 255, cv2.THRESH_BINARY) # find bright objects
    contours, _ = cv2.findContours(threshold_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    for contour in contours:
        for point in contour:
            dist_to_center = np.linalg.norm(np.array(point[0]) - np.array(circle_center))
            if abs(dist_to_center - circle_radius) < 10: # find objects on/near the circle's circumference
                x, y, w, h = cv2.boundingRect(contour)
                object_location = (x + w // 2, y + h // 2)
                object_size = max(w, h)
                object_brightness = np.mean(gray_image[y:y+h, x:x+w])
                
                if object_size > min_object_size:
                    time_stamp = i / float(fps)  # begin sonification code
                    note_index = i % len(twinkle_notes)
                    obj_box = (object_location[0] - triggered_box_size // 2,
                               object_location[1] - triggered_box_size // 2,
                               object_location[0] + triggered_box_size // 2,
                               object_location[1] + triggered_box_size // 2)
                    
                    is_duplicate = False
                    for region in triggered_regions: # counter annoying pulsing noise when large objects remain on the circumference
                        region_box, trigger_time = region
                        if (obj_box[0] < region_box[2] and obj_box[2] > region_box[0] and
                            obj_box[1] < region_box[3] and obj_box[3] > region_box[1]):
                            if (time_stamp - trigger_time) < cooldown_period:
                                is_duplicate = True
                                break

                    if not is_duplicate:
                        if object_size < 50: # for stars
                            instrument = instrument_harp
                            brightness_normalized = 1 - (object_brightness / 255.0)
                            note_index = int(brightness_normalized * (len(twinkle_notes) - 1))
                            pitch = twinkle_notes[note_index]
                            volume = 20 * np.log10(object_size / image.shape[0]) + 100
                        else:
                            instrument = instrument_strings
                            brightness_normalized = 1 - (object_brightness / 255.0)
                            note_index = int(brightness_normalized * (len(twinkle_notes) - 1))
                            pitch = twinkle_notes[note_index]
                            volume = 20 * np.log10(object_size / image.shape[0]) + 100


                        if len(instrument.notes) > 0 and instrument.notes[-1].pitch == pitch:
                            instrument.notes[-1].end = time_stamp + 0.2 # allow for elongation
                        else:
                            note = pretty_midi.Note(
                                velocity=int(volume),
                                pitch=int(pitch),
                                start=time_stamp,
                                end=time_stamp + 0.1
                            )
                            instrument.notes.append(note)
                        
                        instrument.notes.append(note)
                        triggered_regions.append((obj_box, time_stamp))                    
                    
                if object_size < 50:
                    cv2.rectangle(image, (x, y), (x + w, y + h), (255, 0, 255), 2)  # magenta objects are "stars"
                else:
                    cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 255), 2)  # yellow objects are "nebulae"

                progress_bar_width = 40
                progress = (i / frame_number) * progress_bar_width
                loading_message = f"Processing frame {i}/{frame_number} [{'=' * int(progress)}{' ' * (progress_bar_width - int(progress))}]"
                print(loading_message, end="\r")
    
    frames_with_circles.append(image.copy())
    frames_with_boxes.append(image.copy())

timestr = time.strftime("%H-%M-%S")
video_path = 'raw_videos/frames_with_boxes_' + timestr + '.mp4'
box_video = cv2.VideoWriter(video_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (image.shape[1], image.shape[0]))
for frame in frames_with_boxes:
    box_video.write(frame)
box_video.release()

midi.instruments.append(instrument_harp)
midi.instruments.append(instrument_strings)

midi_path = 'raw_audios/twinkles_' + timestr + '.mid'
midi.write(midi_path)

def convert_midi_to_wav(midi_file, output_file, soundfont_path):
    fluidsynth = FluidSynth(sound_font=soundfont_path)
    fluidsynth.midi_to_audio(midi_file, output_file)

midi_file = midi_path
output_file = midi_path + '.wav'
soundfont_path = '/Path/to/TimGM6mb.sf'  # download at https://github.com/craffel/pretty-midi/blob/main/pretty_midi/TimGM6mb.sf2
convert_midi_to_wav(midi_file, output_file, soundfont_path)

video = VideoFileClip(video_path)
audio = AudioFileClip(output_file)

final_video = video.set_audio(audio)
final_video.write_videofile('sonified_video_' + timestr + '.mp4', codec='libx264', audio_codec='libmp3lame') # audio codec may be changed to aac. VS Code couldn't play audio code embedded that way, so this was better for my workflow.
