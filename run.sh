#!/bin/bash

if [ "$#" -ne 5 ]; then
    echo "Usage: run_parallel.sh <bike_route_file> <gps_record_file> <start_timestamp> <end_timestamp> <n>"
    exit 1
fi

bike_route_file=$1
gps_record_file=$2
start_timestamp=$3
end_timestamp=$4
n=$5

# Set the timezone to UTC
export TZ=UTC

# Convert timestamps to milliseconds since epoch
start_milliseconds=$(date -d "$start_timestamp" +%s%3N)
end_milliseconds=$(date -d "$end_timestamp" +%s%3N)

# Calculate total duration and interval duration in milliseconds
total_duration=$((end_milliseconds - start_milliseconds))
interval_duration=$((total_duration / n))

# Generate frames in parallel
for i in $(seq 0 $((n - 1))); do
    interval_start_milliseconds=$((start_milliseconds + i * interval_duration))
    interval_end_milliseconds=$((interval_start_milliseconds + interval_duration))

    # Handle the last interval to ensure it ends at the exact end_timestamp
    if [ "$i" -eq "$((n - 1))" ]; then
        interval_end_milliseconds=$end_milliseconds
    fi

    interval_start_timestamp=$(date -u -d "@$(echo "scale=3; $interval_start_milliseconds / 1000" | bc)" +%Y-%m-%dT%H:%M:%S.%3NZ)
    interval_end_timestamp=$(date -u -d "@$(echo "scale=3; $interval_end_milliseconds / 1000" | bc)" +%Y-%m-%dT%H:%M:%S.%3NZ)

    echo "Running generate_frames.py for interval $((i + 1))/$n: $interval_start_timestamp to $interval_end_timestamp"
    python generate_frames.py "$bike_route_file" "$gps_record_file" "$interval_start_timestamp" "$interval_end_timestamp" 1 &
done

# Wait for all background processes to finish
wait

echo "All frame generation processes completed."

python ./create_video.py ./frames ./output.mp4

echo "finished"
