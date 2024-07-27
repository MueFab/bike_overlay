import datetime
import matplotlib
matplotlib.use('Agg')  # Use the 'Agg' backend
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
from geopy.distance import distance
import os
import sys
import csv
import concurrent.futures

def parse_csv(file_path):
    points = []
    with open(file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            points.append({
                'latitude': float(row['latitude']),
                'longitude': float(row['longitude']),
                'elevation': float(row['elevation']),
                'time': datetime.datetime.fromisoformat(row['time']),
                'temperature': float(row['temperature']) if row['temperature'] else None,
                'heart_rate': int(row['heart_rate']) if row['heart_rate'] else None,
                'cadence': int(row['cadence']) if row['cadence'] else None,
                'speed': float(row['speed']),
                'total_distance': float(row['total_distance']),
                'total_ascent': float(row['total_ascent']),
                'total_descent': float(row['total_descent'])
            })
    return points

def interpolate_data(points, timestamp):
    before = after = None
    for i in range(len(points) - 1):
        if points[i]['time'] <= timestamp <= points[i + 1]['time']:
            before = points[i]
            after = points[i + 1]
            break
    if not before or not after:
        return None

    total_time = (after['time'] - before['time']).total_seconds()
    time_ratio = (timestamp - before['time']).total_seconds() / total_time

    interpolated_point = {
        'latitude': before['latitude'] + (after['latitude'] - before['latitude']) * time_ratio,
        'longitude': before['longitude'] + (after['longitude'] - before['longitude']) * time_ratio,
        'elevation': before['elevation'] + (after['elevation'] - before['elevation']) * time_ratio,
        'temperature': before['temperature'] + (after['temperature'] - before['temperature']) * time_ratio if before['temperature'] is not None and after['temperature'] is not None else None,
        'heart_rate': before['heart_rate'] + (after['heart_rate'] - before['heart_rate']) * time_ratio if before['heart_rate'] is not None and after['heart_rate'] is not None else None,
        'cadence': before['cadence'] + (after['cadence'] - before['cadence']) * time_ratio if before['cadence'] is not None and after['cadence'] is not None else None,
        'timestamp': timestamp,
        'speed': before['speed'] + (after['speed'] - before['speed']) * time_ratio,
        'total_distance': before['total_distance'] + (after['total_distance'] - before['total_distance']) * time_ratio,
        'total_ascent': before['total_ascent'] + (after['total_ascent'] - before['total_ascent']) * time_ratio,
        'total_descent': before['total_descent'] + (after['total_descent'] - before['total_descent']) * time_ratio
    }

    return interpolated_point

def create_map(route_points, current_point, width, height):
    fig, ax = plt.subplots(figsize=(width / 80, height / 80))
    fig.patch.set_facecolor((0, 0, 1))  # Set figure background to blue
    ax.set_facecolor((0, 0, 1))  # Set axis background to blue
    ax.axis('off')  # Ensure axis is turned off

    try:
        lats, lons = zip(*[(point['latitude'], point['longitude']) for point in route_points])
    except ValueError as e:
        print(f"Error unpacking route points: {e}")
        return None

    ax.plot(lons, lats, 'k-', linewidth=4)  # Black border
    ax.plot(lons, lats, 'w-', linewidth=2)  # White line
    ax.plot(current_point['longitude'], current_point['latitude'], 'ro')  # Current position

    ax.set_aspect('equal', adjustable='box')  # Ensure equal scaling

    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)  # Remove any margins
    fig.canvas.draw()

    # Save the plot to a PIL Image
    map_image = Image.frombuffer('RGBA', fig.canvas.get_width_height(), fig.canvas.buffer_rgba(), 'raw', 'RGBA', 0, 1)
    plt.close(fig)
    return map_image

def create_elevation_profile(route_points, current_point, width, height):
    fig, ax = plt.subplots(figsize=(width / 65, height / 65))
    fig.patch.set_facecolor((0, 0, 1))  # Set figure background to blue
    ax.set_facecolor((0, 0, 1))  # Set axis background to blue

    distances = [point['total_distance'] for point in route_points]
    elevations = [point['elevation'] for point in route_points]

    ax.plot(distances, elevations, 'k-', linewidth=4)  # Black border
    ax.plot(distances, elevations, 'w-', linewidth=2)  # White line

    ax.plot(current_point['total_distance'], current_point['elevation'], 'ro')  # Current elevation

    ax.axis('off')  # Remove x/y axis and labels
    fig.canvas.draw()

    # Save the plot to a PIL Image
    elevation_image = Image.frombuffer('RGBA', fig.canvas.get_width_height(), fig.canvas.buffer_rgba(), 'raw', 'RGBA', 0, 1)
    plt.close(fig)
    return elevation_image

