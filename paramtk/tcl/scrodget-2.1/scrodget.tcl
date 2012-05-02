package provide scrodget 2.0.2


##  scrodget.tcl
##
##  scrodget.tcl - a generic SCROlled wiDGET
##
##    Scrodget enables user to create easily a widget with its scrollbar.
##    Scrollbars are created by Scrodget and scroll commands are automatically
##    associated to a scrollable widget with Scrodget::associate.
##
##    scrodget was inspired by ScrolledWidget (BWidget)
##
##  Copyright (c) 2005 <Irrational Numbers> : <aburatti@libero.it> 
##
##
##  NOTE: package "snit" (v0.97) is required.
##   It is freely downloadable from the Web:
##       http://www.wjduquette.com/snit
##
##  This program is free software; you can redistibute it and/or modify
##  it under the terms of the GNU General Public License as published by
##  the Free Software Foundation.
##
##  See the file "license" for information on usage and
##  redistribution of this program, and for a disclaimer of all warranties.
##

package require snit

#
# How to use scrodget:
#   Read "scrodget.txt" for detailed info.
#   Sample code is provided in "demo*.tcl".
#

option add *Scrodget.scrollsides se
option add *Scrodget.autohide   false


snit::widget scrodget {
    widgetclass Scrodget

    component northScroll -public northScroll
    component southScroll -public southScroll
    component eastScroll  -public eastScroll
    component westScroll  -public westScroll
     # replacement for old (deprecated) syntax:
     # expose hull as frame
    #    interp alias {} frame {} hull
    #    component hull -public frame
    delegate method {frame *} to hull

    option -scrollsides  \
           -default se  \
           -configuremethod Set_scrollsides \
           -validatemethod  Check_scrollsides

    method Check_scrollsides {option sides} {
      if { ! [regexp -expanded  {^[nesw]*$} $sides] } {
        return -code error "#bad scrollsides \"$sides\": only n,s,w,e allowed"
      }
    }

    option -autohide \
           -default false \
           -configuremethod Set_autohide

    variable auto     ; # array
    variable isHidden ; # array
    variable internalW  {}

     # Constants
     
     # for each 'side' (n,s,w,e) 
     #  define the position {row,col} within the 3x3 grid
    typevariable GridIdx  -array {
       n { 0 1 }
       s { 2 1 }
       w { 1 0 }
       e { 1 2 }
    }
    
    constructor {args} {
        # NOTE: 'isHidden' attribute for south/north (or east/west) are paired
       set isHidden(ns)  0
       set isHidden(ew)  0
       install northScroll using scrollbar $win.northScroll -orient horizontal
       install southScroll using scrollbar $win.southScroll -orient horizontal
       install eastScroll  using scrollbar $win.eastScroll
       install westScroll  using scrollbar $win.westScroll

         # fix against deprecated scrollbar set/get syntax
       $northScroll set 0 1
       $southScroll set 0 1
       $eastScroll  set 0 1
       $westScroll  set 0 1

        # 3 x 3 grid ; 
	#  the central cell (1,1) is for the internal widget.
	#  +-----+-----+----+  
	#  |     | n   |    |
	#  +-----+-----+----+  
	#  | w   |inter| e  |
	#  +-----+-----+----+  
	#  |     | s   |    |
	#  +-----+-----+----+  
	# Cells e or w are for vertical scrollbars 
	# Cells n or s are for horizontal scrollbars
	#  Note that scrollbars may be hidden.      

       grid rowconfig    $win 1 -weight 1 -minsize 0
       grid columnconfig $win 1 -weight 1 -minsize 0

        # force onconfigure
       $win configure -scrollsides [$win cget -scrollsides]
       $win configure -autohide    [$win cget -autohide]

       $self configurelist $args
    }


      # from the scrollbar's name, derive its 'side'
      #   i.e.  [whichSide $win.westScroll]  returns 'w'
    proc whichSide { sb } {
      return [string index [winfo name $sb] 0]
    }


      # from the scrollbar's name, derive its 'orientation'
      #  return values are: "ns" or "ew"
      # NOTE: [whichSide $win.northScroll] returns 'ew' (i.e. horizontal)
    proc whichOrient { sb } {
      set side [whichSide $sb]
      if { [string first $side "ns"] >= 0 } {
          set orient ew
      } else {
          set orient ns
      }
      return $orient
    }

    method associate { args } {
       set argc [llength $args]
       if { $argc == 0 } { return $internalW }
       if { $argc > 1 } {    
          return -code error "wrong # args: should be \"$win associate ?widget?\""
       }
        # just one argument 
       set w [lindex $args 0]

       if { $w != {}  &&  ! [winfo exists $w] } {
          return -code error "error: widget \"$w\" does not exist"
       }

        # detach previously associated-widget (if any)
       catch { 
        grid forget $internalW 
        $internalW configure -xscrollcommand {} -yscrollcommand {}
       }
       
       set internalW $w
       if { $internalW != {} } {
          $win.eastScroll configure  -command "$internalW yview"
          $win.westScroll configure  -command "$internalW yview"
          $win.northScroll configure -command "$internalW xview"
          $win.southScroll configure -command "$internalW xview"

          $internalW configure \
 	    -xscrollcommand [mymethod Auto_setScrollbar $win.northScroll $win.southScroll] \
 	    -yscrollcommand [mymethod Auto_setScrollbar $win.eastScroll $win.westScroll]

          catch {raise $internalW $win}
          grid $internalW -in $win -row 1 -column 1  -sticky news
       }
    }


    method Set_scrollsides {option sides} {      
       set options(-scrollsides) $sides
       if { ! $isHidden(ew) } {
           show_scrollbar $win.northScroll  $options(-scrollsides)
           show_scrollbar $win.southScroll  $options(-scrollsides)
       }
       if { ! $isHidden(ns) } {
           show_scrollbar $win.eastScroll   $options(-scrollsides)
           show_scrollbar $win.westScroll   $options(-scrollsides)
       }
    }
        

      # internal
      # note: both scrollbars have the same orientation
    method _handle_autohide { sbA sbB } {
       set sideA  [whichSide $sbA]
       set orient [whichOrient $sbA]
           
       if { $auto($orient) } {
           # 1/true : check if scrollbar should be hidden
           #          (based on the scrollbar's visible range)
           eval $win Auto_setScrollbar $sbA $sbB [$sbA get]
       } else {
           # 0/false : if scrollbars are hidden, then show them 
           if { $isHidden($orient) } {
              show_scrollbar $sbA  $options(-scrollsides)
              show_scrollbar $sbB  $options(-scrollsides)
              set isHidden($orient) 0
           }
       }
    }


    proc boolValue {x} { 
       if { [string is boolean $x] } {
         if { "$x" } { return 1 } else { return 0 }
       }
       return -code error "# not a boolean value"
    }


    method Set_autohide {option value} {
       set value1 $value
        # normalize boolean value (if boolean)
       catch { set value1 [boolValue $value1] }

       switch -- $value1 {
         0 -
         none       { set auto(ew) 0 ; set auto(ns) 0 }
         vertical   { set auto(ew) 0 ; set auto(ns) 1 }
         horizontal { set auto(ew) 1 ; set auto(ns) 0 }
         1 -
         both       { set auto(ew) 1 ; set auto(ns) 1 }
         default    { return -code error \
"# bad autohide \"$value\":\
 must be none,vertical,horizontal,both or a boolean value"
                    }
       }
       set options(-autohide) $value
       $win _handle_autohide $win.northScroll $win.southScroll
       $win _handle_autohide $win.eastScroll  $win.westScroll
    }


     # ? can a 'proc' access typevariables ??  yes.
    proc show_scrollbar {sb validSides} {
       set side [whichSide $sb]
       if { [string first $side $validSides] != -1 } {
            set r [lindex $GridIdx($side) 0]
            set c [lindex $GridIdx($side) 1]
            set sticky [whichOrient $sb]            
            grid $sb -row $r -column $c -sticky $sticky
       } else {
           grid forget $sb
       }
     }


     # private method
    method Auto_setScrollbar { sbA sbB first last }  {
       set sideA  [whichSide $sbA]
       set orient [whichOrient $sbA]

       if { $auto($orient) } {
          if { $first == 0 && $last == 1 } {
             if { ! $isHidden($orient) } {
                grid forget $sbA
                grid forget $sbB
                set isHidden($orient) 1
             }
          } else {
             if { $isHidden($orient) } {
                show_scrollbar $sbA  $options(-scrollsides) 
                show_scrollbar $sbB  $options(-scrollsides)                 
                set isHidden($orient) 0
             }
          }
       }
       $sbA set $first $last
       $sbB set $first $last
    }

}
