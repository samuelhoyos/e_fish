import subprocess
import os
from pathlib import Path
import pandas as pd
import re
from sklearn.neighbors import LocalOutlierFactor
from . import signals
from concurrent.futures import ProcessPoolExecutor


folder = Path(__file__).parent.parent
input_folder = Path(__file__).parent.parent.parent /Path("data")
module = "shg.f90"
code = "second_harmonic_generation.f90"


def write_input(
    first_osc: int,
    last_osc: int,
    delta_t: float,
    t_diff: float,
    input_path: str ,
    pos_path: str,
    bcs1_gen_name: str,
    bcs2_gen_name: str,
    pd_gen_name: str,
    pmt_gen_name: str,
    fmt: str = ".txt",
    skip: int = 5,
    n_elements: int = 2002,
    t_bgd: float = 0,
    trigger: float = 0.15,
):
    with open(str(input_folder / Path(input_path)), "w") as file:
        file.write(str(input_folder / Path(pos_path)) + "\\" + "\n")
        file.write(bcs1_gen_name + "\n")
        file.write(bcs2_gen_name + "\n")
        file.write(pd_gen_name + "\n")
        file.write(pmt_gen_name + "\n")
        file.write(fmt + "\n")
        file.write(str(first_osc) + "\n")
        file.write(str(last_osc) + "\n")
        file.write(str(skip) + "\n")
        file.write(str(n_elements) + "\n")
        
        file.write(str(t_bgd) + "\n")
        file.write(str(delta_t) + "\n")
        file.write(str(t_diff) + "\n")
        file.write(str(trigger) + "\n")
    return print(f"Content written to {str(input_folder/Path(input_path))}")


def compile_shg(path_folder: str):
    compile_command = f"gfortran {str(folder/Path(path_folder))}\\{module} {str(folder/Path(path_folder))}\\{code} -o {str(folder/Path(path_folder))}\\second_harmonic_generation"
    subprocess.run(compile_command, shell=True, check=True)
    # Execute the compiled Fortran program
    execute_command = f"{str(folder/Path(path_folder))}\\second_harmonic_generation"

    try:
        result = subprocess.run(
            execute_command, shell=True, check=True
        )
        print("Standard Output:", result.stdout)
    except subprocess.CalledProcessError as e:
        print("Error occurred:")
        print("Return Code:", e.returncode)
        print("Standard Output:", e.stdout)
        print("Error Output:", e.stderr)
        result = subprocess.run(
            execute_command, shell=True, check=True, capture_output=True, text=True
        )
    return print("Standard Output:", result.stdout)




# def add_leading_zeros(channel: str, pos_path: str, total_length=5, fmt: str = ".txt"):
#     date_part = pos_path.split('/')[0].replace('_', '')
#     kv_part = pos_path.split('/')[1].split('_')[1].split('k')[0]
#     pattern = re.compile(rf"({channel}--{date_part}_Air150mbar_{kv_part}kV--)(\d+)({fmt})")
    
#     dir_path = input_folder / Path(pos_path)
    
#     if not dir_path.is_dir():
#         print(f"Directory does not exist: {dir_path}")
#         return
    
#     print(f"Processing directory: {dir_path}")

#     for filename in os.listdir(dir_path):
#         match = pattern.match(filename)
#         if match:
#             prefix = match.group(1)
#             number = match.group(2)
#             suffix = match.group(3)
#             zero_padded_number = number.zfill(total_length)
#             new_filename = f"{prefix}{zero_padded_number}{suffix}"
#             os.rename(dir_path / filename, dir_path / new_filename)
#             print(f'Renamed: {filename} -> {new_filename}')
    
#     print(f"Leading zeros were added to files in {dir_path}")

def add_leading_zeros(channel: str, pos_path: str, total_length=5, fmt: str = ".txt"):
    date_part = pos_path.split('\\')[0].replace('_', '')
    kv_part = pos_path.split('\\')[1].split('_')[1].split('k')[0]
    pattern = re.compile(rf"({channel}--{date_part}_Air150mbar_{kv_part}kV--)(\d+)({fmt})")
    
    dir_path = input_folder / Path(pos_path)
    
    if not dir_path.is_dir():
        print(f"Directory does not exist: {dir_path}")
        return
    
    print(f"Processing directory: {dir_path}")

    for filename in os.listdir(dir_path):
        match = pattern.match(filename)
        if match:
            prefix = match.group(1)
            number = match.group(2)
            suffix = match.group(3)
            zero_padded_number = number.zfill(total_length)
            new_filename = f"{prefix}{zero_padded_number}{suffix}"
            new_filepath = dir_path / new_filename

            # Check if the new filename already exists
            if new_filepath.exists():
                print(f"File {new_filename} already exists. Skipping renaming.")
            else:
                os.rename(dir_path / filename, new_filepath)
                print(f'Renamed: {filename} -> {new_filename}')
    
    print(f"Leading zeros were added to files in {dir_path}")

