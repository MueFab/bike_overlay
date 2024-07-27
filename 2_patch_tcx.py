import xml.etree.ElementTree as ET
import csv
import sys
from datetime import datetime, timedelta

def parse_tcx(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Define namespaces to search within the TCX file
    namespaces = {
        'tcx': 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2',
        'ns3': 'http://www.garmin.com/xmlschemas/ActivityExtension/v2'
    }

    points = []
    for trackpoint in root.findall('.//tcx:Trackpoint', namespaces):
        time_elem = trackpoint.find('tcx:Time', namespaces)
        distance_elem = trackpoint.find('tcx:DistanceMeters', namespaces)
        speed_elem = trackpoint.find('.//ns3:Speed', namespaces)

        time = datetime.fromisoformat(time_elem.text[:-1]) if time_elem is not None else None
        distance = float(distance_elem.text) if distance_elem is not None else None
        speed = float(speed_elem.text) if speed_elem is not None else None

        points.append({
            'time': time,
            'distance_meters': round(distance, 3),
            'speed': round(speed * 3.6, 1)
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
                current_time += timedelta(seconds=1)
                filled_points.append({
                    'time': current_time,
                    'distance_meters': points[i]['distance_meters'],
                    'speed': 0
                })
    filled_points.append(points[-1])
    return filled_points

def replace_gpx_with_tcx(gpx_csv, tcx_points, output_csv):
    # Read GPX CSV
    gpx_points = []
    with open(gpx_csv, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            gpx_points.append(row)

    # Create a dictionary for quick lookup of TCX points by timestamp
    tcx_dict = {point['time'].isoformat(timespec='milliseconds') + 'Z': point for point in tcx_points}

    # Replace speed and distance in GPX points with TCX values
    for gpx_point in gpx_points:
        timestamp = gpx_point['time']
        if timestamp in tcx_dict:
            gpx_point['speed'] = tcx_dict[timestamp]['speed']
            gpx_point['total_distance'] = round(tcx_dict[timestamp]['distance_meters'] / 1000, 3)

    # Save the updated GPX points to a new CSV
    with open(output_csv, 'w', newline='') as file:
        fieldnames = gpx_points[0].keys()
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for point in gpx_points:
            writer.writerow(point)

def main():
    if len(sys.argv) != 4:
        print("Usage: replace_gpx_with_tcx.py <tcx_file> <gpx_csv_file> <output_csv_file>")
        sys.exit(1)

    tcx_file = sys.argv[1]
    gpx_csv_file = sys.argv[2]
    output_csv_file = sys.argv[3]

    tcx_points = parse_tcx(tcx_file)
    tcx_points = fill_gaps(tcx_points)
    replace_gpx_with_tcx(gpx_csv_file, tcx_points, output_csv_file)

if __name__ == "__main__":
    main()
