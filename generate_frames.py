import gpxpy
import gpxpy.gpx
import datetime
import matplotlib
matplotlib.use('Agg')  # Use the 'Agg' backend
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
from geopy.distance import distance
import concurrent.futures
import os
import sys


def parse_gpx(file_path):
    with open(file_path, 'r') as gpx_file:
        gpx = gpxpy.parse(gpx_file)
    points = []
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                temp = hr = cad = None
                if point.extensions:
                    for ext in point.extensions:
                        if 'TrackPointExtension' in ext.tag:
                            temp = ext.find('{http://www.garmin.com/xmlschemas/TrackPointExtension/v1}atemp')
                            hr = ext.find('{http://www.garmin.com/xmlschemas/TrackPointExtension/v1}hr')
                            cad = ext.find('{http://www.garmin.com/xmlschemas/TrackPointExtension/v1}cad')
                            temp = float(temp.text) if temp is not None else None
                            hr = int(hr.text) if hr is not None else None
                            cad = int(cad.text) if cad is not None else None

                points.append({
                    'latitude': point.latitude,
                    'longitude': point.longitude,
                    'elevation': point.elevation,
                    'time': point.time,
                    'temperature': temp,
                    'heart_rate': hr,
                    'cadence': cad
                })
    return points


def interpolate_data(points, timestamp):
    before = after = None
    index = 0
    for i in range(len(points) - 1):
        if points[i]['time'] <= timestamp <= points[i + 1]['time']:
            index = i
            before = points[i]
            after = points[i + 1]
            break
    if not before or not after:
        return None
    if after['time'] - before['time'] > datetime.timedelta(seconds=5):
        total_distance = 0
        for i in range(points.index(before) + 1):
            if i > 0:
                total_distance += distance((points[i - 1]['latitude'], points[i - 1]['longitude']),
                                           (points[i]['latitude'], points[i]['longitude'])).meters
        interpolated_point = {
            'latitude': before['latitude'],
            'longitude': before['longitude'],
            'elevation': before['elevation'],
            'temperature': before['temperature'],
            'heart_rate': before['heart_rate'],
            'cadence': before['cadence'],
            'timestamp': timestamp,  # Add the current timestamp
            'speed': 0,
            'total_distance': total_distance
        }
        return interpolated_point


    total_time = (after['time'] - before['time']).total_seconds()
    time_ratio = (timestamp - before['time']).total_seconds() / total_time

    interpolated_point = {
        'latitude': before['latitude'] + (after['latitude'] - before['latitude']) * time_ratio,
        'longitude': before['longitude'] + (after['longitude'] - before['longitude']) * time_ratio,
        'elevation': before['elevation'] + (after['elevation'] - before['elevation']) * time_ratio,
        'temperature': before['temperature'] + (after['temperature'] - before['temperature']) * time_ratio if before[
                                                                                                                  'temperature'] is not None and
                                                                                                              after[
                                                                                                                  'temperature'] is not None else None,
        'heart_rate': before['heart_rate'] + (after['heart_rate'] - before['heart_rate']) * time_ratio if before[
                                                                                                              'heart_rate'] is not None and
                                                                                                          after[
                                                                                                              'heart_rate'] is not None else None,
        'cadence': before['cadence'] + (after['cadence'] - before['cadence']) * time_ratio if before[
                                                                                                  'cadence'] is not None and
                                                                                              after[
                                                                                                  'cadence'] is not None else None,
        'timestamp': timestamp  # Add the current timestamp
    }

    # Calculate speed (m/s)
    distance_covered = distance((before['latitude'], before['longitude']),
                                (after['latitude'], after['longitude'])).meters * time_ratio

    distance_old = distance((points[index - 1]['latitude'], points[index - 1]['longitude']),
                                (before['latitude'], before['longitude'])).meters
    distance_new = distance((before['latitude'], before['longitude']),
                            (after['latitude'], after['longitude'])).meters
    speed_new = distance_new / total_time
    speed_old = distance_old / (before['time'] - points[index - 1]['time']).total_seconds()
    interpolated_point['speed'] = (speed_old + (speed_new - speed_old) * time_ratio) * 3.6

    # Calculate total distance so far
    total_distance = 0
    for i in range(points.index(before) + 1):
        if i > 0:
            total_distance += distance((points[i - 1]['latitude'], points[i - 1]['longitude']),
                                       (points[i]['latitude'], points[i]['longitude'])).meters
    total_distance += distance_covered
    interpolated_point['total_distance'] = total_distance

    return interpolated_point



def find_nearest_point(route_points, current_point):
    min_distance = float('inf')
    nearest_point_index = -1
    for i, point in enumerate(route_points):
        dist = distance((point['latitude'], point['longitude']),
                        (current_point['latitude'], current_point['longitude'])).meters
        if dist < min_distance:
            min_distance = dist
            nearest_point_index = i
    return nearest_point_index


