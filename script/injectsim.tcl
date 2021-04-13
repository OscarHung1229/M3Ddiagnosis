proc faultsim_inject {fname logpath} {
	set f [open $fname "r"]
	set cnt 0

	while { [gets $f data] >= 0 } {
		set cnt [expr $cnt+1]
		if {$cnt == 1} {
			continue
		}
		set words [split $data]
		set fault [lindex $words 0]
		set pin [lindex $words 2]
		set arg "$fault $pin"
		set logname "[lindex [split $pin "/"] 0]_[lindex [split $pin "/"] 1]_st${fault}.log"
		puts $logname
		[run_simulation -slow $arg -failure_file $logpath/$logname]
	}

	close $f
}
