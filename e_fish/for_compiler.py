import subprocess
import os
from pathlib import Path
import pandas as pd
import re
from sklearn.neighbors import LocalOutlierFactor
from . import signals

folder = Path(__file__).parent.parent
input_folder = Path(__file__).parent.parent / "data"
module = "shg.f90"
code = "second_harmonic_generation.f90"


def write_input(
    first_osc: int,
    last_osc: int,
    delta_t: float,
    t_diff: float,
    input_path: str = "2024_05_16/input_pos2_45.dat",
    pos_path: str = "2024_05_16/pos2_45kV",
    bcs1_gen_name: str = "C11--20240516_Air150mbar_45kV--",
    bcs2_gen_name: str = "C44--20240516_Air150mbar_45kV--",
    pd_gen_name: str = "C2--20240516_Air150mbar_45kV--",
    pmt_gen_name: str = "C33--20240516_Air150mbar_45kV--",
    fmt: str = ".txt",
    skip: int = 5,
    n_elements: int = 2002,
    t_bgd: float = 0,
    trigger: float = 0.15,
):
    with open(str(input_folder / Path(input_path)), "w") as file:
        file.write(str(input_folder / Path(pos_path)) + "/" + "\n")
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
    compile_command = f"gfortran {str(folder/Path(path_folder))}/{module} {str(folder/Path(path_folder))}/{code} -o {str(folder/Path(path_folder))}/second_harmonic_generation"
    subprocess.run(compile_command, shell=True, check=True)
    # Execute the compiled Fortran program
    execute_command = f"{str(folder/Path(path_folder))}/second_harmonic_generation"

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

    # Print the output of the Fortran program


def add_leading_zeros(
    channel: str,
    pos_path: str = "2024_05_16/pos2_45kV",
    total_length=5,
    fmt: str = ".txt",
):
    # Change to the target directory
    os.chdir(str(input_folder / Path(pos_path)))

    # Regular expression to match the filenames and capture the numeric part
    pattern = re.compile(rf"({channel}--20240516_Air150mbar_45kV--)(\d+)(\ {fmt})")

    # List all files in the directory
    for filename in os.listdir("."):
        match = pattern.match(filename)
        if match:
            prefix = match.group(1)
            number = match.group(2)
            suffix = match.group(3)

            # Determine the number of leading zeros needed
            zero_padded_number = number.zfill(total_length)

            # Reconstruct the filename with leading zeros
            new_filename = f"{prefix}{zero_padded_number}{suffix}"

            # Rename the file
            os.rename(filename, new_filename)
            # print(f'Renamed: {filename} -> {new_filename}')
    return print("Leading zeros were added")


def write_files(
    df: pd.DataFrame,
    channel: str,
    pos_path: str = "2024_05_16/pos2_45kV",
    fmt: str = ".txt",
):
    header_text = "LECROYWR625Zi;61392;Waveform \n Segments;1;SegmentSize;2002 \n Segment;TrigTime;TimeSinceSegment1 \n #1date;0"

    for file_number, group in df.groupby("file_number"):
        file_path = f"{str(input_folder)}/{pos_path}/{channel}--20240516_Air150mbar_45kV--{file_number}.txt"

        # Open the file in write mode and write the header text
        with open(file_path, "w") as f:
            f.write(header_text + "\n")

        # Append the DataFrame content to the file
        group[["time", "amplitude"]].reset_index(drop=True).to_csv(
            file_path, sep=";", index=False, mode="a"  # Append mode
        )
    add_leading_zeros(pos_path=pos_path, channel=channel, fmt=fmt)
    return print(
        f"Files written for channel {channel} at {str(input_folder/Path(pos_path))}"
    )


def write_shg_for_ssc(path_to_read: str, path_to_write: str):
    path_to_read_file = Path(__file__).parent.parent / path_to_read
    path_to_write_file = Path(__file__).parent.parent / path_to_write

    df = pd.read_csv(f"{str(path_to_read)}", delimiter=";")
    df = df[["timens", "shg_single"]].sort_values("timens")
    df.drop(df.index[-1], inplace=True)
    df=signals.remove_outliers(df)
    df.to_csv(f"{str(path_to_write)}", sep=";", index=False)

    return print("E-FISH signal written for statistics")


def write_input_for_ssc(
    path: str, n_elements: int, header: int = 1, bin_width: float = 0.2, path_to_data:str="e_fish_signal.dat"
):
    path_to_input = Path(__file__).parent.parent / path

    with open(str(path_to_input), "w") as file:
        file.write(str(Path(path_to_input).parent) + "/" "\n")
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
    compile_command = f"gfortran {str(folder/Path(path_folder))}/{module} {str(folder/Path(path_folder))}/{code} -o {str(folder/Path(path_folder))}/stud_stat_calc"
    subprocess.run(compile_command, shell=True, check=True)
    # Execute the compiled Fortran program
    execute_command = f"{str(folder/Path(path_folder))}/stud_stat_calc"

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
