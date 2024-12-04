import subprocess
import os
from pathlib import Path
import pandas as pd
import re
from . import signals
from concurrent.futures import ProcessPoolExecutor


folder = Path(__file__).parent.parent
input_folder = Path(__file__).parent.parent.parent / Path("data")
module = "shg.f90"
code = "second_harmonic_generation.f90"


def write_input(
    first_osc: int,
    last_osc: int,
    delta_t: float,
    t_diff: float,
    input_path: str,
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
    """
    Creates a configuration file with the necessary parameters for Inna's code,
    including paths and relevant simulation parameters.

    This function writes the configuration data to a specified file, including details
    such as the paths to input directories, the names of generators, and simulation
    parameters like time differences, background time, and trigger values.

    Parameters:
    -----------
    first_osc : int
        The number corresponding to the first oscillogram.
    last_osc : int
        The number corresponding to the last oscillogram.
    delta_t : float
        Full width at half maximum.
    t_diff : float
        The time difference between PMT and PD signals.
    input_path : str
        The relative path where the configuration file will be saved.
    pos_path : str
        The relative path to the folder containing the data for the point under consideration.
    bcs1_gen_name : str
        Base name for the first channel.
    bcs2_gen_name : str
        Base name for the files with the transmitted pulses.
    pd_gen_name : str
        Base name for the files to save PD signals.
    pmt_gen_name : str
        Base name for the files to save PMT signals.
    fmt : str, optional
        The file extension, default is ".txt".
    skip : int, optional
        Rows to skip, default is 5.
    n_elements : int, optional
        The total number of data points per oscillogram, default is 2002.
    t_bgd : float, optional
        The background time, default is 0.
    trigger : float, optional
        The trigger value for the oscilloscope, default is 0.15.

    Side Effects:
    -------------
    - Creates the output file specified by 'input_path'.
    """
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
    """
    Compiles and executes a FORTRAN code for second harmonic generation.

    Parameters:
    -----------
    path_folder : str
        Path to the folder containing the FORTRAN source files.

    Returns:
    --------
    None

    Side Effects:
    -------------
    - Compiles the FORTRAN code using 'gfortran'.
    - Executes the compiled program.
    - Prints the standard output or error message if the execution fails.

    Exceptions:
    -----------
    subprocess.CalledProcessError
        Raised if the compilation or execution fails.
    """
    compile_command = f"gfortran {str(folder/Path(path_folder))}\\{module} {str(folder/Path(path_folder))}\\{code} -o {str(folder/Path(path_folder))}\\second_harmonic_generation"
    subprocess.run(compile_command, shell=True, check=True)
    # Execute the compiled Fortran program
    execute_command = f"{str(folder/Path(path_folder))}\\second_harmonic_generation"

    try:
        result = subprocess.run(execute_command, shell=True, check=True)
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


def add_leading_zeros(channel: str, pos_path: str, total_length=5, fmt: str = ".txt"):
    """
    Renames files in a specified directory by adding leading zeros to the numerical part of the filenames.

    Parameters:
    -----------
    channel : str
        The prefix identifying the file channel (e.g., "C11").

    pos_path : str
        Relative path to the directory containing the files. The path is split to extract date and voltage information.

    total_length : int, optional
        Total number of digits for the numeric portion of the filename (default is 5).

    fmt : str, optional
        File format/extension to match, e.g., ".txt" (default is ".txt").

    Side Effects:
    -------------
    - Renames files within the specified directory by adding leading zeros to the numeric part.
    - Skips renaming if the target filename already exists.

    Notes:
    ------
    The directory path is derived from 'input_folder' combined with 'pos_path'.

    Exceptions:
    -----------
    Prints a message if the directory does not exist or if the filename already exists.
    """
    date_part = pos_path.split("\\")[0].replace("_", "")
    kv_part = pos_path.split("\\")[1].split("_")[1].split("k")[0]
    pattern = re.compile(
        rf"({channel}--{date_part}_Air150mbar_{kv_part}kV--)(\d+)({fmt})"
    )

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
                print(f"Renamed: {filename} -> {new_filename}")

    print(f"Leading zeros were added to files in {dir_path}")


def write_single_file(file_info):
    """
    Writes data to a single file, creating the necessary directories and adding a header text.

    Parameters:
    -----------
    file_info : tuple
        A tuple containing the following elements:
        - file_number : int.
        - group : pd.DataFrame
            A DataFrame containing the data to be written to the file, expected to have "time" and "amplitude" columns.
        - base_path : Path
            The base path where the file will be saved.
        - static_part1 : str
            A static string part of the filename, typically containing the channel.
        - static_part2 : str
            Another static string part of the filename, typically containing the voltage.
        - header_text : str
            The header text that will be written at the beginning of the file.

    Side Effects:
    -------------
    - Creates the target file and its parent directories if they do not exist.
    - Writes the header text and data to the file.
    - Appends the data (time and amplitude) from the group DataFrame to the file.

    Notes:
    ------
    - If the 'group' DataFrame is empty, a warning is printed and no data is written to the file.
    """

    file_number, group, base_path, static_part1, static_part2, header_text = file_info
    file_path = base_path / f"{static_part1}{static_part2}{file_number}.txt"

    file_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure directory exists

    with open(file_path, "w") as f:
        f.write(header_text + "\n")

    if group.empty:
        print(f"Warning: Data for file {file_path} is empty.")
    else:
        group[["time", "amplitude"]].to_csv(file_path, sep=";", index=False, mode="a") #append mode


def write_files(df: pd.DataFrame, channel: str, pos_path: str, fmt: str = ".txt"):
    """
    Writes multiple files based on the input DataFrame, using multiprocessing to speed up the file writing process.

    Parameters:
    -----------
    df : pd.DataFrame
        A DataFrame containing the data to be written to the files. The data is grouped by the "file_number" column.
    channel : str
        The channel identifier.
    pos_path : str
        The relative path where the files will be saved.
    fmt : str, optional
        The file extension for the output files, default is ".txt".

    Side Effects:
    -------------
    - Creates the necessary directories for saving the files.
    - Writes data for each file into separate files using multiprocessing.
    - Appends the 'time' and 'amplitude' columns from the DataFrame to the output files.
    - Calls the 'add_leading_zeros' function to standardize the filenames.

    Notes:
    ------
    - The header text mimics the format generated by an oscilloscope.
    - The file paths are constructed based on the 'channel', 'pos_path', and 'file_number'.
    """

    # Mimics the header generated by the oscilloscope
    header_text = "LECROYWR625Zi;61392;Waveform\nSegments;1;SegmentSize;2002\nSegment;TrigTime;TimeSinceSegment1\n#1date;0"

    pos_path_parts = pos_path.split("\\")
    base_path = Path(input_folder) / Path(pos_path)
    static_part1 = (
        f"{channel}--{int(''.join(pos_path_parts[0].split('_')))}_Air150mbar_"
    )
    static_part2 = f"{int(pos_path_parts[1].split('_')[1].split('k')[0])}kV--"

    # Prepare the data for multiprocessing
    file_groups = [
        (file_number, group, base_path, static_part1, static_part2, header_text)
        for file_number, group in df.groupby("file_number")
    ]

    with ProcessPoolExecutor() as executor:
        executor.map(write_single_file, file_groups)

    # Add leading zeros to the file names
    add_leading_zeros(pos_path=pos_path, channel=channel, fmt=fmt)
    print(f"Files written for channel {channel} at {base_path}")


def write_shg_for_ssc(path_to_read: str, path_to_write: str):
    """
    Extracts relevant information from the file generated by the SHG code from an input CSV file and writes the processed data to an output CSV file.

    Parameters:
    -----------
    path_to_read : str
        The relative path to the input CSV file containing SHG signal data.
    path_to_write : str
        The relative path where the processed CSV file will be saved.

    Side Effects:
    -------------
    - Reads data from the input CSV file.
    - Extracts the 'timens' and 'shg_single' columns and sorts them by 'timens'.
    - Drops the last row from the dataset.
    - Removes outliers from the 'shg_single' column using a custom outlier removal function.
    - Writes the processed data to the specified output file.

    Notes:
    ------
    - The function assumes the presence of an 'input_folder' variable that defines the base directory for reading and writing files.
    """

    path_to_read_file = input_folder / path_to_read
    path_to_write_file = input_folder / path_to_write

    df = pd.read_csv(f"{str(path_to_read_file)}", delimiter=";")
    df = df[["timens", "shg_single"]].sort_values("timens")
    df.drop(df.index[-1], inplace=True)
    df = signals.remove_outliers(df)
    df.to_csv(f"{str(path_to_write_file)}", sep=";", index=False)

    return print("E-FISH signal written for statistics")


def write_input_for_ssc(
    path: str,
    n_files: int,
    header: int = 1,
    bin_width: float = 0.2,
    path_to_data: str = "e_fish_signal.dat",
):
    """
    Writes the input data required for the SSC to a specified file.

    Parameters:
    -----------
    path : str
        The relative path where the input file will be saved.
    n_files : int
        The number of files to be included in the input file.
    header : int, optional
        Specifies number of lines constituting the header, default is 1.
    bin_width : float, optional
        The bin width to be written to the input file, default is 0.2 ns.
    path_to_data : str, optional
        The relative path to the data file, default is "e_fish_signal.dat".

    Side Effects:
    -------------
    - Creates and writes an input file at the specified 'path' with the necessary parameters for SSC.
    - Writes the directory path, data file path, header, number of elements, and bin width to the file.

    Notes:
    ------
    - The function assumes the presence of an 'input_folder' variable that defines the base directory for saving the input file.
    """
    path_to_input = input_folder / path

    with open(str(path_to_input), "w") as file:
        file.write(str(Path(path_to_input).parent) + "\\" "\n")
        file.write(path_to_data + "\n")
        file.write(str(header) + "\n")
        file.write(str(n_files) + "\n")
        file.write(str(bin_width) + "\n")
    return print("Input for SSC ready")


def compile_ssc(
    path_folder: str = "FORTRAN",
    module: str = "ssc.f90",
    code: str = "stud_stat_calc.f90",
):
    """
    Compiles and executes the Fortran code for the SSC (Student Statistic Code) calculation.

    Parameters:
    -----------
    path_folder : str, optional
        The folder containing the Fortran source files, default is "FORTRAN".
    module : str, optional
        The name of the Fortran module file to be compiled, default is "ssc.f90".
    code : str, optional
        The name of the Fortran code file to be compiled, default is "stud_stat_calc.f90".

    Side Effects:
    -------------
    - Compiles the Fortran source files ('module' and 'code') using the 'gfortran' compiler.
    - Executes the compiled Fortran program and captures its output.
    - Prints the standard output or error messages from the execution.

    Notes:
    ------
    - The function assumes that the 'folder' variable points to the directory containing the Fortran files.
    - Any errors during the compilation or execution will be printed along with the error details.
    """

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