def create_map(route_points, current_point, width, height):
    fig, ax = plt.subplots(figsize=(width / 80, height / 80))
    fig.patch.set_facecolor((0, 0, 1))  # Set figure background to green
    ax.set_facecolor((0, 0, 1))  # Set axis background to green
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
    fig.patch.set_facecolor((0, 0, 1))  # Set figure background to green
    ax.set_facecolor((0, 0, 1))  # Set axis background to green

    distances = [0]
    elevations = [route_points[0]['elevation']]

    for i in range(1, len(route_points)):
        prev_point = route_points[i - 1]
        curr_point = route_points[i]
        segment_distance = distance((prev_point['latitude'], prev_point['longitude']),
                                    (curr_point['latitude'], curr_point['longitude'])).meters
        distances.append(distances[-1] + segment_distance)
        elevations.append(curr_point['elevation'])

    ax.plot(distances, elevations, 'k-', linewidth=4)  # Black border
    ax.plot(distances, elevations, 'w-', linewidth=2)  # White line

    nearest_point_index = find_nearest_point(route_points, current_point)
    current_distance = distances[nearest_point_index]

    ax.plot(current_distance, current_point['elevation'], 'ro')  # Current elevation

    ax.axis('off')  # Remove x/y axis and labels
    fig.canvas.draw()

    # Save the plot to a PIL Image
    elevation_image = Image.frombuffer('RGBA', fig.canvas.get_width_height(), fig.canvas.buffer_rgba(), 'raw', 'RGBA',
                                       0, 1)
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
    # Create an empty image with green background
    img = Image.new('RGB', (1920, 1080), color=(0, 0, 255))  # Green background
    draw = ImageDraw.Draw(img)

    # Load a larger font using the default PIL font
    font_size = 20
    font = ImageFont.truetype("DejaVuSansMono-Bold.ttf", font_size)  # Monospace font

    # Format text with defaults for None values
    temperature_text = f"{interpolated_point['temperature']:.1f} °C" if interpolated_point['temperature'] is not None else "N/A"
    heart_rate_text = f"{interpolated_point['heart_rate']:.0f} bpm" if interpolated_point['heart_rate'] is not None else "N/A"
    cadence_text = f"{interpolated_point['cadence']:.0f} rpm" if interpolated_point['cadence'] is not None else "N/A"

    # Add text with the interpolated data
    text = (
        f"Lat:   {interpolated_point['latitude']:.6f}\n"
        f"Long:  {interpolated_point['longitude']:.6f}\n"
        f"Elev:  {interpolated_point['elevation']:.2f} m\n"
        f"Temp:  {temperature_text}\n"
        f"HR:    {heart_rate_text}\n"
        f"Cad:   {cadence_text}\n"
        f"Speed: {interpolated_point['speed']:.2f} km/h\n"
        f"Dist:  {interpolated_point['total_distance'] / 1000:.2f} km\n"
        f"Date:  {interpolated_point['timestamp'].isoformat()[0:10]}\n"
        f"UTC:   {interpolated_point['timestamp'].isoformat()[11:23]}"
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


def create_video_overlay_image(bike_route_file, gps_record_file, timestamp_str):
    route_points = parse_gpx(bike_route_file)
    gps_points = parse_gpx(gps_record_file)

    timestamp = datetime.datetime.fromisoformat(timestamp_str)
    interpolated_point = interpolate_data(gps_points, timestamp)

    if not interpolated_point:
        raise ValueError("Timestamp is out of range of the GPS data.")

    map_image_width = 400  # Width in pixels (50% smaller)
    map_image_height = 200  # Height in pixels for the map (50% smaller)

    map_image = create_map(route_points, interpolated_point, map_image_width, map_image_height)
    elevation_image = create_elevation_profile(route_points, interpolated_point, map_image_width, map_image_height // 2)

    overlay_image = create_overlay_image(interpolated_point, map_image, elevation_image)

    return overlay_image


def generate_frame(args):
    bike_route_file, gps_record_file, timestamp_str, frame_dir = args
    frame = create_video_overlay_image(bike_route_file, gps_record_file, timestamp_str)
    frame_path = os.path.join(frame_dir, f"frame_{timestamp_str}.png")
    frame.save(frame_path)
    return frame_path


def main():
    if len(sys.argv) != 6:
        print(
            "Usage: generate_frames.py <bike_route_file> <gps_record_file> <start_timestamp> <end_timestamp> <num_threads>")
        sys.exit(1)

    bike_route_file = sys.argv[1]
    gps_record_file = sys.argv[2]
    start_timestamp_str = sys.argv[3]
    end_timestamp_str = sys.argv[4]
    num_threads = int(sys.argv[5])

    start_timestamp = datetime.datetime.fromisoformat(start_timestamp_str)
    end_timestamp = datetime.datetime.fromisoformat(end_timestamp_str)
    fps = 60
    frame_interval = datetime.timedelta(seconds=1 / fps)
    current_timestamp = start_timestamp

    timestamps = []
    while current_timestamp <= end_timestamp:
        timestamps.append(current_timestamp.isoformat())
        current_timestamp += frame_interval

    frame_dir = 'frames'
    os.makedirs(frame_dir, exist_ok=True)

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        future_to_timestamp = {executor.submit(generate_frame, (bike_route_file, gps_record_file, ts, frame_dir)): ts
                               for ts in timestamps}
        for future in concurrent.futures.as_completed(future_to_timestamp):
            try:
                future.result()
            except Exception as exc:
                print(f'Generated an exception: {exc}')


if __name__ == "__main__":
    main()
