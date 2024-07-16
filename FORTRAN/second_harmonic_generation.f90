program second_harmonic_generation
    use shg
    implicit none
!------------------------------DECLARATION------------------------------
!---------------------------------INPUT---------------------------------
    character(80) filebase_bcs1, filebase_bcs4, filebase_pd, filebase_pmt, fileformat   !usually C1, C4, C2 and C4 respectively
    integer osc_a, osc_z                                                    !1st and last oscillogrammes needed
    integer header                                                          !# of lines to skip at header
    integer n_elements                                                      !# of lines with significant values
    integer n_bcs1, n_bcs4, latest_plasma_mode, current_plasma_mode         !# in data array for triggering time for BCS1, same for BCS2, difference in # of time arrays btw inc and trans for the most retarded plasma mode, current plasma mode
    integer n_min, n_max                                                    !#s to scan PD signal: physical condition = to be between incedent and transmitted pulses
    real*16 t_bgd, delta_t, pmt_delay                                       ![s], first XX seconds of signal where there's only background, FWHM of photodiod and photomultiplier pulse, integration will pas on (t_max-delta_t;t_max+delta_t); time of delay btw pd and pmt
    real*16 timestep                                                        !timestep - difference between two closest input T points
    real*16 trigger                                                         ![a.u.], trigger level of BCS1 and BCS2 signals
    character(100) inputfile, outputfile, emissionfile, filepath, emissionpath             !filename of file with data input and output information, filepath for data and emission's file name (if needed), should be syncronised with latest plasma mode manually
!---------------------------------OUTPUT--------------------------------
    real*16, allocatable                    ::  signalwbgd(:,:)             !
    real*16, allocatable                    ::  signal(:,:)                 !
    real*16, allocatable                    ::  emission(:,:)               !
    real*16, dimension (:), allocatable     :: pd_integral   
    real*16, dimension (:), allocatable     :: pmt_integral
    real*16, dimension (:,:), allocatable   :: shg_singleshot
    real*16, dimension (:), allocatable     :: pd_maxima
    real*16, dimension (:), allocatable     :: pmt_maxima
    real*16, dimension (:), allocatable     :: pmt_noise_maxima
    real*16 integral                                                        !current value of integrated signal
    character(len=1) :: separator
!---------------------------------INNER---------------------------------
    integer i, j                                                            !counter
    integer filenumber, t_pd_max, t_pmt_max, t_pmt_noise_max                !
    character(80) filebase, filename
                                        !
!-----------------------------INITIALIZATION----------------------------
    inputfile='/home/samuel/Documents/Internship/STAGE/e_fish/data/2024_05_16/input_pos2_45.dat'
    outputfile='/home/samuel/Documents/Internship/STAGE/e_fish/data/2024_05_16/output_pos2_45.dat'
    emissionfile='AveragedEmissionSyncro.dat'
!------------------------------DEALLOCATION-----------------------------
    if (allocated(signalwbgd)) then 
        deallocate(signalwbgd)
    endif
    if (allocated(signal)) then
        deallocate(signal)
    endif
    if (allocated(emission)) then
        deallocate(emission)
    endif
    if (allocated(pd_integral)) then
        deallocate(pd_integral)
    endif
    if (allocated(pmt_integral)) then
        deallocate(pmt_integral)
    endif
    if (allocated(shg_singleshot)) then
        deallocate(shg_singleshot)
    endif
    if (allocated(pd_maxima)) then
        deallocate(pd_maxima)
    endif
    if (allocated(pmt_maxima)) then
        deallocate(pmt_maxima)
    endif
    if (allocated(pmt_noise_maxima)) then
        deallocate(pmt_noise_maxima)
    endif
