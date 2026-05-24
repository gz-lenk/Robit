proc parse_args {argv} {
    array set opts {}
    set i 0
    while {$i < [llength $argv]} {
        set key [lindex $argv $i]
        incr i
        if {$i >= [llength $argv]} {
            error "missing value for $key"
        }
        set value [lindex $argv $i]
        incr i
        regsub {^--} $key "" key
        set opts($key) $value
    }
    return [array get opts]
}

proc json_escape {text} {
    set text [string map [list "\\" "\\\\" "\"" "\\\"" "\n" "\\n" "\r" ""] $text]
    return $text
}

proc parse_wns_from_text {text} {
    if {[regexp {WNS\(ns\)\s+([-0-9.]+)} $text -> wns]} {
        return $wns
    }
    if {[regexp {Slack\s+\(MET\)\s+:\s+([-0-9.]+)} $text -> wns]} {
        return $wns
    }
    if {[regexp {Slack\s+\(VIOLATED\)\s+:\s+([-0-9.]+)} $text -> wns]} {
        return $wns
    }
    return "unknown"
}

proc path_field {path prop fallback} {
    if {[catch {set value [get_property $prop $path]}]} {
        return $fallback
    }
    if {$value eq ""} {
        return $fallback
    }
    return $value
}

proc write_summary_json {path summary} {
    set fh [open $path w]
    puts $fh "{"
    puts $fh "  \"top\": \"[json_escape [dict get $summary top]]\","
    puts $fh "  \"part\": \"[json_escape [dict get $summary part]]\","
    puts $fh "  \"strategy\": \"[json_escape [dict get $summary strategy]]\","
    puts $fh "  \"wns\": \"[json_escape [dict get $summary wns]]\","
    puts $fh "  \"worst_logic_levels\": \"[json_escape [dict get $summary worst_logic_levels]]\","
    puts $fh "  \"critical_paths\": ["
    set first 1
    foreach item [dict get $summary critical_paths] {
        if {!$first} { puts $fh "," }
        set first 0
        puts -nonewline $fh "    {\"slack\": \"[json_escape [dict get $item slack]]\", "
        puts -nonewline $fh "\"levels\": \"[json_escape [dict get $item levels]]\", "
        puts -nonewline $fh "\"startpoint\": \"[json_escape [dict get $item startpoint]]\", "
        puts -nonewline $fh "\"endpoint\": \"[json_escape [dict get $item endpoint]]\"}"
    }
    puts $fh ""
    puts $fh "  ],"
    puts $fh "  \"high_fanout_nets\": ["
    set first 1
    foreach item [dict get $summary high_fanout_nets] {
        if {!$first} { puts $fh "," }
        set first 0
        puts -nonewline $fh "    {\"name\": \"[json_escape [dict get $item name]]\", "
        puts -nonewline $fh "\"fanout\": \"[json_escape [dict get $item fanout]]\"}"
    }
    puts $fh ""
    puts $fh "  ]"
    puts $fh "}"
    close $fh
}

array set opts [parse_args $argv]
foreach required {top part rtl out_dir jobs strategy max_paths max_fanout summary_json} {
    if {![info exists opts($required)]} {
        error "missing required --$required"
    }
}

file mkdir $opts(out_dir)
set project_name "timing_$opts(strategy)"
create_project -force $project_name $opts(out_dir) -part $opts(part)
if {[info exists opts(board_part)] && $opts(board_part) ne ""} {
    set board_matches [get_board_parts -quiet $opts(board_part)]
    if {[llength $board_matches] > 0} {
        set_property board_part $opts(board_part) [current_project]
    } else {
        puts "WARNING: board_part '$opts(board_part)' not found. Continuing with part '$opts(part)'."
    }
}

set rtl_files [split $opts(rtl) ";"]
foreach rtl $rtl_files {
    if {$rtl ne ""} {
        read_verilog -sv $rtl
    }
}

if {[info exists opts(xdc)] && $opts(xdc) ne ""} {
    foreach xdc [split $opts(xdc) ";"] {
        if {$xdc ne ""} {
            read_xdc $xdc
        }
    }
} elseif {[info exists opts(clock_period)]} {
    create_clock -name $opts(clock_port) -period $opts(clock_period) [get_ports $opts(clock_port)]
}

set synth_args [list -top $opts(top) -part $opts(part)]
if {$opts(strategy) ne "default"} {
    lappend synth_args -directive $opts(strategy)
}
synth_design {*}$synth_args
opt_design
place_design
phys_opt_design
route_design

set timing_report [file join $opts(out_dir) "timing_summary.rpt"]
set fanout_report [file join $opts(out_dir) "high_fanout_nets.rpt"]
set critical_report [file join $opts(out_dir) "critical_paths.rpt"]

report_timing_summary -file $timing_report
report_timing -max_paths $opts(max_paths) -sort_by slack -file $critical_report
report_high_fanout_nets -max_nets $opts(max_fanout) -file $fanout_report

set timing_text ""
if {[file exists $timing_report]} {
    set fh [open $timing_report r]
    set timing_text [read $fh]
    close $fh
}
set wns [parse_wns_from_text $timing_text]

set critical_paths {}
set worst_levels 0
set paths [get_timing_paths -max_paths $opts(max_paths) -sort_by slack]
foreach path $paths {
    set slack [path_field $path SLACK unknown]
    set levels [path_field $path LOGIC_LEVELS 0]
    set startpoint [path_field $path STARTPOINT_PIN unknown]
    set endpoint [path_field $path ENDPOINT_PIN unknown]
    if {$levels > $worst_levels} {
        set worst_levels $levels
    }
    lappend critical_paths [dict create \
        slack $slack \
        levels $levels \
        startpoint $startpoint \
        endpoint $endpoint]
}

set fanout_items {}
set nets [lsort -integer -decreasing -command {apply {{a b} {
    set fa [get_property FLAT_PIN_COUNT $a]
    set fb [get_property FLAT_PIN_COUNT $b]
    expr {$fa - $fb}
}}} [get_nets -hierarchical]]
set count 0
foreach net $nets {
    if {$count >= $opts(max_fanout)} {
        break
    }
    set fanout [get_property FLAT_PIN_COUNT $net]
    if {$fanout eq ""} {
        set fanout [llength [all_fanout -flat -endpoints_only -from $net]]
    }
    lappend fanout_items [dict create name $net fanout $fanout]
    incr count
}

write_summary_json $opts(summary_json) [dict create \
    top $opts(top) \
    part $opts(part) \
    strategy $opts(strategy) \
    wns $wns \
    worst_logic_levels $worst_levels \
    critical_paths $critical_paths \
    high_fanout_nets $fanout_items]

write_checkpoint -force [file join $opts(out_dir) "routed.dcp"]
close_project