def draw_text_with_border(draw, text, position, font, border_width, fill_color, border_color):
    x, y = position
    # Draw border
    for dx in range(-border_width, border_width + 1):
        for dy in range(-border_width, border_width + 1):
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), text, font=font, fill=border_color)
    # Draw fill
    draw.text(position, text, font=font, fill=fill_color)

def create_overlay_image(interpolated_point, map_image, elevation_image):
    # Create an empty image with blue background
    img = Image.new('RGB', (1920, 1080), color=(0, 0, 255))  # Blue background
    draw = ImageDraw.Draw(img)

    # Load a larger font using the default PIL font
    font_size = 20
    font = ImageFont.truetype("DejaVuSansMono-Bold.ttf", font_size)  # Monospace font

    # Format text with defaults for None values
    temperature_text = f"{interpolated_point['temperature']:.0f} °C" if interpolated_point['temperature'] is not None else "N/A"
    heart_rate_text = f"{interpolated_point['heart_rate']:.0f} bpm" if interpolated_point['heart_rate'] is not None else "N/A"
    cadence_text = f"{interpolated_point['cadence']:.0f} rpm" if interpolated_point['cadence'] is not None else "N/A"

    # Add text with the interpolated data
    text = (
        f"Date:  {interpolated_point['timestamp'].isoformat()[0:10]}\n"
        f"UTC:   {interpolated_point['timestamp'].isoformat()[11:19]}\n"
        f"Lat:   {interpolated_point['latitude']:.5f}\n"
        f"Long:  {interpolated_point['longitude']:.5f}\n"
        f"Elev:  {interpolated_point['elevation']:.0f} m\n"
        f"Temp:  {temperature_text}\n"
        f"HR:    {heart_rate_text}\n"
        f"Cad:   {cadence_text}\n"
        f"Speed: {interpolated_point['speed']:.1f} km/h\n"
        f"Dist:  {interpolated_point['total_distance']:.3f} km\n"
        f"Asc:   {interpolated_point['total_ascent']:.0f} m\n"
        f"Desc:  {interpolated_point['total_descent']:.0f} m"
    )
    text_position = (img.width - 250, 10)
    draw_text_with_border(draw, text, text_position, font, border_width=2, fill_color='white', border_color='black')

    # Add the map image and elevation profile image to the bottom right corner
    map_x = img.width - map_image.width
    map_y = img.height - map_image.height
    img.paste(map_image, (map_x, map_y))

    elevation_x = map_x - 70
    elevation_y = map_y - elevation_image.height + 10  # Reduce distance between plots
    img.paste(elevation_image, (elevation_x, elevation_y))

    return img

def create_video_overlay_image(points, timestamp_str):
    timestamp = datetime.datetime.fromisoformat(timestamp_str)
    interpolated_point = interpolate_data(points, timestamp)

    if not interpolated_point:
        raise ValueError("Timestamp is out of range of the GPS data.")

    map_image_width = 400  # Width in pixels (50% smaller)
    map_image_height = 200  # Height in pixels for the map (50% smaller)

    map_image = create_map(points, interpolated_point, map_image_width, map_image_height)
    elevation_image = create_elevation_profile(points, interpolated_point, map_image_width, map_image_height // 2)

    overlay_image = create_overlay_image(interpolated_point, map_image, elevation_image)

    return overlay_image

def generate_frame(points, timestamp_str, frame_dir):
    frame = create_video_overlay_image(points, timestamp_str)
    frame_path = os.path.join(frame_dir, f"frame_{timestamp_str}.png")
    frame.save(frame_path)
    return frame_path

def main():
    if len(sys.argv) != 4:
        print("Usage: generate_frames.py <gps_csv_file> <start_timestamp> <end_timestamp>")
        sys.exit(1)

    gps_csv_file = sys.argv[1]
    start_timestamp_str = sys.argv[2]
    end_timestamp_str = sys.argv[3]

    start_timestamp = datetime.datetime.fromisoformat(start_timestamp_str)
    end_timestamp = datetime.datetime.fromisoformat(end_timestamp_str)
    fps = 59.9401
    frame_interval = datetime.timedelta(seconds=1 / fps)
    current_timestamp = start_timestamp

    timestamps = []
    while current_timestamp <= end_timestamp:
        timestamps.append(current_timestamp.isoformat())
        current_timestamp += frame_interval

    frame_dir = 'frames'
    os.makedirs(frame_dir, exist_ok=True)

    points = parse_csv(gps_csv_file)

    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = [executor.submit(generate_frame, points, ts, frame_dir) for ts in timestamps]
        for future in concurrent.futures.as_completed(futures):
            try:
                frame_path = future.result()
                print(f'Generated frame: {frame_path}')
            except Exception as exc:
                print(f'Generated an exception: {exc}')

if __name__ == "__main__":
    main()
