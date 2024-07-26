# astro-video-sonification

Sonification for astronomical images yield fascinating results that can evoke the same wonder as the images themselves--this can be particularly useful for the visually impaired.

However, sonification has rarely been done for videos, which arguable have the potential for more. 

This approach first uses capture_video.py to convert video frames to a series of images, then, in sonify.py, uses OpenCV to detect objects lying on the circumference of a circle drawn on each frame. Bright, small objects are classified as stars and sonified by an Ocarina, while larger objects are sonified by a choir, adding an ambient effect whenever nebulous objects enter the frame. The notes played are part of the C wholetone scale. The pitch of a note triggered by an object is determined by its brightness while its volume is determined by its size. In the future I'd like to add color, but with the current infrastructure that would drastically reduce the efficiency and production time.
