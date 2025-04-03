#!/usr/bin/env python3
# any2srt.py - Convert RTF, TXT, VTT, XML, and SBV caption files to SRT format

import sys
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime
import shutil

def convert_to_srt(input_file, output_file=None):
    """Convert various caption formats to SRT format"""
    if not os.path.isfile(input_file):
        print(f"Error: {input_file} not found")
        return False
    
    # Determine file type by extension
    _, ext = os.path.splitext(input_file)
    ext = ext.lower()
    
    # Set output file name if not provided
    if not output_file:
        output_file = os.path.splitext(input_file)[0] + '.srt'
    
    try:
        result = False
        
        # Special handling for TXT files with specific timestamp format
        if ext == '.txt':
            # First check if file has the special format with "0:00:01.000,0:00:07.160" timestamps
            # We'll use a more robust approach to handle special characters
            with open(input_file, 'rb') as f:
                content = f.read(1000)  # Read the first 1000 bytes
            
            try:
                # Try to decode the content to check for timestamp pattern
                content_str = content.decode('utf-8', errors='ignore')
                if re.search(r'\d+:\d+:\d+\.\d+,\d+:\d+:\d+\.\d+', content_str):
                    print(f"Detected special timestamp format in {input_file}, using special TXT converter...")
                    result = convert_special_txt_format(input_file, output_file)
                    if result and is_srt_valid(output_file):
                        print(f"Successfully converted {input_file} to {output_file}")
                        return True
            except:
                pass  # Ignore any decoding errors here, we'll try other methods
        
        # First attempt: try standard conversion based on file extension
        if ext == '.rtf':
            result = convert_rtf_to_srt(input_file, output_file)
        elif ext == '.txt':
            result = convert_txt_to_srt(input_file, output_file)
        elif ext == '.vtt':
            result = convert_vtt_to_srt(input_file, output_file)
        elif ext == '.xml':
            result = convert_xml_to_srt(input_file, output_file)
        elif ext == '.sbv':
            result = convert_sbv_to_srt(input_file, output_file)
        elif ext == '.srt':
            # Just copy the file
            shutil.copy2(input_file, output_file)
            result = True
        else:
            print(f"Error: Unsupported file format '{ext}'")
            return False
        
        # Validate the result
        if result and is_srt_valid(output_file):
            print(f"Successfully converted {input_file} to {output_file}")
            return True
        
        # Second attempt: if first conversion failed, try with special TXT converter 
        # for files with specific timestamp format
        if ext == '.txt' and (not result or not is_srt_valid(output_file)):
            try:
                print(f"Trying special TXT format converter...")
                result = convert_special_txt_format(input_file, output_file)
                if result and is_srt_valid(output_file):
                    print(f"Successfully converted {input_file} using special TXT format converter")
                    return True
            except Exception as e:
                print(f"Error with special TXT format converter: {str(e)}")
        
        # Third attempt: try with other converters as fallback
        if not result or not is_srt_valid(output_file):
            print(f"Standard conversion failed for {input_file}, trying alternative methods...")
            
            # Try all converters in sequence until one succeeds
            converters = [
                ('TXT converter', convert_txt_to_srt),
                ('VTT converter', convert_vtt_to_srt),
                ('SBV converter', convert_sbv_to_srt),
                ('RTF converter', convert_rtf_to_srt)
            ]
            
            for converter_name, converter_func in converters:
                if converter_func.__name__ == f"convert_{ext[1:]}_to_srt":
                    continue  # Skip the converter we already tried
                
                try:
                    print(f"Trying {converter_name}...")
                    result = converter_func(input_file, output_file)
                    if result and is_srt_valid(output_file):
                        print(f"Successfully converted {input_file} using {converter_name}")
                        return True
                except Exception as e:
                    print(f"Error with {converter_name}: {str(e)}")
            
            # Last resort: try to parse as plain text for files with no clear format
            try:
                print("Trying direct text extraction...")
                with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
                
                if len(text) > 100:  # If there's substantial text
                    result = convert_long_text_to_srt(text, output_file)
                    if result and is_srt_valid(output_file):
                        print(f"Successfully converted {input_file} using plain text extraction")
                        return True
            except Exception as e:
                print(f"Error with plain text extraction: {str(e)}")
            
            print(f"All conversion methods failed for {input_file}")
            return False
            
        return result
    except Exception as e:
        print(f"Error converting {input_file}: {str(e)}")
        return False

