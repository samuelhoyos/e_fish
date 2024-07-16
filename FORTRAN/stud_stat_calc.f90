program stud_stat_calc
    use ssc
    implicit none
!------------------------------DECLARATION------------------------------
!---------------------------------INPUT---------------------------------
!--------------------------ALL TIMES ARE IN[NS]-------------------------
    character(100) inputfile, studentfile, outputfile, filepath              !filenames of file with data input and output information
    integer header                                                          !# of lines to skip at header
    integer n_elements                                                      !# of lines with significant values
    integer n_student                                                       !# of lines with significant values for a t_student
    real*16 bin_width                                                       ![ns], width of a bin, 1st bin begins from first data point, each bin has a time coordinate in a middle of a bin
!---------------------------------OUTPUT--------------------------------
    real*16, allocatable                    ::  shg_singleshot(:,:)         !ORDERED FROM T_MIN TO T_MAX!!!
    real*16, allocatable                    ::  t_student(:,:)              !student's coefficients database for a selected probability (usually requested standart is 0.95=95%)
    real*16, allocatable                    ::  shg_binned(:,:)             !result of the work: 1st column for time [ns], 2nd for arithmetic average (further 'mean'), 3rd for absolute random error (furter 'error'), 4th for # of data points collected in a bin (further 'histogram')
    integer n_bins                                                          !# of bins
    character(len=1) :: separator
!---------------------------------INNER---------------------------------
    character(80) filename                                                  !
    integer i, j                                                            !counters
!-----------------------------INITIALIZATION----------------------------
    inputfile='/home/samuel/Documents/Internship/STAGE/e_fish/data/2024_05_16/input_pos2_45_SSC.dat'                                                   !directs to 'shg_singleshot.dat'with all single shot data for selected case
    studentfile='t_student.dat'                                             !gives the student coefficients for a chosen probability (usually requested standart is 0.95=95%)
    outputfile='/home/samuel/Documents/Internship/STAGE/e_fish/data/2024_05_16/output_pos2_45_SSC.dat'
!------------------------------DEALLOCATION-----------------------------
    if (allocated(shg_singleshot)) then
        deallocate(shg_singleshot)
    endif   
    if (allocated(t_student)) then
        deallocate(t_student)
    endif   
!---------------------------READING INPUT FILE1--------------------------- 
    open(20240516, file=inputfile)
    read(20240516, "(A)") filepath, filename
    read(20240516, *) header, n_elements
    read(20240516, *) bin_width
    print *, filepath, filename, header, n_elements, bin_width
    close(20240516)
!---------------------------READING INPUT FILE2--------------------------- 
    open(202405165, file=studentfile)
    !print *, "checkpoint"
    call file_reading (filepath, studentfile, 1, t_student, n_student)
    !print '(i6)', n_student
    ! do i=1, n_student
    !    print '(f6.0, f8.4)', t_student(i,1), t_student(i,2)
    ! enddo
    close(202405165)
!----------------------------ALLOCATION, ZEROING------------------------
    allocate(shg_singleshot(n_elements,2))  
    do i=1, n_elements
        shg_singleshot(i,1)=0.0
        shg_singleshot(i,2)=0.0
    enddo
    !print '(i6)', n_elements
    !do i=1, n_elements
    !    print '(f6.2, f6.2)', shg_singleshot(i,1), shg_singleshot(i,2)
    !enddo
!----------------------------FILE PREPARATION---------------------------
    open(202405160, file=outputfile)
    write(202405160,"(A)")'binns;mean;error;histogram'
!-----------------------------------------------------------------------
!--------------------------------MAIN-----------------------------------
!-----------------------------------------------------------------------
    
!----------------------------READING DATA-------------------------------
    !print *, "checkpoint"
    call file_reading (filepath, filename, header, shg_singleshot, n_elements)
    !do i=1, n_elements
    !    print '(e14.6, e14.6)', shg_singleshot(i,1), shg_singleshot(i,2)
    !enddo
!----------------------CREATING AND FILLING BINS------------------------
    call binner_sinner(t_student, n_student, shg_singleshot, n_elements, bin_width, shg_binned, n_bins)
    separator = ';'
    print *, n_bins
    do i=1, n_bins
        if (shg_binned(i,4) .NE. 0.0) then
            write(202405160, "(f6.2,a,e14.4,a,e14.4,a,i8)") shg_binned(i,1),trim(separator),shg_binned(i,2),trim(separator),&
            shg_binned(i,3),trim(separator),int(shg_binned(i,4))
        endif
    enddo
    
    close(202405160)
    
end program stud_stat_calc