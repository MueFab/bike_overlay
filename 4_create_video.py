"""
Video Creation from Image Frames

This script creates a video from a sequence of image frames stored in a specified directory.
The resulting video is saved in the specified output file path. It also cleans up by deleting
the frame images after the video is created.

Usage:
    python create_video.py <frame_dir> <output_file>

Dependencies:
    - OpenCV (cv2)

Author: Fabian Müntefering
Date: 2024-07-27
"""

import os
import cv2
import sys


def create_video(image_folder, video_name, fps):
    """
    Creates a video from a sequence of images in a specified folder.

    Args:
        image_folder (str): The folder containing the image frames.
        video_name (str): The path to the output video file.
        fps (float): Frames per second for the video.

    Returns:
        None
    """
    # Get all image files from the folder
    images = [img for img in os.listdir(image_folder) if img.endswith(".png")]
    images.sort()  # Ensure images are in the correct order

    if not images:
        print("No images found in the specified folder.")
        return

    # Read the first image to get the size
    first_image_path = os.path.join(image_folder, images[0])
    frame = cv2.imread(first_image_path)
    if frame is None:
        print(f"Error reading the first image: {first_image_path}")
        return

    height, width, layers = frame.shape

    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # You can use 'XVID' or other codecs
    video = cv2.VideoWriter(video_name, fourcc, fps, (width, height))

    for i, image in enumerate(images):
        print(f"Adding frame: {i + 1}/{len(images)}")
        img_path = os.path.join(image_folder, image)
        frame = cv2.imread(img_path)
        if frame is not None:
            video.write(frame)
        else:
            print(f"Warning: Skipping frame {image}, as it could not be read.")

    # Release the video writer object
    video.release()
    print(f"Video has been created and saved as {video_name}.")

    # Optionally, delete the frame images from the disk
    for image in images:
        os.remove(os.path.join(image_folder, image))
    print("All frames have been deleted from the disk.")


def main():
    """
    Main function to run the video creation script.

    Expects two command-line arguments:
        - The directory containing the image frames.
        - The path to the output video file.
    """
    if len(sys.argv) != 3:
        print("Usage: create_video.py <frame_dir> <output_file>")
        sys.exit(1)

    frame_dir = sys.argv[1]
    output_file = sys.argv[2]

    create_video(frame_dir, output_file, 59.9401)


if __name__ == "__main__":
    main()