def is_srt_valid(srt_file):
    """Check if SRT file is valid by verifying it has content and proper structure"""
    try:
        with open(srt_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read().strip()
            
            # Check if file is empty
            if not content:
                return False
            
            # Check if file has at least one subtitle entry (number, timestamp, text)
            lines = content.split('\n')
            if len(lines) < 3:
                return False
                
            # Basic check for SRT structure (should have numbers and timestamps)
            has_timestamp = False
            has_number = False
            
            for line in lines:
                if '-->' in line:
                    has_timestamp = True
                if re.match(r'^\d+$', line.strip()):
                    has_number = True
                if has_timestamp and has_number:
                    return True
            
            return False
    except Exception:
        return False

def convert_rtf_to_srt(input_file, output_file):
    """Convert RTF to SRT format"""
    # Read the RTF file content
    with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # More robust RTF stripping
    # Remove all RTF control sequences
    content = re.sub(r'\\[a-zA-Z0-9]+(-?[0-9]+)?[ ]?', ' ', content)
    
    # Remove RTF curly braces, header, and other control characters
    content = re.sub(r'\{\\rtf[^}]*\}', '', content)
    content = re.sub(r'\{[^}]*\}', '', content)
    content = re.sub(r'[\{\}]', '', content)
    content = re.sub(r'\\\n', '\n', content)
    content = re.sub(r'\\[a-z0-9\-*]+', '', content)
    
    # Replace Unicode escape sequences
    content = re.sub(r'\\u([0-9]+)\?', lambda m: chr(int(m.group(1))), content)
    
    # Remove special characters and normalize whitespace
    content = re.sub(r'\\\'[0-9a-f]{2}', '', content)
    content = re.sub(r'\s+', ' ', content)
    
    # Split into lines for processing
    lines = content.split('\\')
    cleaned_lines = []
    
    # Clean up the lines
    for line in lines:
        line = line.strip()
        if line and not line.startswith('\\') and not line.startswith('{') and not line.startswith('}'):
            # Detect and extract timestamp patterns
            for timestamp_format in [
                r'(\d+:\d+:\d+[,\.]\d+)\s*(?:-->|->|–>|-)\s*(\d+:\d+:\d+[,\.]\d+)', # Standard format
                r'(\d+:\d+:\d+)[^0-9:]*(\d+:\d+:\d+)',  # Simple time range
                r'(\d+:\d+:\d+\.\d+),(\d+:\d+:\d+\.\d+)'  # SBV format
            ]:
                timestamp_match = re.search(timestamp_format, line)
                if timestamp_match:
                    start_time = timestamp_match.group(1)
                    end_time = timestamp_match.group(2)
                    cleaned_lines.append(f"{start_time} --> {end_time}")
                    
                    # Extract the text after the timestamp
                    text = line[timestamp_match.end():].strip()
                    if text:
                        cleaned_lines.append(text)
                    break
            else:
                # No timestamp found, consider it as subtitle text
                cleaned_lines.append(line)
    
    # Join the cleaned lines and convert using text conversion
    cleaned_content = '\n'.join(cleaned_lines)
    
    # Write to a temporary file
    temp_file = output_file + '.temp.txt'
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(cleaned_content)
    
    # Use the TXT converter on the cleaned content
    result = convert_txt_to_srt(temp_file, output_file)
    
    # Remove the temporary file
    try:
        os.remove(temp_file)
    except:
        pass
    
    return result

def convert_txt_to_srt(input_file, output_file):
    """Convert TXT to SRT format"""
    with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    # Check if this is a single long line transcript with no timestamps
    if len(lines) == 1 and len(lines[0]) > 1000 and not re.search(r'\d+:\d+', lines[0]):
        return convert_long_text_to_srt(lines[0], output_file)
    
    srt_content = []
    counter = 1
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines
        if not line:
            i += 1
            continue
        
        # Check for various timestamp formats
        
        # Format 1: Standard SRT-like with arrow "00:00:00,344 --> 00:00:07,297"
        # Format 2: Using en-dash "00:00:00,344 –> 00:00:07,297"
        # Format 3: Using hyphen "00:00:00,344 - 00:00:07,297"
        timestamp_match = re.search(r'(\d+:?\d*:?\d*[,\.:]\d*)\s*(?:-->|->|–>|-)\s*(\d+:?\d*:?\d*[,\.:]\d*)', line)
        
        # Format 4: Start and end times separated by comma without spaces "0:00:01.000,0:00:07.160"
        if not timestamp_match:
            timestamp_match = re.search(r'^(\d+:?\d*:?\d*[,\.:]\d*)\s*,\s*(\d+:?\d*:?\d*[,\.:]\d*)$', line)
            
        # Format 5: Just start time "00:00:00" or "0:00:01.160"
        if not timestamp_match:
            timestamp_match = re.search(r'^(\d+:?\d*:?\d*[,\.:]*\d*)$', line)
            
            if timestamp_match:
                start_time = timestamp_match.group(1)
                # Set a default end time 5 seconds later if only start time is provided
                end_time = None
        else:
            start_time = timestamp_match.group(1)
            end_time = timestamp_match.group(2)
            
        # Format 6: With colon for milliseconds "00:00:00:00 - 00:00:14:22"
        if not timestamp_match:
            timestamp_match = re.search(r'(\d+:\d+:\d+:\d+)\s*(?:-->|->|–>|-)\s*(\d+:\d+:\d+:\d+)', line)
            if timestamp_match:
                start_time = timestamp_match.group(1)
                end_time = timestamp_match.group(2)
                # Convert colon milliseconds to comma format
                start_time = re.sub(r'(\d+:\d+:\d+):(\d+)', r'\1,\2', start_time)
                end_time = re.sub(r'(\d+:\d+:\d+):(\d+)', r'\1,\2', end_time)
        
        # Format 7: Simplified time format "0:01:"
        if not timestamp_match:
            timestamp_match = re.search(r'^(\d+:\d+):$', line)
            if timestamp_match:
                time_part = timestamp_match.group(1)
                # Expand to full timestamp format
                if time_part.count(':') == 1:
                    start_time = f"00:{time_part},000"
                end_time = None
        
        if timestamp_match:
            # Normalize timestamps to SRT format (HH:MM:SS,mmm)
            if start_time:
                start_time = normalize_timestamp(start_time)
                
                if end_time:
                    end_time = normalize_timestamp(end_time)
                else:
                    # If no end time provided, add 5 seconds to start time
                    time_parts = start_time.replace(',', ':').split(':')
                    if len(time_parts) >= 3:
                        hours = int(time_parts[0])
                        minutes = int(time_parts[1])
                        seconds = int(time_parts[2])
                        millis = int(time_parts[3]) if len(time_parts) > 3 else 0
                        
                        # Add 5 seconds
                        seconds += 5
                        if seconds >= 60:
                            minutes += seconds // 60
                            seconds %= 60
                            if minutes >= 60:
                                hours += minutes // 60
                                minutes %= 60
                                
                        end_time = f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"
                    else:
                        # If time format is too simple, just add 5 seconds to default end time
                        end_time = f"00:00:05,000"
                
                # Get the subtitle text
                subtitle_lines = []
                i += 1
                
                # Collect subtitle text until we encounter another timestamp or empty line
                timestamp_pattern = r'^\d+:?\d*:?\d*[,\.:]\d*(?:,|\s*(?:-->|->|–>|-))\s*\d+:?\d*:?\d*[,\.:]\d*$|^\d+:?\d*:?\d*[,\.:]*\d*$'
                while i < len(lines) and lines[i].strip() and not re.match(timestamp_pattern, lines[i].strip()):
                    subtitle_lines.append(lines[i].strip())
                    i += 1
                
                # If we don't have subtitle lines but the next line isn't a timestamp, it's probably the subtitle
                if not subtitle_lines and i < len(lines) and not re.match(timestamp_pattern, lines[i].strip()):
                    subtitle_lines.append(lines[i].strip())
                    i += 1
                
                if subtitle_lines:
                    srt_content.append(f"{counter}")
                    srt_content.append(f"{start_time} --> {end_time}")
                    srt_content.extend(subtitle_lines)
                    srt_content.append("")
                    counter += 1
            else:
                i += 1
        else:
            i += 1
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(srt_content))
    
    return True

