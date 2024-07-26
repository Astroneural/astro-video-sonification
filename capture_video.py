import cv2
video_capture = cv2.VideoCapture('carina.mp4')
frame_number = 0

while True:
    ret, frame = video_capture.read()
    if not ret:
        break

    # Save the frame as an image
    frame_filename = f'/Users/shaum/space-sonification/carina_frames/frame_{frame_number:04d}.jpg'  # Adjust the filename format
    cv2.imwrite(frame_filename, frame)
    frame_number += 1
video_capture.release()

print(f"Frames extracted: {frame_number}")