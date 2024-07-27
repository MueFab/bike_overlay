import os
import cv2
import sys

def create_video(image_folder, video_name, fps):
    # Get all image files from the folder
    images = [img for img in os.listdir(image_folder) if img.endswith(".png")]
    images.sort()  # Ensure images are in the correct order

    # Read the first image to get the size
    frame = cv2.imread(os.path.join(image_folder, images[0]))
    height, width, layers = frame.shape

    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # You can use 'XVID' or other codecs
    video = cv2.VideoWriter(video_name, fourcc, fps, (width, height))

    for i, image in enumerate(images):
        print(f"Adding frame: {i + 1}/{len(images)}")
        img_path = os.path.join(image_folder, image)
        frame = cv2.imread(img_path)
        video.write(frame)

    # Release the video writer object
    video.release()

    # Delete the frame images from the disk
    for image in images:
        os.remove(os.path.join(image_folder, image))
    print("All frames have been deleted from the disk.")


def main():
    if len(sys.argv) != 3:
        print("Usage: create_video.py <frame_dir> <output_file>")
        sys.exit(1)

    frame_dir = sys.argv[1]
    output_file = sys.argv[2]

    create_video(frame_dir, output_file, 59.9401)

if __name__ == "__main__":
    main()
