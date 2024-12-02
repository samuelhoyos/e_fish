module shg
    contains 

subroutine name_osc(filenumber, filebase, filename, fileformat)
!---------------------------------DESCRIPTION---------------------------
! takes an oscillogramme # from list's variable line
! returns full oscillogramme name using the channel number, precised inside of subroutine
! example: input "20" output "C2_00020.txt"
!---------------------------------INPUT---------------------------------
    integer, intent(in)         ::  filenumber                  !number ##### of the oscillogramme: Ci_#####.txt
    character(80), intent(in)   ::  filebase, fileformat        !typical name Ci_##### and format of the file, usually .txt or .trc.txt
!---------------------------------OUTPUT--------------------------------
    character(80), intent(inout)::  filename                    !name of desired oscillogramme    
!---------------------------------INNER---------------------------------
    integer j, c, c1                                            !helping variables

    filename=filebase
    !print *, filename
    !print *, len_trim(filename)
    l=len_trim(filename)
    do j=0,4
        c=filenumber/10**j
        c1=mod(c, 10)
        filename((l-j+5):(l-j+5) )=achar((iachar("0")+c1))
        !print *, filename
    enddo
    filename((len_trim(filename)+1):(len_trim(filename)+len_trim(fileformat)))=fileformat                       !modify to .trc.txt for Binary2ASCII and to .txt to ASCII
    !print *, filename
    
end subroutine name_osc

subroutine file_reading (filepath, filename, header, signalwbgd, n_elements)
!---------------------------------DESCRIPTION---------------------------
! takes the filename, skips #=header of strings from the header (descriptive part of file, not data)
! returns measured signalwbgd of n_elements points
!---------------------------------INPUT---------------------------------
    character(80), intent(in)   ::  filename                    !contains #=header supportive lines and signalwbgd
    character(111), intent(in)   ::  filepath                    !line of file with path information
    integer, intent(in)         ::  header                      !number of lines with non-digital data
!---------------------------------OUTPUT--------------------------------
    real*16, allocatable        ::  signalwbgd(:,:)             !array: 1st column for time, 2nd for data values
    integer, intent(inout)      ::  n_elements                  !number of lines with digital data == lenght of the output massive; changes in cours of programm
