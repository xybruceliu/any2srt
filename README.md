# any2srt

A simple Python utility to convert various caption formats to SRT (SubRip Text) format.

## Supported Formats

- RTF (Rich Text Format)
- TXT (Plain Text)
- VTT (Web Video Text Tracks)
- XML (Various XML-based caption formats)

## Usage

```bash
python any2srt.py input_file [output_file]
```

Where:
- `input_file` is the path to the caption file you want to convert
- `output_file` (optional) is the path where the converted SRT file will be saved. If not provided, the script will use the same name as the input file but with a .srt extension.

## Examples

```bash
# Convert a VTT file to SRT
python any2srt.py captions.vtt

# Convert a TXT file to SRT with a custom output filename
python any2srt.py captions.txt my_subtitles.srt
```

## Format Notes

- **RTF**: Basic RTF parsing (strips formatting codes and tries to extract timestamps and text)
- **TXT**: Expects timestamps in a format similar to SRT (00:00:00,000 --> 00:00:00,000)
- **VTT**: Full WebVTT format support with proper conversion of timing formats
- **XML**: Supports common XML-based subtitle formats by looking for subtitle elements and timing attributes

## Requirements

- Python 3.6 or higher
- No external dependencies required

## License

MIT