def write_single_file(file_info):
    file_number, group, base_path, static_part1, static_part2, header_text = file_info
    file_path = base_path / f"{static_part1}{static_part2}{file_number}.txt"

    file_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure directory exists

    with open(file_path, "w") as f:
        f.write(header_text + "\n")

    if group.empty:
        print(f"Warning: Data for file {file_path} is empty.")
    else:
        group[["time", "amplitude"]].to_csv(file_path, sep=";", index=False, mode="a")

def write_files(df: pd.DataFrame, channel: str, pos_path: str, fmt: str = ".txt"):
    header_text = "LECROYWR625Zi;61392;Waveform\nSegments;1;SegmentSize;2002\nSegment;TrigTime;TimeSinceSegment1\n#1date;0"

    pos_path_parts = pos_path.split('\\')
    base_path = Path(input_folder) / Path(pos_path)
    static_part1 = f"{channel}--{int(''.join(pos_path_parts[0].split('_')))}_Air150mbar_"
    static_part2 = f"{int(pos_path_parts[1].split('_')[1].split('k')[0])}kV--"

    # Prepare the data for multiprocessing
    file_groups = [(file_number, group, base_path, static_part1, static_part2, header_text)
                   for file_number, group in df.groupby("file_number")]

    with ProcessPoolExecutor() as executor:
        executor.map(write_single_file, file_groups)

    add_leading_zeros(pos_path=pos_path, channel=channel, fmt=fmt)
    print(f"Files written for channel {channel} at {base_path}")

# def write_files(df: pd.DataFrame, channel: str, pos_path: str, fmt: str = ".txt"):
#     """
#     Writes files based on the provided DataFrame and parameters.

#     Parameters:
#         df (pd.DataFrame): DataFrame containing the data to be written.
#         channel (str): Channel name for the output files.
#         pos_path (str): Path where the files will be saved.
#         fmt (str): File format (default: ".txt").
#     """
#     header_text = "LECROYWR625Zi;61392;Waveform\nSegments;1;SegmentSize;2002\nSegment;TrigTime;TimeSinceSegment1\n#1date;0"

#     # Ensure the output path exists
    

#     pos_path_parts = pos_path.split('/')
#     base_path = Path(input_folder) / Path(pos_path)
#     static_part1 = f"{channel}--{int(''.join(pos_path_parts[0].split('_')))}_Air150mbar_"
#     static_part2 = f"{int(pos_path_parts[1].split('_')[1].split('k')[0])}kV--"

#     # Prepare the data for multiprocessing, excluding files that already exist
#     file_groups = []
#     for file_number, group in df.groupby("file_number"):
#         output_filename = f"{static_part1}{static_part2}{file_number}{fmt}"
#         output_filepath = base_path / output_filename
        
#         if os.path.exists(output_filepath):
#             print(f"File already exists: {output_filepath}. Skipping file creation.")
#         else:
#             # Only add to file_groups if the file doesn't exist
#             file_groups.append((file_number, group, base_path, static_part1, static_part2, header_text))

#     # Proceed with writing files only for those that don't exist
#     if file_groups:
#         try:
#             with ProcessPoolExecutor() as executor:
#                 executor.map(write_single_file, file_groups)
#         except Exception as e:
#             print(f"An error occurred during file writing: {e}")
#             return

#         add_leading_zeros(pos_path=pos_path, channel=channel, fmt=fmt)
#         print(f"Files written for channel {channel} at {base_path}")
#     else:
#         print(f"No new files were created for channel {channel}.")


# def write_files(df: pd.DataFrame, channel: str, pos_path: str, fmt: str = ".txt"):
#     """
#     Writes files based on the provided DataFrame and parameters.

#     Parameters:
#         df (pd.DataFrame): DataFrame containing the data to be written.
#         channel (str): Channel name for the output files.
#         pos_path (str): Path where the files will be saved.
#         fmt (str): File format (default: ".txt").
#     """
#     header_text = "LECROYWR625Zi;61392;Waveform\nSegments;1;SegmentSize;2002\nSegment;TrigTime;TimeSinceSegment1\n#1date;0"

#     # Ensure the output path exists

