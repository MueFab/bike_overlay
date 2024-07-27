# GPS Data Processing and Video Generation

This repository contains scripts for processing GPS data from GPX and TCX files, generating visual overlays for videos, and creating videos from image frames. The scripts are designed to work with GPS data, generate plots, and combine these into video overlays.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Scripts Overview](#scripts-overview)
- [Contributing](#contributing)
- [License](#license)

## Installation

To install the required dependencies, use the following command:

```bash
pip install -r requirements.txt
```

Ensure you have Python installed on your system. The required libraries are listed in the `requirements.txt` file.

## Usage

1. **GPX Data Extraction and Interpolation**

   Extract data from a GPX file, fill gaps in the data, and output to a CSV file.

   ```bash
   python extract_gpx_data.py <gpx_file> <output_csv_file>
   ```

2. **Replace GPX Data with TCX Data**

   Replace speed and distance data in a GPX CSV file with data from a TCX file. This is necessary to e.g. use
   Garmin speed and distance sensor data instead of GPS data.

   ```bash
   python replace_gpx_with_tcx.py <tcx_file> <gpx_csv_file> <output_csv_file>
   ```

3. **Generate Frames for Video Overlay**

   Create overlay images with GPS data and plots, suitable for video integration.

   ```bash
   python generate_frames.py <gps_csv_file> <start_timestamp> <end_timestamp>
   ```

4. **Create Video from Frames**

   Combine the generated image frames into a video. The resulting overlay video can be combined in any video editing software with the original video footage via chroma keying.

   ```bash
   python create_video.py <frame_dir> <output_video_file>
   ```

## Example Output

The following image shows an example output of the generated video overlay. The video overlay is created from the GPS data and a plot of the speed and altitude profile.

![Example Video Overlay](example.png)

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.