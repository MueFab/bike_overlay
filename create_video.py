import os
import sys

from moviepy.editor import ImageSequenceClip

def create_video(frame_dir, output_file, fps=60):
    frames = [os.path.join(frame_dir, frame) for frame in sorted(os.listdir(frame_dir)) if frame.endswith(".png")]

    clip = ImageSequenceClip(frames, fps=fps)
    clip.write_videofile(output_file, codec='libx264', threads=12)

    # Clean up frame files if needed
  #  for frame_path in frames:
  #      os.remove(frame_path)

def main():
    if len(sys.argv) != 3:
        print("Usage: create_video.py <frame_dir> <output_file>")
        sys.exit(1)

    frame_dir = sys.argv[1]
    output_file = sys.argv[2]

    create_video(frame_dir, output_file)

if __name__ == "__main__":
    main()
