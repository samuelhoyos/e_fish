from e_fish import for_compiler, load, time, transmitted, signals
from pathlib import Path
import pandas as pd

trigger_up = 0.15
trigger_down = -trigger_up
fortran_folder = "FORTRAN"
module_file = "shg.f90"
main_file = "second_harmonic_generation.f90"
executable_file = "second_harmonic_generation"
n_elements = 2002
data_path="2024_05_16\pos2_27kV\pos2_27kV"
date=data_path.split("\\")[0]
pos_volt=data_path.split("\\")[1].split("k")[0]
voltage=data_path.split("\\")[1].split("_")[1].split("k")[0]
joined_date="".join(date.split("_"))
if __name__ == "__main__":
    df_1 =load.get_df(channel="C1", folder=Path(data_path))
    df_2 =load.get_df(channel="C2", folder=Path(data_path))
    df_3 =load.get_df(channel="C3", folder=Path(data_path))
    # # # df_td = time.get_td_df(df_1)
    # # print("checkpoint")
    df_1 =load.avg_amplitude(df=df_1, window_size=10)
    df_time=time.calculate_df_time(df_1,trigger_up,trigger_down)
    print("checkpoint")
    df_shifted= time.shift_reflected_pulse(df_1,df_time)
    df_transmitted=transmitted.compute_pulse(df_1, df_shifted, df_time)
    print("checkpoint")
    df_discharge=transmitted.get_discharge_times(df_transmitted, trigger_up)
    df_2=df_2[df_2.file_number.isin(df_discharge.file_number)]
    df_2=signals.shift_laser_signal(df_2, df_discharge)
    # print("checkpoint")
    df_1['amplitude']=-df_1['avg_amplitude']
    df_3['amplitude']=-df_3['amplitude']
    df_3_max=signals.find_pmt_max(df_3)
    df_transmitted=transmitted.complete_signal(df_transmitted,n_elements=n_elements)
    df_transmitted.rename(columns={'transmitted':'amplitude'}, inplace=True)

    fwhm=time.calculate_int_interval(df_2)
    t_diff=time.calculate_pd_pmt_diff(df_3_max, df_2)

    for_compiler.write_files(df_1,channel="C11",pos_path=data_path)
    for_compiler.write_files(df_3,channel="C33",pos_path=data_path)
    for_compiler.write_files(df_transmitted,channel="C44",pos_path=data_path)

    first_osc=int(df_discharge.iloc[0].file_number)
    last_osc=int(df_discharge.iloc[-1].file_number)
    for_compiler.write_input(first_osc=first_osc,last_osc=last_osc,delta_t=fwhm,t_diff=t_diff,pos_path=data_path, input_path=f"{date}/input_{pos_volt}.dat", bcs1_gen_name=f"C11--{joined_date}_Air150mbar_{voltage}kV--",
                             bcs2_gen_name=f"C44--{joined_date}_Air150mbar_{voltage}kV--",pd_gen_name=f"C2--{joined_date}_Air150mbar_{voltage}kV--", pmt_gen_name=f"C33--{joined_date}_Air150mbar_{voltage}kV--")

    for_compiler.compile_shg("FORTRAN")

    for_compiler.write_shg_for_ssc(
        path_to_write=f"{date}/e_fish_signal.dat",
        path_to_read=f"{date}/output_{pos_volt}.dat",
    )
    n_elements = len(
        pd.read_csv(
            str(Path(__file__).parent.parent.parent / f"data/{date}/e_fish_signal.dat"),
            delimiter=";",
        )
    )
    for_compiler.write_input_for_ssc(
        path=f"{date}/input_{pos_volt}_SSC.dat", n_elements=n_elements, path_to_data="e_fish_signal.dat", bin_width=0.2
    )
    for_compiler.compile_ssc()
