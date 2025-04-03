#!/usr/bin/env python3
# batch_convert.py - Batch convert caption files to SRT format

import os
import sys
import shutil
from any2srt import convert_to_srt

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
            for line in lines:
                if '-->' in line:
                    has_timestamp = True
                    break
            
            return has_timestamp
    except Exception:
        return False

def batch_convert_captions(input_dir, success_dir, problem_dir):
    """Convert all caption files in input_dir to SRT format"""
    os.makedirs(success_dir, exist_ok=True)
    os.makedirs(problem_dir, exist_ok=True)
    
    supported_extensions = ['.rtf', '.txt', '.vtt', '.xml', '.sbv', '.srt']
    
    successful = 0
    problematic = 0
    skipped = 0
    
    for filename in os.listdir(input_dir):
        file_path = os.path.join(input_dir, filename)
        
        # Skip directories
        if os.path.isdir(file_path):
            continue
        
        # Skip hidden files
        if filename.startswith('.'):
            skipped += 1
            continue
        
        # Get file extension
        _, ext = os.path.splitext(filename)
        ext = ext.lower()
        
        # Skip unsupported file types
        if ext not in supported_extensions:
            print(f"Skipping unsupported file: {filename}")
            skipped += 1
            continue
        
        # If it's already an SRT file, just copy it to success directory
        if ext == '.srt':
            dest_path = os.path.join(success_dir, filename)
            shutil.copy2(file_path, dest_path)
            print(f"Copied SRT file: {filename}")
            successful += 1
            continue
        
        # For other file types, attempt conversion
        output_filename = os.path.splitext(filename)[0] + '.srt'
        output_path = os.path.join(success_dir, output_filename)
        
        try:
            print(f"Converting {filename}...")
            result = convert_to_srt(file_path, output_path)
            
            # Check if conversion was successful and SRT file is valid
            if result and is_srt_valid(output_path):
                print(f"Successfully converted: {filename} -> {output_filename}")
                successful += 1
            else:
                print(f"Conversion failed or produced empty file: {filename}")
                # Move the original file to the problem directory
                if os.path.exists(output_path):
                    os.remove(output_path)
                problem_file_path = os.path.join(problem_dir, filename)
                shutil.copy2(file_path, problem_file_path)
                problematic += 1
        except Exception as e:
            print(f"Error converting {filename}: {str(e)}")
            # Move the original file to the problem directory
            problem_file_path = os.path.join(problem_dir, filename)
            shutil.copy2(file_path, problem_file_path)
            problematic += 1
    
    return successful, problematic, skipped

def main():
    input_dir = 'caption_to_fix'
    success_dir = 'captions_fixed'
    problem_dir = 'captions_problematic'
    
    if not os.path.isdir(input_dir):
        print(f"Error: {input_dir} directory not found.")
        return
    
    print(f"Starting batch conversion from {input_dir}...")
    successful, problematic, skipped = batch_convert_captions(input_dir, success_dir, problem_dir)
    
    print("\nConversion Summary:")
    print(f"Successfully converted: {successful}")
    print(f"Problematic conversions: {problematic}")
    print(f"Skipped files: {skipped}")
    print(f"\nSuccessful conversions are in: {os.path.abspath(success_dir)}")
    print(f"Problematic files are in: {os.path.abspath(problem_dir)}")

if __name__ == "__main__":
    main() 