def convert_long_text_to_srt(text, output_file):
    """Convert a single long text (like a transcript) to SRT format by breaking it into segments"""
    # Clean the text
    text = text.strip()
    
    # Split text into sentences or segments
    # We'll use common sentence terminators and speaking transition markers
    segments = []
    
    # First try to split by common speaker transition patterns
    speaker_transitions = re.split(r'\s*(?:[A-Z][a-z]+:|\[?[A-Z][a-z]+\]?:|\([A-Z][a-z]+\):)\s*', text)
    
    if len(speaker_transitions) > 3:  # If we found several speaker transitions
        segments = speaker_transitions
    else:
        # Otherwise split by sentence terminators
        sentence_splits = re.split(r'(?<=[.!?])\s+', text)
        
        # Group sentences into reasonable segments (4-5 sentences per segment)
        segment_size = 3  # Number of sentences per segment
        for i in range(0, len(sentence_splits), segment_size):
            segment = ' '.join(sentence_splits[i:i+segment_size])
            if segment:
                segments.append(segment)
    
    # Remove any empty segments
    segments = [s for s in segments if s.strip()]
    
    # Create SRT content with estimated timestamps
    # Assume an average speaking rate of 150 words per minute (2.5 words per second)
    srt_content = []
    counter = 1
    
    current_time_seconds = 0
    words_per_second = 2.5
    
    for segment in segments:
        words = len(segment.split())
        duration = max(2, words / words_per_second)  # At least 2 seconds per segment
        
        # Calculate timestamps
        start_time = format_timestamp(current_time_seconds)
        current_time_seconds += duration
        end_time = format_timestamp(current_time_seconds)
        
        # Add a small gap between segments
        current_time_seconds += 0.25
        
        # Add to SRT content
        srt_content.append(f"{counter}")
        srt_content.append(f"{start_time} --> {end_time}")
        
        # Split segment into multiple lines if it's too long (more than 42 characters per line)
        line_length = 42
        if len(segment) > line_length:
            words = segment.split()
            lines = []
            current_line = []
            
            for word in words:
                if sum(len(w) for w in current_line) + len(current_line) + len(word) <= line_length:
                    current_line.append(word)
                else:
                    lines.append(' '.join(current_line))
                    current_line = [word]
            
            if current_line:
                lines.append(' '.join(current_line))
            
            srt_content.extend(lines)
        else:
            srt_content.append(segment)
        
        srt_content.append("")
        counter += 1
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(srt_content))
    
    return True