!-----------------------------------READING-----------------------------
    open(20240516, file=inputfile)
    read(20240516, "(A)") filepath, filebase_bcs1, filebase_bcs4, filebase_pd, filebase_pmt, fileformat
    read(20240516, "(i8)") osc_a, osc_z, header, n_elements
    read(20240516, *) t_bgd, delta_t, pmt_delay, trigger
    close(20240516)
    ! print *, trim(filepath)
    ! print *, trim(filebase_bcs1)
    ! print *, trim(filebase_bcs4)
    ! print *, trim(filebase_pd)
    ! print *, trim(filebase_pmt)
    ! print *, trim(fileformat)
    ! print *, osc_a
    ! print *, osc_z
    ! print *, header
    ! print *,"n_elements=", n_elements
    ! print *, t_bgd
    ! print *, delta_t
    ! print *, pmt_delay
    ! print *,"trigger", trigger
    
!-----------------------------ALLOCATION, ZEROING-----------------------
    allocate(pd_integral(osc_z))
    allocate(pmt_integral(osc_z))
    allocate(shg_singleshot(osc_z,2))
    allocate(pd_maxima(osc_z))
    allocate(pmt_maxima(osc_z))
    allocate(pmt_noise_maxima(osc_z))
    do i=1, osc_z
        pd_integral(i)=0.0
        pmt_integral(i)=0.0
        shg_singleshot(i,1)=0.0
        shg_singleshot(i,2)=0.0
        pd_maxima(i)=0.0
        pmt_maxima(i)=0.0
        pmt_noise_maxima(i)=0.0
    enddo
!----------------------------FILE PREPARATION---------------------------
    open(202405160, file=outputfile)
    write(202405160,"(A)")'timens;noi(pmt);max(pmt);sqrt(pmt);max(pd);pd;shg_single;osc'
!-----------------------------------------------------------------------
!--------------------------------MAIN-----------------------------------
!-----------------------------------------------------------------------

!---------------------LATEST PLASMA MODE DEFINITION---------------------                                                                            !EXPERIMENTAL VERSION
    latest_plasma_mode=0                                                    !difference in # of time arrays btw inc and trans                       !EXPERIMENTAL VERSION
    n_min=n_elements                                                                                                                                !EXPERIMENTAL VERSION
    n_max=0                                                                                                                                    !EXPERIMENTAL VERSION
    do i=osc_a, osc_z                                                                                                                               !EXPERIMENTAL VERSION
        print *, 'osc#=', i                                                                                                                 !EXPERIMENTAL VERSION
        print *, 'C1'                                                      !arriving signal                                                        !EXPERIMENTAL VERSION
        call name_osc(i, filebase_bcs1, filename, fileformat)                                                                                  !EXPERIMENTAL VERSION
        call file_reading (filepath, filename, header, signalwbgd, n_elements)                                                                      !EXPERIMENTAL VERSION
        call offset_substraction (signalwbgd, n_elements, t_bgd, signal)                                                                            !EXPERIMENTAL VERSION
        n_bcs1=1                                                            !first elements in array                                                !EXPERIMENTAL VERSION
        do while (signal(n_bcs1,2) .LT. trigger)                                                                                                    !EXPERIMENTAL VERSION
            n_bcs1=n_bcs1+1                                                                                                                 !EXPERIMENTAL VERSION
        enddo                                                                                                                                       !EXPERIMENTAL VERSION
        n_min=min(n_bcs1, n_min)                                                                                                                    !EXPERIMENTAL VERSION
                                                                                                                                                    !EXPERIMENTAL VERSION
        print *, 'C4'                                                      !transmitted signal                                                     !EXPERIMENTAL VERSION
        call name_osc(i, filebase_bcs4, filename, fileformat)                                                                                       !EXPERIMENTAL VERSION
        call file_reading (filepath, filename, header, signalwbgd, n_elements) 
                                                                             !EXPERIMENTAL VERSION
        call offset_substraction (signalwbgd, n_elements, t_bgd, signal) 
                                                                        !EXPERIMENTAL VERSION
        n_bcs4=n_bcs1     
        print *, "n_bcs4", n_bcs4                                               !first elements in array                                                !EXPERIMENTAL VERSION
        do while (signal(n_bcs4,2) .LT. trigger)                                                                                                    !EXPERIMENTAL VERSION
            n_bcs4=n_bcs4+1  
            !print *, "n", n_bcs4                                                                                                                     !EXPERIMENTAL VERSION
        enddo    
                                                                                                                                            !EXPERIMENTAL VERSION
        n_max=max(n_bcs4, n_max)                                                                                                                    !EXPERIMENTAL VERSION
                                                                                                                                                    !EXPERIMENTAL VERSION
        latest_plasma_mode=max(latest_plasma_mode, (n_bcs4-n_bcs1))                                                                                 !EXPERIMENTAL VERSION
        print '(i8, i8, i8, i8, i8)', i, n_bcs4, n_bcs1, (n_bcs4-n_bcs1), latest_plasma_mode                                                       !EXPERIMENTAL VERSION
    enddo                                                                                                                                           !EXPERIMENTAL VERSION
    
    timestep=(signalwbgd(2,1)-signalwbgd(1,1))
    
