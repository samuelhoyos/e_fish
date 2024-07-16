module ssc
    contains 

subroutine file_reading (filepath, filename, header, signalwbgd, n_elements)
!---------------------------------DESCRIPTION---------------------------
! takes the filename, skips #=header of strings from the header (descriptive part of file, not data)
! returns measured signalwbgd of n_elements points
!---------------------------------INPUT---------------------------------
    character(80), intent(in)   ::  filename                    !contains #=header supportive lines and signalwbgd
    character(80), intent(in)   ::  filepath                    !line of file with path information
    integer, intent(in)         ::  header                      !number of lines with non-digital data
!---------------------------------OUTPUT--------------------------------
    real*16, allocatable        ::  signalwbgd(:,:)             !array: 1st column for time, 2nd for data values
    integer, intent(inout)      ::  n_elements                  !number of lines with digital data == lenght of the output massive; changes in cours of programm
!---------------------------------INNER---------------------------------
    integer i                                                   !counter
    
    n_elements=0
    !print *, n_elements
    open(1, file=trim(filepath)//trim(filename))
    !print *, trim(filepath)//trim(filename)
    do while(.true.)
        read(1, "(A)", iostat=iostat) line
        if (iostat /= 0) exit
        !print *, n_elements
        n_elements = n_elements + 1                                 !total # of lines
        
    end do
    !print *, n_elements
    rewind(1)                                                   !goes to the head of file again
    
    n_elements=n_elements-header                                !# of digital data lines
    if (allocated(signalwbgd)) then
            deallocate(signalwbgd)
    endif
    allocate(signalwbgd(n_elements, 2))
    do i=1, header
        read(1, "(A)")                                        !skipping #=header lines
    enddo       
    do i=1, n_elements
        read(1, *) signalwbgd(i, 1), signalwbgd(i, 2)           !writing all the lines after skipped ones: time and amplitude
        print *, signalwbgd(i, 1), signalwbgd(i, 2)  
    enddo
    close(1)
       
end subroutine file_reading

subroutine binner_sinner(t_student, n_student, shg_singleshot, n_elements, bin_width, shg_binned, n_bins)
!---------------------------------DESCRIPTION---------------------------
! takes the unbinned data shg_singleshot, does # of bins to fit all the time points from t_min to t_max with a bin_width step
! returns an (n_bins, 2) array with statistically treated values and filled time axis as a middle bin time point
!---------------------------------INPUT---------------------------------
    real*16, intent(in)         ::  shg_singleshot(n_elements, 2)   !first column - time, second - data
    real*16, intent(in)         ::  t_student(n_student,2)            !student coefficients for absolute random error estimation for a chosen probability (usually requested standart is 0.95=95%)
    integer, intent(in)         ::  n_elements                      !#of points in input array
    integer, intent(in)         ::  n_student                       !#of points in input array for t_student values
    real*16, intent(in)         ::  bin_width                       !the selected width of the bin
!---------------------------------OUTPUT--------------------------------
    real*16, allocatable        ::  shg_binned(:,:)                 !1st column for time, 2nd for arithmetic average (further 'mean'), 3rd for absolute random error (furter 'error'), 4th for # of data points collected in a bin (further 'histogram')
    integer, intent(inout)      ::  n_bins                          !# of bins
!---------------------------------INNER---------------------------------
    integer i, j, j_initial, j_final                                !counters
    logical flag                                                    ! boolean variable with values .TRUE. or .FALSE. to continue in or to go out of the cycle

!--------------------------CORRECT INPUT CHECK--------------------------
    !print '(i6)', n_student
    !do i=1, n_student
    !    print '(f6.0, f8.4)', t_student(i,1), t_student(i,2)
    !enddo
    !print '(i6)', n_elements
    !do i=1, n_elements
    !    print '(e14.6, e14.6)', shg_singleshot(i,1), shg_singleshot(i,2)
    !enddo
    !print '(f6.2)', bin_width    
    
    n_bins=int(( shg_singleshot(n_elements,1)-shg_singleshot(1,1) )/bin_width)+1
    !print '(e14.6, e14.6, i6)', shg_singleshot(n_elements,1), shg_singleshot(1,1), n_bins
    print *, n_bins
!------------------------------DEALLOCATION-----------------------------
    if (allocated(shg_binned)) then
        deallocate(shg_binned)
    endif
!-----------------------------ALLOCATION, ZEROING-----------------------
    allocate(shg_binned(n_bins,4))
    do i=1, n_bins
        shg_binned(i,1)=shg_singleshot(1,1)+bin_width*(i-1)                                 !TIME = time in a beginning of each bin for now for commodity, in the end will be changed to the central time value during the bin
        shg_binned(i,2)=0.0                                                                 !MEAN values are initially zeroed
        shg_binned(i,3)=0.0                                                                 !ERROR values are initially zeroed
        shg_binned(i,4)=0.0                                                                 !HISTOGRAM values are initially zeroed        
    enddo
    do i=1, n_bins
       print '(i8, f6.2, e12.2, e12.2, i6)', i, shg_binned(i,1), shg_binned(i,2), shg_binned(i,3), int(shg_binned(i,4))
    enddo
!--------------------------------CALCULATIONS---------------------------
    j=1
    j_initial=1
    j_final=1
    flag=.TRUE.
    do i=1, n_bins
        print '(i8, i8, i8)', j, j_initial, j_final
        do while (flag)
            if (shg_singleshot(j,1) .GE. shg_binned(i,1)) then
                flag=.FALSE.
            else
                if (j .GE. n_elements) then
                    flag=.FALSE.
                endif
            endif
            j=j+1
        enddo
        j_initial=j-1
        j=j-1
        flag=.TRUE.
        !print '(i8, i8, i8)', j, j_initial, j_final
        !print *, '--------bin-------bin+1-------t_shg---------shg--hist-----j'
        do while (flag)
            if (shg_singleshot(j,1) .GE. shg_binned(i,1)+bin_width) then
                flag=.FALSE.
            else
                shg_binned(i,2)=shg_binned(i,2)+shg_singleshot(j,2)                             !summ of all singleshot values of the bin, will be devided by the bins histogram further
                shg_binned(i,4)=shg_binned(i,4)+1                                               !evaluation of the bins histogram
                print '(f12.2, f12.2, f12.2, e12.2, i6, i6)', shg_binned(i,1), shg_binned(i,1)+bin_width, shg_singleshot(j,1),&
                shg_singleshot(j,2), int(shg_binned(i,4)), j
                if (j .GE. n_elements) then
                    j=j+1
                    flag=.FALSE.
                endif
            endif
            j=j+1
        enddo
        j_final=j-2
        flag=.TRUE.
        !print '(i8, i8, i8)', j, j_initial, j_final
        
!------------------------------STATISTICS-------------------------------
        if (shg_binned(i,4) .GT. 1.0) then
            shg_binned(i,2)=shg_binned(i,2)/shg_binned(i,4)                                 !MEAN values - READY
            !print '(i8, i8, i8)', j, j_initial, j_final
            !print *, '-------mean------single---(delta)^2--S(delta)^2-----j'
            do j=j_initial, j_final
                shg_binned(i,3)=shg_binned(i,3)+(shg_binned(i,2)-shg_singleshot(j,2))**2    !evolution of unbiased variance estimate S^2, will be divided by (histogram-1)
                !print '(e12.2, e12.2, e12.2, e12.2, i6)', shg_binned(i,2), shg_singleshot(j,2), (shg_binned(i,2)-shg_singleshot(j,2))**2, shg_binned(i,3), j
            enddo
            !print *, 'sum(delta)^2=', shg_binned(i,3)
            shg_binned(i,3)=shg_binned(i,3)/((shg_binned(i,4)-1)*shg_binned(i,4))
            !print *, 'sum(delta)^2/(hist*(hist-1))=', shg_binned(i,3)
            shg_binned(i,3)=sqrt(shg_binned(i,3))*t_student(int(shg_binned(i,4)),2)         !ERROR - READY
            !print *, 't_student(hist)=', t_student(int(shg_binned(i,4)),2)
        endif        
        j=j_final+1
        print *, 'OUT--------time------------mean-----------error------------hist-------i'
        print '(f16.2, e16.2, e16.2, f16.2, i8)', shg_binned(i,1), shg_binned(i,2), shg_binned(i,3), shg_binned(i,4), i
        print '(i8, i8, i8)', j, j_initial, j_final  
    enddo
    
    do i=1, n_bins
        shg_binned(i,1)=shg_binned(i,1)+bin_width/2.0                                           !time = central time value during the bin
    enddo

end subroutine binner_sinner

end module ssc