#     pos_path_parts = pos_path.split('/')
#     base_path = Path(input_folder) / Path(pos_path)
#     static_part1 = f"{channel}--{int(''.join(pos_path_parts[0].split('_')))}_Air150mbar_"
#     static_part2 = f"{int(pos_path_parts[1].split('_')[1].split('k')[0])}kV--"

#     # Prepare the data for multiprocessing
#     file_groups = [(file_number, group, base_path, static_part1, static_part2, header_text)
#                    for file_number, group in df.groupby("file_number")]

#     # Check for existing files before writing
#     for file_number, group in df.groupby("file_number"):
#         output_filename = f"{static_part1}{static_part2}{file_number}{fmt}"
#         output_filepath = base_path / output_filename
        
#         if os.path.exists(output_filepath):
#             print(f"File already exists: {output_filepath}. Skipping file creation.")
#             continue

#     try:
#         with ProcessPoolExecutor() as executor:
#             executor.map(write_single_file, file_groups)
#     except Exception as e:
#         print(f"An error occurred during file writing: {e}")
#         return

#     add_leading_zeros(pos_path=pos_path, channel=channel, fmt=fmt)
#     print(f"Files written for channel {channel} at {base_path}")

# def write_single_file(file_number_group, base_path, static_part1, static_part2, header_text):
#     file_number, group = file_number_group
#     file_path = base_path / f"{static_part1}{static_part2}{file_number}.txt"
#     #print(f"Writing to: {file_path}")

#     file_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
    
#     with open(file_path, "w") as f:
#         f.write(header_text + "\n")
    
#     if group.empty:
#         print(f"Warning: Data for file {file_path} is empty.")
#     else:
#         group[["time", "amplitude"]].to_csv(file_path, sep=";", index=False, mode="a")
#         #print(f"File written: {file_path} with {len(group)} records.")

# def write_files(df: pd.DataFrame, channel: str, pos_path: str, fmt: str = ".txt"):
#     header_text = "LECROYWR625Zi;61392;Waveform\nSegments;1;SegmentSize;2002\nSegment;TrigTime;TimeSinceSegment1\n#1date;0"
    
#     pos_path_parts = pos_path.split('/')
#     base_path = input_folder / Path(pos_path)
#     static_part1 = f"{channel}--{int(''.join(pos_path_parts[0].split('_')))}_Air150mbar_"
#     static_part2 = f"{int(pos_path_parts[1].split('_')[1].split('k')[0])}kV--"
    
#     file_groups = list(df.groupby("file_number"))

#     with ProcessPoolExecutor() as executor:
#         futures = [executor.submit(write_single_file, file_group, base_path, static_part1, static_part2, header_text) for file_group in file_groups]
#         for future in futures:
#             future.result()  # Ensure any raised exceptions are propagated
    
#     add_leading_zeros(pos_path=pos_path, channel=channel, fmt=fmt)
#     print(f"Files written for channel {channel} at {base_path}")

# def add_leading_zeros(channel: str, pos_path: str, total_length=5, fmt: str = ".txt"):
#     # Extract the parts from pos_path
#     date_part = pos_path.split('/')[0].replace('_', '')
#     kv_part = pos_path.split('/')[1].split('_')[1].split('k')[0]
    
#     # Construct the regular expression pattern to match filenames
#     pattern = re.compile(rf"({channel}--{date_part}_Air150mbar_{kv_part}kV--)(\d+)({fmt})")
    
#     # Print pattern for debugging
  
#     # List all files in the directory
#     dir_path = input_folder / Path(pos_path)
  
    
#     # Ensure the directory exists
#     if not dir_path.is_dir():
#         print(f"Directory does not exist: {dir_path}")
#         return
    
#     for filename in os.listdir(dir_path):
#         match = pattern.match(filename)
#         if match:
#             prefix = match.group(1)
#             number = match.group(2)
#             suffix = match.group(3)

            
#             # Determine the number of leading zeros needed
#             zero_padded_number = number.zfill(total_length)

#             # Reconstruct the filename with leading zeros
#             new_filename = f"{prefix}{zero_padded_number}{suffix}"

#             # Rename the file
#             os.rename(dir_path / filename, dir_path / new_filename)
#             print(f'Renamed: {filename} -> {new_filename}')
        

#     return print(f"Leading zeros were added to files in {dir_path}")



# def write_files(
#     df: pd.DataFrame,
#     channel: str,
#     pos_path: str,
#     fmt: str = ".txt",
# ):
#     header_text = "LECROYWR625Zi;61392;Waveform \n Segments;1;SegmentSize;2002 \n Segment;TrigTime;TimeSinceSegment1 \n #1date;0"