!------------TIMING DEFINITION FOR AVERAGED EMISSION SIGNAL-------------
    !TO ADD TWO FILES - AVERAGED EMISSION AND CORRESPONDING BCS2 TO PERFORM A SYNCRONIZATION
    !means define the time shift for emission waveform so that I_tr for both latest plasma mode case and emission case are triggered at the same time
    !after that one should after each read of new data subtract the averaged emission waveform
    !open(20181123, file=emissionfile)
    !emissionpath='C:\Users\orel\Dropbox\SHG\Console1\'
    !call file_reading (emissionpath, emissionfile, 1, emission, n_elements)
    
    if (allocated(emission)) then 
        deallocate(emission)
    endif
    allocate(emission(n_elements,2))
    
    do i=1, n_elements
        emission(i,1)=signalwbgd(i,1)
        emission(i,2)=0.0
    enddo  
!------------------------SINGLE SHG CALCULATIONS------------------------
    do i=osc_a, osc_z
        print *, 'osc#=', i
!---------------------------PD CALCULATIONS-----------------------------
        print *, 'C2'
        call name_osc(i, filebase_pd, filename, fileformat)
        call file_reading (filepath, filename, header, signalwbgd, n_elements)
        call offset_substraction (signalwbgd, n_elements, t_bgd, signal)
        call maxima_search(signal, n_elements, n_min, n_max, t_pd_max)                                                                              !EXPERIMENTAL VERSION        
        call integration(signal, n_elements, t_pd_max-(int(delta_t/timestep)+1), t_pd_max+(int(delta_t/timestep)+1), integral)
        
        if ((signal(t_pd_max,2)>0.0) .AND. (integral>0.0)) then                                                      !pd is >0
!---------------------------PMT CALCULATIONS----------------------------
            pd_maxima(i)=signal(t_pd_max,2)
            pd_integral(i)=integral
            print *, 'C3'
            call name_osc(i, filebase_pmt, filename, fileformat)
            call file_reading (filepath, filename, header, signalwbgd, n_elements)
            call offset_substraction (signalwbgd, n_elements, t_bgd, signal)
            do j=1, n_elements
                signal(j,2)=signal(j,2)-emission(j,2)                                                                                                                                           !EMISSION SUBTRACTION, verrry manual thing, to be improved
            enddo
            t_pmt_max=t_pd_max+int(pmt_delay/timestep)+1
            call integration(signal, n_elements, t_pmt_max-(int(delta_t/timestep)+1), t_pmt_max+(int(delta_t/timestep)+1), integral)
            call maxima_search(signal, n_elements, t_pmt_max-2*(int(delta_t/timestep)+1), t_pmt_max-(int(delta_t/timestep)+1),&
            t_pmt_noise_max)     !EXPERIMENTAL VERSION: NOISE SEARCH
            pmt_maxima(i)=signal(t_pmt_max,2)
            pmt_noise_maxima(i)=signal(t_pmt_noise_max,2)
            pmt_integral(i)=integral
           
            if (pmt_maxima(i) .GT. 0.14) then                                                                                                       !SATURATED value - to define for each experiment! and indicate here a bit less, because it may flucrtuate a bit (we usually have around 0.15)
                call wigwam_correction(signal, n_elements, t_pmt_max, pmt_maxima(i), pmt_integral(i))
            endif
            
            if (pmt_maxima(i) .GT. pmt_noise_maxima(i)) then                                                                                        !EXPERIMENTAL VERSION: NOISE SEARCH
                if ((pmt_maxima(i)>0.0) .AND. (pmt_integral(i)>0.0)) then                                                                           !pmt is >0
                    print *, '--------------------PASSED osc=', i
                