def format_timestamp(seconds):
    """Format seconds as SRT timestamp (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def normalize_timestamp(timestamp):
    """Normalize various timestamp formats to SRT format (HH:MM:SS,mmm)"""
    # Replace period with comma for milliseconds
    timestamp = timestamp.replace('.', ',')
    
    # Count the number of time components
    parts = re.split(r'[:,]', timestamp)
    
    if len(parts) == 1:  # Just seconds
        seconds = int(parts[0])
        return f"00:00:{seconds:02d},000"
        
    elif len(parts) == 2:  # MM:SS or SS,mmm
        if ',' in timestamp:
            seconds, millis = parts
            return f"00:00:{int(seconds):02d},{millis.ljust(3, '0')[:3]}"
        else:
            minutes, seconds = parts
            return f"00:{int(minutes):02d}:{int(seconds):02d},000"
            
    elif len(parts) == 3:  # HH:MM:SS or MM:SS,mmm
        if ',' in timestamp:
            minutes, seconds, millis = parts
            return f"00:{int(minutes):02d}:{int(seconds):02d},{millis.ljust(3, '0')[:3]}"
        else:
            hours, minutes, seconds = parts
            return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d},000"
            
    elif len(parts) == 4:  # HH:MM:SS,mmm
        hours, minutes, seconds, millis = parts
        # Ensure proper formatting with leading zeros
        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d},{millis.ljust(3, '0')[:3]}"
    
    # If we can't parse it, return as is
    return timestamp

def convert_timestamp(timestamp):
    """Convert various timestamp formats to SRT format (HH:MM:SS,mmm)"""
    # Basic handling for HH:MM:SS format
    if re.match(r'\d+:\d+:\d+$', timestamp):
        return timestamp + ",000"
    return timestamp

def convert_vtt_to_srt(input_file, output_file):
    """Convert VTT to SRT format"""
    with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Remove WebVTT header
    content = re.sub(r'WEBVTT.*?(\r\n|\r|\n)(\r\n|\r|\n)', '', content)
    
    # Normalize different line ending styles
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    
    # VTT files can sometimes use comma instead of arrow (like txt files)
    if ',' in content and not '-->' in content:
        # Process like a TXT file with comma-separated timestamps
        lines = content.split('\n')
        return convert_txt_to_srt(input_file, output_file)
    
    # Convert timestamps in different formats
    
    # Format 1: Standard VTT format with hours: 00:00:00.000 --> 00:00:05.000
    content = re.sub(r'(\d+):(\d+):(\d+)\.(\d+)', r'\1:\2:\3,\4', content)
    
    # Format 2: VTT format without hours: 00:00.000 --> 00:05.000
    # Convert to standard SRT format with hours (00:00:00,000 --> 00:00:05,000)
    content = re.sub(r'(\d+):(\d+)\.(\d+)', r'00:\1:\2,\3', content)
    
    # Process content line by line
    lines = content.split('\n')
    srt_content = []
    counter = 1
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines or notes
        if not line or line.startswith("NOTE"):
            i += 1
            continue
        
        # Look for timestamp patterns (more flexible now)
        timestamp_match = re.search(r'(\d+:\d+:\d+,\d+)\s*-->\s*(\d+:\d+:\d+,\d+)', line)
        
        if timestamp_match:
            start_time = timestamp_match.group(1)
            end_time = timestamp_match.group(2)
            
            # Get subtitle text (could be multiple lines)
            subtitle_lines = []
            i += 1
            while i < len(lines) and lines[i].strip() and not re.search(r'\d+:\d+:\d+[,\.]\d+\s*-->', lines[i]):
                subtitle_lines.append(lines[i].strip())
                i += 1
            
            if subtitle_lines:
                srt_content.append(f"{counter}")
                srt_content.append(f"{start_time} --> {end_time}")
                srt_content.extend(subtitle_lines)
                srt_content.append("")
                counter += 1
        else:
            i += 1
    
    # If no valid captions were found, try alternative parsing approaches
    if counter == 1:
        # Try processing as a text file with different timestamp formats
        return convert_txt_to_srt(input_file, output_file)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(srt_content))
    
    return True

def convert_xml_to_srt(input_file, output_file):
    """Convert XML to SRT format"""
    try:
        tree = ET.parse(input_file)
        root = tree.getroot()
        
        # Try to handle different XML caption formats (TTML, DFXP, etc.)
        srt_content = []
        counter = 1
        
        # Look for common patterns in subtitle XML formats
        subtitles = root.findall('.//p') or root.findall('.//subtitle') or root.findall('.//text')
        
        for subtitle in subtitles:
            start_time = subtitle.get('begin') or subtitle.get('start')
            end_time = subtitle.get('end') or subtitle.get('dur')
            
            if start_time and end_time:
                # Convert time format if needed
                start_time = convert_xml_time(start_time)
                end_time = convert_xml_time(end_time)
                
                text = subtitle.text.strip() if subtitle.text else ""
                
                if text:
                    srt_content.append(f"{counter}")
                    srt_content.append(f"{start_time} --> {end_time}")
                    srt_content.append(f"{text}")
                    srt_content.append("")
                    counter += 1
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(srt_content))
        
        return True
    except ET.ParseError:
        print(f"Error: Unable to parse XML file {input_file}")
        return False

def convert_sbv_to_srt(input_file, output_file):
    """Convert SBV (YouTube's Simple SubRip format) to SRT format"""
    with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    srt_content = []
    counter = 1
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines
        if not line:
            i += 1
            continue
        
        # Look for timestamp pattern like "0:00:00.000,0:00:05.000"
        timestamp_match = re.search(r'(\d+:\d+:\d+\.\d+),(\d+:\d+:\d+\.\d+)', line)
        
        if timestamp_match:
            # Convert timestamps from HH:MM:SS.mmm to HH:MM:SS,mmm format
            start_time = timestamp_match.group(1).replace('.', ',')
            end_time = timestamp_match.group(2).replace('.', ',')
            
            # Ensure proper hour formatting (0:00:00 -> 00:00:00)
            if start_time.count(':') == 2 and start_time[1] == ':':
                start_time = '0' + start_time
            if end_time.count(':') == 2 and end_time[1] == ':':
                end_time = '0' + end_time
            
            # Get the subtitle text (could be multiple lines until next timestamp)
            subtitle_lines = []
            i += 1
            while i < len(lines) and lines[i].strip() and not re.search(r'\d+:\d+:\d+\.\d+,\d+:\d+:\d+\.\d+', lines[i]):
                subtitle_lines.append(lines[i].strip())
                i += 1
            
            if subtitle_lines:
                srt_content.append(f"{counter}")
                srt_content.append(f"{start_time} --> {end_time}")
                srt_content.extend(subtitle_lines)
                srt_content.append("")
                counter += 1
        else:
            i += 1
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(srt_content))
    
    return True