#     for file_number, group in df.groupby("file_number"):
#         file_path = f"{str(input_folder)}/{pos_path}/{channel}--{int(''.join(pos_path.split('/')[0].split('_')))}_Air150mbar_{int(pos_path.split('/')[1].split('_')[1].split('k')[0])}kV--{file_number}.txt"


#         # Open the file in write mode and write the header text
#         with open(file_path, "w") as f:
#             f.write(header_text + "\n")

#         # Append the DataFrame content to the file
#         group[["time", "amplitude"]].reset_index(drop=True).to_csv(
#             file_path, sep=";", index=False, mode="a"  # Append mode
#         )
#     add_leading_zeros(pos_path=pos_path, channel=channel, fmt=fmt)
#     return print(
#         f"Files written for channel {channel} at {str(input_folder/Path(pos_path))}"
#     )
# def write_files(
#     df: pd.DataFrame,
#     channel: str,
#     pos_path: str,
#     fmt: str = ".txt",
# ):
#     #input_folder = Path("your_input_folder_path")  # Define your input folder path here
#     header_text = "LECROYWR625Zi;61392;Waveform\nSegments;1;SegmentSize;2002\nSegment;TrigTime;TimeSinceSegment1\n#1date;0"
    
#     pos_path_parts = pos_path.split('/')
#     base_path = f"{input_folder}/{pos_path}"
#     static_part1 = f"{channel}--{int(''.join(pos_path_parts[0].split('_')))}_Air150mbar_"
#     static_part2 = f"{int(pos_path_parts[1].split('_')[1].split('k')[0])}kV--"

#     def write_single_file(file_number_group):
#         file_number, group = file_number_group
#         file_path = f"{base_path}/{static_part1}{static_part2}{file_number}.txt"
#         file_path.parent.mkdir(parents=True, exist_ok=True) 
#         with open(file_path, "w") as f:
#             f.write(header_text + "\n")
#         group[["time", "amplitude"]].to_csv(
#             file_path, sep=";", index=False, mode="a"
#         )
    
#     # Use a ProcessPoolExecutor to parallelize file writing
#     with ProcessPoolExecutor() as executor:
#         executor.map(write_single_file, df.groupby("file_number"))

#     add_leading_zeros(pos_path=pos_path, channel=channel, fmt=fmt)
#     print(f"Files written for channel {channel} at {str(input_folder / Path(pos_path))}")



def write_shg_for_ssc(path_to_read: str, path_to_write: str):
    path_to_read_file = input_folder/ path_to_read
    path_to_write_file = input_folder / path_to_write

    df = pd.read_csv(f"{str(path_to_read_file)}", delimiter=";")
    df = df[["timens", "shg_single"]].sort_values("timens")
    df.drop(df.index[-1], inplace=True)
    df=signals.remove_outliers(df)
    df.to_csv(f"{str(path_to_write_file)}", sep=";", index=False)

    return print("E-FISH signal written for statistics")


def write_input_for_ssc(
    path: str, n_elements: int, header: int = 1, bin_width: float = 0.2, path_to_data:str="e_fish_signal.dat"
):
    path_to_input = input_folder / path

    with open(str(path_to_input), "w") as file:
        file.write(str(Path(path_to_input).parent) + "\\" "\n")
        file.write(path_to_data+ "\n")
        file.write(str(header) + "\n")
        file.write(str(n_elements) + "\n")
        file.write(str(bin_width) + "\n")
    return print("Input for SSC ready")


def compile_ssc(
    path_folder: str = "FORTRAN",
    module: str = "ssc.f90",
    code: str = "stud_stat_calc.f90",
):
    compile_command = f"gfortran {str(folder/Path(path_folder))}\\{module} {str(folder/Path(path_folder))}\\{code} -o {str(folder/Path(path_folder))}\\stud_stat_calc"
    subprocess.run(compile_command, shell=True, check=True)
    # Execute the compiled Fortran program
    execute_command = f"{str(folder/Path(path_folder))}\\stud_stat_calc"

    try:
        result = subprocess.run(
            execute_command, shell=True, check=True, capture_output=True, text=True
        )
        print("Standard Output:", result.stdout)
    except subprocess.CalledProcessError as e:
        print("Error occurred:")
        print("Return Code:", e.returncode)
        print("Standard Output:", e.stdout)
        print("Error Output:", e.stderr)
        result = subprocess.run(
            execute_command, shell=True, check=True, capture_output=True, text=True
        )