!--------------------CURRENT PLASMA MODE CALCULATION--------------------                                                                            !EXPERIMENTAL VERSION
                    print *, 'C1'                                                      !arriving signal                                            !EXPERIMENTAL VERSION
                    call name_osc(i, filebase_bcs1, filename, fileformat)                                                                           !EXPERIMENTAL VERSION
                    call file_reading (filepath, filename, header, signalwbgd, n_elements)                                                          !EXPERIMENTAL VERSION
                    call offset_substraction (signalwbgd, n_elements, t_bgd, signal)                                                                !EXPERIMENTAL VERSION
                    n_bcs1=1                                                            !first elements in array                                    !EXPERIMENTAL VERSION
                    do while (signal(n_bcs1,2) .LT. trigger)                                                                                        !EXPERIMENTAL VERSION
                        n_bcs1=n_bcs1+1                                                                                                             !EXPERIMENTAL VERSION
                    enddo                                                                                                                           !EXPERIMENTAL VERSION
                    print *, 'C4'                                                      !transmitted signal                                         !EXPERIMENTAL VERSION
                    call name_osc(i, filebase_bcs4, filename, fileformat)                                                                           !EXPERIMENTAL VERSION
                    call file_reading (filepath, filename, header, signalwbgd, n_elements)                                                          !EXPERIMENTAL VERSION
                    call offset_substraction (signalwbgd, n_elements, t_bgd, signal)                                                                !EXPERIMENTAL VERSION
                    n_bcs4=n_bcs1                                                       !first elements in array                                    !EXPERIMENTAL VERSION
                    do while (signal(n_bcs4,2) .LT. trigger)                                                                                        !EXPERIMENTAL VERSION
                        n_bcs4=n_bcs4+1                                                                                                             !EXPERIMENTAL VERSION
                    enddo                                                                                                                           !EXPERIMENTAL VERSION
                    current_plasma_mode=n_bcs4-n_bcs1                                                                                               !EXPERIMENTAL VERSION
                    print '(i8, i8, i8)', i, current_plasma_mode, latest_plasma_mode                                                               !EXPERIMENTAL VERSION
!-----------------------------TIME ADJUSTMENT---------------------------                                                                            !EXPERIMENTAL VERSION
                    t_pd_max=t_pd_max+latest_plasma_mode-current_plasma_mode                                                                        !EXPERIMENTAL VERSION
                
!----------------------------SAVING SINGLESHOTS-------------------------
                    shg_singleshot(i,1)=signal(t_pd_max,1)*1e9                          !time in [ns]
                    shg_singleshot(i,2)=sqrt(pmt_integral(i))/pd_integral(i)
                    separator = ';'
                    write(202405160,'(f11.2,a,e11.4,a,e11.4,a,e11.4,a,e11.4,a,e11.4,a,e11.4,a,i6)') &
                    shg_singleshot(i,1),trim(separator),pmt_noise_maxima(i),trim(separator),pmt_maxima(i),trim(separator), &
                    sqrt(pmt_integral(i)),trim(separator),pd_maxima(i),trim(separator),pd_integral(i),trim(separator), &
                    shg_singleshot(i,2),trim(separator),i
                                
                endif
            endif
        endif
    enddo
    print *, "checkpoint"
    write(202405160, "(i8)") latest_plasma_mode

!---------------------------DEALLOCATION, CLOSURE-----------------------
    deallocate(signalwbgd)
    deallocate(signal)
    deallocate(pd_integral)  
    deallocate(pmt_integral)
    deallocate(shg_singleshot)
    deallocate(pd_maxima)
    deallocate(pmt_maxima)
    deallocate(pmt_noise_maxima)
    deallocate(emission)
    close(20240516)
    
end program second_harmonic_generation