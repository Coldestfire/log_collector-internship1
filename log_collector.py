#DESCRIPTION:
#The following Python code reads a JSON config file that lists directories and the format of the log files it contains. It then prompts the user to enter start and end date/time and creates a zip archive that contains the matching files from all folders that were created between the specified date/time range

#REQUIRED LIBRARIES:
#- os
#- zipfile
#- json
#- datetime
#- glob

#CONSTRAINT:
#The script will exit if the output zip file size exceeds 1GB

import os
import zipfile
import json
from datetime import datetime
import glob

# Function to search for core dump files
def search_for_core_files(core_dirs):
    core_files = []
    for dir_name, file_specs in core_dirs.items():
        for file_spec in file_specs:
            if file_spec["filename"] == "core":
                path = file_spec["path"]
                files = glob.glob(os.path.join(path, "core.*"))
                if files:
                    core_files.extend(files)
    return core_files

# Function to get program name from core dump file
def get_program_name(core_dump_file):
    output = os.popen(f"file {core_dump_file}").read()
    program_name = output.split(", execfn: ")[1].split(", platform:")[0].replace("'", "")
    return program_name

# Function to run gdb command and save output to file
def run_gdb_command_and_save_output(program_name, core_dump_file):
    output_file = f"{core_dump_file}.log"
    command = f"gdb {program_name} {core_dump_file} -ex bt full -ex quit"
    output = os.popen(command).read()
    with open(output_file, "w") as f:
        f.write(output)

# Read config file
with open('config.json') as f:
    config = json.load(f)

# Collect start and end date/time from user
start_date = input("Enter start date (mm/dd/yyyy): ")
start_time = input("Enter start time (hh:mm): ")
end_date = input("Enter end date (mm/dd/yyyy): ")
end_time = input("Enter end time (hh:mm): ")

# Convert start and end date/time to datetime objects
start_datetime = datetime.strptime(start_date + ' ' + start_time, '%m/%d/%Y %H:%M')
end_datetime = datetime.strptime(end_date + ' ' + end_time, '%m/%d/%Y %H:%M')

# Create output zip file
zip_filename = f"aumtech.{start_datetime.strftime('%m%d%y')}hhmi.zip"
myzip = zipfile.ZipFile(zip_filename, 'w')

# Loop through directories in config file
for dir_name, dir_info in config['dirs'].items():
    # Loop through file formats in directory
    for file_info in dir_info:
        # Get list of matching files
        matching_files = glob.glob(os.path.join(file_info['path'], file_info['filename']))
        # Loop through matching files
        for file in matching_files:
            # Get file creation time
            file_ctime = datetime.fromtimestamp(os.path.getctime(file))
            # Check if file was created within specified date/time range
            if start_datetime <= file_ctime <= end_datetime:
                # Add file to output zip file
                myzip.write(file, os.path.basename(file))
                

        # Search for core dump files
        core_files = search_for_core_files(config["dirs"])

        # Process each core dump file
        for core_dump_file in core_files:

            # Get program name
            program_name = get_program_name(core_dump_file)

            # Run gdb command and save output
            run_gdb_command_and_save_output(program_name, core_dump_file)

            # Add output file to zip file
            output_file = f"{core_dump_file}.log"
            myzip.write(output_file, os.path.basename(output_file))
            os.remove(output_file)  # Remove the log file after it has been added to the zip file


# Create text file containing date range
text_filename = "date_range.txt"
with myzip.open(text_filename, 'w') as text_file:
    text_file.write(f"Files collected from {start_datetime} to {end_datetime}".encode())

    # Check if zip file size exceeds 1GB
    if os.path.getsize(zip_filename) > 1024*1024*1024:
        print("Zip file size exceeds 1GB, exiting...")
        os.remove(zip_filename)

# Close output zip file
myzip.close()

print("Logs Zipped Successfully")
