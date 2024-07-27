import gpxpy
import gpxpy.gpx
import datetime
import csv
import sys
from geopy.distance import distance


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
                            cad = int(cad.text) if cad is not None else 0

                points.append({
                    'latitude': round(point.latitude, 6),
                    'longitude': round(point.longitude, 6),
                    'elevation': round(point.elevation, 0),
                    'time': point.time,
                    'temperature': temp,
                    'heart_rate': hr,
                    'cadence': cad
                })
    return points


def fill_gaps(points):
    filled_points = []
    for i in range(len(points) - 1):
        filled_points.append(points[i])
        time_diff = (points[i + 1]['time'] - points[i]['time']).total_seconds()
        if time_diff > 1:
            current_time = points[i]['time']
            while (points[i + 1]['time'] - current_time).total_seconds() > 1:
                current_time += datetime.timedelta(seconds=1)
                filled_points.append({
                    'latitude': points[i]['latitude'],
                    'longitude': points[i]['longitude'],
                    'elevation': points[i]['elevation'],
                    'time': current_time,
                    'temperature': int(interpolate(points[i]['temperature'], points[i + 1]['temperature'], current_time,
                                                   points[i]['time'], points[i + 1]['time'])),
                    'heart_rate': int(interpolate(points[i]['heart_rate'], points[i + 1]['heart_rate'], current_time,
                                                  points[i]['time'], points[i + 1]['time'])),
                    'cadence': 0,
                    'speed': 0
                })
    filled_points.append(points[-1])
    return filled_points


def interpolate(value1, value2, current_time, time1, time2):
    if value1 is None or value2 is None:
        return None
    time_ratio = (current_time - time1).total_seconds() / (time2 - time1).total_seconds()
    return value1 + (value2 - value1) * time_ratio


def calculate_speed_and_distance(points):
    total_distance = 0
    total_ascent = 0
    total_descent = 0
    for i in range(1, len(points)):
        time_diff = (points[i]['time'] - points[i - 1]['time']).total_seconds()
        elevation_diff = points[i]['elevation'] - points[i - 1]['elevation']

        if time_diff >= 3:
            points[i]['speed'] = 0
        else:
            dist = distance((points[i - 1]['latitude'], points[i - 1]['longitude']),
                            (points[i]['latitude'], points[i]['longitude'])).meters
            total_distance += dist
            points[i]['speed'] = round((dist / time_diff) * 3.6, 1)  # Convert to km/h

        if elevation_diff > 0:
            total_ascent += elevation_diff
        else:
            total_descent -= elevation_diff

        points[i]['total_distance'] = round(total_distance / 1000, 2)  # Convert to km
        points[i]['total_ascent'] = round(total_ascent, 2)
        points[i]['total_descent'] = round(total_descent, 2)

    points[0]['speed'] = 0  # Initial point speed
    points[0]['total_distance'] = 0
    points[0]['total_ascent'] = 0
    points[0]['total_descent'] = 0
    return points


def format_timestamp(dt):
    return dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

def save_to_csv(points, csv_file):
    with open(csv_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['time', 'latitude', 'longitude', 'elevation', 'temperature', 'heart_rate', 'cadence', 'speed',
                         'total_distance', 'total_ascent', 'total_descent'])
        for point in points:
            writer.writerow([
                format_timestamp(point['time']),
                point['latitude'],
                point['longitude'],
                point['elevation'],
                point['temperature'],
                point['heart_rate'],
                point['cadence'],
                point['speed'],
                point['total_distance'],
                point['total_ascent'],
                point['total_descent']
            ])


def main():
    if len(sys.argv) != 3:
        print("Usage: extract_gpx_data.py <gpx_file> <csv_file>")
        sys.exit(1)

    gpx_file = sys.argv[1]
    csv_file = sys.argv[2]

    points = parse_gpx(gpx_file)
    points = fill_gaps(points)
    points = calculate_speed_and_distance(points)
    save_to_csv(points, csv_file)


if __name__ == "__main__":
    main()