!---------------------------------INNER---------------------------------
    integer i                                                   !counter
    
    n_elements=0
    !print *, "file_for_reading:", trim(filepath)//trim(filename)
    open(1, file=trim(filepath)//trim(filename))
    
    do while (.true.)
        read(unit=1, fmt="(A)", iostat=io_status) line
        if (io_status /= 0) exit
        n_elements = n_elements + 1  ! total # of lines
    end do   
    rewind(1)                                                   !goes to the head of file again
    
    n_elements=n_elements-header                                !# of digital data lines
    if (allocated(signalwbgd)) then
            deallocate(signalwbgd)
    endif
    allocate(signalwbgd(n_elements, 2))
    do i=1, header
        read(1, "(A)") line                                  !skipping #=header lines
    enddo       
    do i=1, n_elements
        read(1, *) signalwbgd(i, 1), signalwbgd(i, 2)           !writing all the lines after skipped ones: time and amplitude
    enddo

    
    close(1)
       
end subroutine file_reading

subroutine offset_substraction (signalwbgd, n_elements, t_bgd, signal)
!---------------------------------DESCRIPTION---------------------------
! takes measured signal of n_elements points and t_bgd since when signal is considered present
! returns signal without offset and/or bgd noise
!---------------------------------INPUT---------------------------------
    real*16, intent(in)         ::  signalwbgd(n_elements, 2)   !first column - time, second - data; contains offset and/or bgd noise   
    integer, intent(in)         ::  n_elements                  !#of points in input array
    real*16, intent(in)         ::  t_bgd                       !ending time position of bgd signal; beginning is considered as the 1st point in data input
!---------------------------------OUTPUT--------------------------------
    real*16, allocatable        ::  signal(:,:)                 !array: 1st column for time, 2nd for data values
!---------------------------------INNER---------------------------------
    real*16 summ, timestep                                      !summ - average bgd field variable, timestep - difference between two closest input T points
    integer i , n_bgd                                           !i - counter, n_bgd - final number for bgd elements
    
    if (allocated(signal)) then
            deallocate(signal)
    endif
    allocate(signal(n_elements, 2))
    
    timestep=(signalwbgd(2,1)-signalwbgd(1,1))
    !n_bgd=int((t_bgd-signalwbgd(1,1))/timestep)+1
    n_bgd=int(t_bgd/timestep)+1
    summ=0.0
    do i=1, n_bgd                                               !summing
        summ=summ+signalwbgd(i,2)
    enddo
    summ=summ/(n_bgd)

    do i=1, n_elements
        signal(i,1)=signalwbgd(i,1)                             !time line finning
        signal(i,2)=signalwbgd(i,2)-summ                        !noise substraction
    enddo
       
end subroutine offset_substraction

subroutine maxima_search(signal, n_elements, n_initial, n_final, t_max)
!---------------------------------DESCRIPTION---------------------------
! takes a signal of n_elements, searches a local maxima in range of n_initial, n_final
! returns maxima's position
!---------------------------------INPUT---------------------------------
    real*16, intent(in)         ::  signal(n_elements, 2)           !first column - time, second - data
    integer, intent(in)         ::  n_elements, n_initial, n_final  !#of points in input array, boundaries of maxima search
!---------------------------------OUTPUT--------------------------------
    integer, intent(inout)      ::  t_max                           !index of a line with max signal
!---------------------------------INNER---------------------------------
    integer i                                                       !counter
    
    t_max=max(1, n_initial)                                         !!!PROTECTION FROM FOOL!!!
    do i=max(1, n_initial)+1, min(n_elements, n_final)              !!!PROTECTION FROM FOOL!!!
        if (signal(i,2)>signal(t_max,2)) then
            t_max=i
        endif
    enddo 
    
end subroutine maxima_search

subroutine integration(signal, n_elements, n_initial, n_final, integral)
!---------------------------------DESCRIPTION---------------------------
! takes a signal of n_elements and boundaries of integraton n_initial and n_final
! returns integral
!---------------------------------INPUT---------------------------------
    real*16, intent(in)         ::  signal(n_elements, 2)           !first column - time, second - data
    integer, intent(in)         ::  n_elements, n_initial, n_final  !#of points in input array, boundaries of maxima search
!---------------------------------OUTPUT--------------------------------
    real*16, intent(inout)      ::  integral                        !integrated signal within (t_max-FWHM, t_max+FWHM)
!---------------------------------INNER---------------------------------
    integer i                                                       !counter
    
    integral=0.0
    do i=max(1, n_initial), min(n_elements, n_final)                !!!PROTECTION FROM FOOL!!!
        integral=integral+signal(i,2)
    enddo
    
    integral=integral*(signal(2,1)-signal(1,1))
    
end subroutine integration

subroutine wigwam_correction(signal, n_elements, t_max, maxima, integral)
!---------------------------------DESCRIPTION---------------------------
! takes a signal of n_elements, t_max position, current values of maxima and integral and searches for a wigwam problem
! if wigwam problem is there, returns corrected values for maxima and integral
! if not, changes nothing
!---------------------------------INPUT---------------------------------
    real*16, intent(in)         ::  signal(n_elements, 2)           !first column - time, second - data
    integer, intent(in)         ::  n_elements, t_max               !#of points in input array, boundaries of maxima search
!---------------------------------OUTPUT--------------------------------
    real*16, intent(inout)      ::  maxima, integral                !integrated signal within (t_max-FWHM, t_max+FWHM)
!---------------------------------INNER---------------------------------
    integer i, ww_min, ww_max                                       !counter, min and max positions of wigwam pedestal
    real*16 slope                                                   !slope>o of the wigwam wall
    
    slope=0.1785*1e9                                                ![a.u./ns*1e9]=[a.u./s], slope is to estimate for every case at Origin PAY ATTENTION TO S-NS TRANSITION!
    
    i=t_max
    do while (signal(i,2) .EQ. signal(t_max,2))
        i=i-1
    enddo
    ww_min=i+1
    i=t_max
    do while (signal(i,2) .EQ. signal(t_max,2))
        i=i+1
    enddo
    ww_max=i-1
    
    !print *, ww_min, ww_max, slope*(signal(ww_max,1)-signal(ww_min,1))
    
    !print '(e14.6, e14.6)', integral, slope*(signal(ww_max,1)-signal(ww_min,1))*(signal(ww_max,1)-signal(ww_min,1))/4.
    integral=integral+slope*(signal(ww_max,1)-signal(ww_min,1))*(signal(ww_max,1)-signal(ww_min,1))/4.
    !print '(e14.6)', integral
    !print '(e14.6, e14.6)', maxima, slope*(signal(ww_max,1)-signal(ww_min,1))/2.
    maxima=maxima+slope*(signal(ww_max,1)-signal(ww_min,1))/2.
    !print '(e14.6)', maxima
    
end subroutine wigwam_correction

end module shg