def convert_xml_time(timestamp):
    """Convert XML timestamp formats to SRT format (HH:MM:SS,mmm)"""
    # Handle common XML time formats
    
    # Format: HH:MM:SS.mmm or HH:MM:SS:mmm
    time_match = re.match(r'(\d+):(\d+):(\d+)[\.:](\d+)', timestamp)
    if time_match:
        hours, minutes, seconds, millis = time_match.groups()
        # Ensure milliseconds are 3 digits
        millis = millis.ljust(3, '0')[:3]
        return f"{hours}:{minutes}:{seconds},{millis}"
    
    # Format: MM:SS.mmm
    time_match = re.match(r'(\d+):(\d+)[\.:](\d+)', timestamp)
    if time_match:
        minutes, seconds, millis = time_match.groups()
        # Ensure milliseconds are 3 digits
        millis = millis.ljust(3, '0')[:3]
        return f"00:{minutes}:{seconds},{millis}"
    
    # Format: time in seconds (float)
    time_match = re.match(r'(\d+\.\d+)s?', timestamp)
    if time_match:
        total_seconds = float(time_match.group(1))
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        millis = int((total_seconds - int(total_seconds)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"
    
    return timestamp

def convert_special_txt_format(input_file, output_file):
    """
    Convert TXT files with a specific format where timestamps like "0:00:01.000,0:00:07.160" 
    are on their own lines followed by caption text.
    """
    # Read the file content, handling BOM and special characters
    with open(input_file, 'rb') as f:
        content = f.read()
    
    # Try to detect encoding
    encoding = 'utf-8'
    if content.startswith(b'\xef\xbb\xbf'):  # UTF-8 BOM
        encoding = 'utf-8-sig'
    elif content.startswith(b'\xff\xfe') or content.startswith(b'\xfe\xff'):  # UTF-16 BOM
        encoding = 'utf-16'
    
    # Decode the content with the detected encoding
    try:
        text = content.decode(encoding, errors='ignore')
    except UnicodeDecodeError:
        # Fallback to latin-1 which should handle any byte value
        text = content.decode('latin-1', errors='ignore')
    
    # Split into lines and process
    lines = text.splitlines()
    
    srt_content = []
    counter = 1
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines
        if not line:
            i += 1
            continue
        
        # Look for timestamp pattern like "0:00:01.000,0:00:07.160"
        # More flexible matching to handle special characters
        timestamp_match = re.search(r'(\d+:\d+:\d+\.\d+),(\d+:\d+:\d+\.\d+)', line)
        
        if timestamp_match:
            start_time = timestamp_match.group(1)
            end_time = timestamp_match.group(2)
            
            # Convert to SRT format (HH:MM:SS,mmm)
            start_time = start_time.replace('.', ',')
            end_time = end_time.replace('.', ',')
            
            # Ensure proper hour formatting (0:00:00 -> 00:00:00)
            if start_time.count(':') == 2 and start_time[0] == '0' and not start_time.startswith('00'):
                start_time = '0' + start_time
            if end_time.count(':') == 2 and end_time[0] == '0' and not end_time.startswith('00'):
                end_time = '0' + end_time
            
            # Get the subtitle text (collect until next timestamp or empty line)
            subtitle_lines = []
            i += 1
            while i < len(lines) and lines[i].strip() and not re.search(r'\d+:\d+:\d+\.\d+,\d+:\d+:\d+\.\d+', lines[i].strip()):
                subtitle_lines.append(lines[i].strip())
                i += 1
            
            if subtitle_lines:
                srt_content.append(f"{counter}")
                srt_content.append(f"{start_time} --> {end_time}")
                srt_content.extend(subtitle_lines)
                srt_content.append("")
                counter += 1
            else:
                i += 1
        else:
            i += 1
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(srt_content))
    
    return True

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python any2srt.py input_file [output_file]")
        return
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    convert_to_srt(input_file, output_file)

if __name__ == "__main__":
    main() 