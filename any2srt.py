#!/usr/bin/env python3
# any2srt.py - Convert RTF, TXT, VTT, and XML caption files to SRT format

import sys
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime

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
        if ext == '.rtf':
            result = convert_rtf_to_srt(input_file, output_file)
        elif ext == '.txt':
            result = convert_txt_to_srt(input_file, output_file)
        elif ext == '.vtt':
            result = convert_vtt_to_srt(input_file, output_file)
        elif ext == '.xml':
            result = convert_xml_to_srt(input_file, output_file)
        else:
            print(f"Error: Unsupported file format '{ext}'")
            return False
        
        if result:
            print(f"Successfully converted {input_file} to {output_file}")
            return True
        return False
    except Exception as e:
        print(f"Error converting {input_file}: {str(e)}")
        return False

def convert_rtf_to_srt(input_file, output_file):
    """Convert RTF to SRT format"""
    # Simple approach: strip RTF formatting and try to extract timestamps and text
    with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Strip RTF control sequences (very basic approach)
    content = re.sub(r'\\[a-z0-9]+', ' ', content)
    content = re.sub(r'[{}]', '', content)
    
    # Try to find time codes and text in simple format
    # This is a simplified approach; real RTF parsing would be more complex
    lines = content.split('\n')
    srt_content = []
    counter = 1
    
    for i in range(0, len(lines), 2):
        if i + 1 < len(lines):
            # Assume first line is timestamp, second is text
            timestamp_match = re.search(r'(\d+:\d+:\d+).*?(\d+:\d+:\d+)', lines[i])
            if timestamp_match:
                start_time = timestamp_match.group(1)
                end_time = timestamp_match.group(2)
                
                # Convert time format if needed
                start_time = convert_timestamp(start_time)
                end_time = convert_timestamp(end_time)
                
                text = lines[i+1].strip()
                if text:
                    srt_content.append(f"{counter}")
                    srt_content.append(f"{start_time} --> {end_time}")
                    srt_content.append(f"{text}")
                    srt_content.append("")
                    counter += 1
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(srt_content))
    
    return True

def convert_txt_to_srt(input_file, output_file):
    """Convert TXT to SRT format"""
    with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    srt_content = []
    counter = 1
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        # Look for timestamp pattern like "00:00:00,000 --> 00:00:00,000"
        timestamp_match = re.search(r'(\d+:\d+:\d+[,\.]\d+)\s*-->\s*(\d+:\d+:\d+[,\.]\d+)', line)
        
        if timestamp_match:
            start_time = timestamp_match.group(1).replace('.', ',')
            end_time = timestamp_match.group(2).replace('.', ',')
            
            # Get the subtitle text (next line)
            if i + 1 < len(lines):
                subtitle_text = lines[i+1].strip()
                
                srt_content.append(f"{counter}")
                srt_content.append(f"{start_time} --> {end_time}")
                srt_content.append(f"{subtitle_text}")
                srt_content.append("")
                
                counter += 1
                i += 2  # Skip the next line since we've processed it
            else:
                i += 1
        else:
            i += 1
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(srt_content))
    
    return True

def convert_vtt_to_srt(input_file, output_file):
    """Convert VTT to SRT format"""
    with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Remove WebVTT header
    content = re.sub(r'WEBVTT.*?(\r\n|\r|\n)(\r\n|\r|\n)', '', content)
    
    # Convert timestamps from HH:MM:SS.mmm to HH:MM:SS,mmm format
    content = re.sub(r'(\d+):(\d+):(\d+)\.(\d+)', r'\1:\2:\3,\4', content)
    
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
        
        # Look for timestamp pattern
        timestamp_match = re.search(r'(\d+:\d+:\d+,\d+)\s*-->\s*(\d+:\d+:\d+,\d+)', line)
        
        if timestamp_match:
            start_time = timestamp_match.group(1)
            end_time = timestamp_match.group(2)
            
            # Get subtitle text (could be multiple lines)
            subtitle_lines = []
            i += 1
            while i < len(lines) and lines[i].strip() and not re.search(r'\d+:\d+:\d+,\d+\s*-->', lines[i]):
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

def convert_timestamp(timestamp):
    """Convert various timestamp formats to SRT format (HH:MM:SS,mmm)"""
    # Basic handling for HH:MM:SS format
    if re.match(r'\d+:\d+:\d+$', timestamp):
        return timestamp + ",000"
    return timestamp

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