#!/bin/bash
#
# Time sheet tool
#

PID=$$
PGM=`basename $0`
TMP=/tmp/.$PGM.$PID
export PATH=$(dirname "$0"):$PATH
. $(which helpers) || exit 1
# DEBUG=yes

if [ "$1" = "-r" ]
then
	shift
	which socat > /dev/null || end $? "install socat"
	log 1 "refreshing"
	pids=$(pgrep mpv)
	for socket in /tmp/videowall-socket.*.*
	do
		echo '{ "command": ["get_property_string", "path"] }' | socat - $socket 2>/dev/null | jq .data | sed 's/"//g' || rm $socket
	done > /tmp/videowall.keep
	count=$(cat /tmp/videowall.keep | wc -l)
	cat /tmp/videowall.keep | SINGLELOOP=true videowall $count "$@"
	sleep $(($count * 2))
	kill -9 $pids 2>/dev/null
	exit
fi

for prefs in /etc/$PGM ~/etc/$PGM ~/.$PGM
do
	#	echo $prefs
	[ -f "$prefs" ] && log "  reading $prefs" && . "$prefs"
done

export PATH="/usr/local/opt/gnu-getopt/bin:$PATH"

OPTS="rkld:m:p:s:V:hvq"
LONGOPTS="days:,kill,panscan:,screen:,max:,volume:,singleloop:,quiet,verbose,help"
parsed_opts=$(getopt -o $OPTS -l "$LONGOPTS" -- "$@" 2>$TMP.getopt)  || end $? "$USAGE $(echo; sed "s/^getopt[\b:]*//" $TMP.getopt)"
eval "set -- $parsed_opts"

for o do
    case $1 in
        (-d|--days) days=$2; log days $days; shift 2;;
        (-m|--max) max=$2; log max $max; shift 2;;
        (-p|--panscan) PANSCAN=$2; log panscan $PANSCAN; shift 2;;
        (-s|--screen) screen=$2; log screen $screen; shift 2;;
        (-V|--volume) VOLUME=$2; log volume $VOLUME; shift 2;;
        (-k|--kill) kill=true; log kill $kill; shift;;
        (-l|--singleloop) SINGLELOOP=true; log singleloop $SINGLELOOP; shift;;
        (-h|--help) help; end;;
        (-q|--quiet) STDOUT="/dev/null"; QUIET=yes; DEBUG=no; shift;;
        (-v|--verbose) STDERR="&1"; DEBUG=yes; shift;;
        (--) shift; break;;
        (*) shift;; # This will handle non-option arguments
    esac
done

[ $ERROR ] && end $ERROR "$(usage)
type '$PGM --help' for more info"

log singleloop $SINGLELOOP
[ ! "$PANSCAN" ] && PANSCAN=false
if isnum $PANSCAN
then
	pan=$PANSCAN
	(( $(echo "$PANSCAN > 1" |bc -l) )) >/dev/null && pan=1
	(( $(echo "$PANSCAN < 0" |bc -l) )) >/dev/null && pan=0
elif istrue $PANSCAN
then
	pan=1
else
	pan=0
fi
fit="-panscan $pan"
log panscan $fit

[ ! "$VOLUME" ] && VOLUME=40
if isnum $VOLUME
then
	SMARTVOLUME=false
elif [ "$VOLUME" = "smart" ] || istrue $VOLUME
then
	SMARTVOLUME=true
	VOLUME=40
else
	SMARTVOLUME=false
fi

[ ! "$RANDOMIZE" ] && RANDOMIZE=true
[ ! "$BALANCE" ] && BALANCE=true
[ ! "$fantomscreen" ] && fantomscreen=none
# echo "fantomscreen $fantomscreen"

trap "sleep 0.25; rm -f $TMP* 2>/dev/null" EXIT
which bc >/dev/null || { echo "no bc found"; exit 2; }
player=$(which mpv || which mplayer) || { echo "$PGM: no player found" >&2 ; exit 1; }
player=$(basename $player)

istrue $kill && pids=$(pgrep $player)

findmovies () {
	isnum $days && dayfilter="-mtime -$days"
	# find "$@" -type f $dayfilter ! \( -iname "*.avi" -o -iname "*.mp4" -o -iname "*.webm" -o -iname "*.wmv" -o -iname "*.mov" -o -iname "*.flv" \) \
	# log "find "$@" -type f $dayfilter -regextype posix-extended -regex '\.(avi|mp4|webm|wmv|mov|mpe?g)$'"

	regex='[^\.].*\.(avi|mp4|webm|m4v|mkv|wmv|mov|mpe?g)(.part)?$'
	if [[ "$OSTYPE" == "darwin"* ]]; then
		log "darwin"
		# macOS
		find -E "$@" -type f $dayfilter -regex "$regex" | grep -v "/\.Saved" > $TMP.find
	else
		log "linux"
		# Linux
		find "$@" -type f $dayfilter -regextype posix-extended -regex "$regex" | grep -v "/\.Saved" > $TMP.find
	fi
	# find "$@" -type f $dayfilter -regextype posix-extended -regex '[^\.].*\.(avi|mp4|webm|m4v|mkv|wmv|mov|mpe?g)(.part)?$' | grep -v "/\.Saved" > $TMP.find
	if isnum $max && isnum $days
	then
		probe=true
		cat $TMP.find | xargs -d"\n" ls -dt | grep "[[:alnum:]]" > $TMP.sorted
		cat $TMP.sorted | while read file
		do
			du "$file" | grep -q "^0" && continue
			echo "$file"
		done > $TMP.filtered
		head -$max $TMP.filtered
	else
		cat $TMP.find
	fi
	log "found  $(cat $TMP.find | wc -l) files in $@"
}

isnum "$1" && windows=$1 && shift
isnum $windows && isnum $max && [ $max -lt $windows ] && windows=$max

uname -a | egrep -q "Ubuntu|Debian" && os=linux

if [ "$1" ]
then
	for file in "$@"
	do
		echo "$file"
	done
elif [ -t 0 ]
then
  pwd
else
  cat
fi | while read file
do
  echo "$file" | grep "https*://" && mode=http && continue
  [ -d "$file" ] && findmovies "$file" && continue
  [ -f "$file" ] && ffprobe -i "$file" >/dev/null 2>/dev/null && echo "$file" && continue
  [ "$NOFILECHECK" = "true" ] && echo "$file"
done > $TMP.list

grep -q . $TMP.list 2>/dev/null || end $? "nothing to play"
log found $(cat $TMP.list | wc -l) videos to play

if [[ "$OSTYPE" == "darwin"* ]]; then
	# macOS
	displayplacer list | awk -F': ' '/Resolution/{res=$2} /Origin/{gsub(/[()]/, "", $2); split($2, a, ","); print res "+" a[1] "+" a[2]}' > $TMP.screens
else
	# Linux
	xrandr --query | grep -E "connected.*[0-9]+x[0-9]+\+[0-9]+\+[0-9]+" \
	| sed -e "s/.*connected //" -e "s/^primary \(.*\)/\\1\tprimary/" \
	| while read line
	do
		pos=$(echo "$line" | cut -d " " -f 1 | cut -d "+" -f 2,3)
		primary=$(echo "$line" | grep -Eo primary)
		printf "$pos\t$line\n"
	done \
	| sort -n | cut -f 2- > $TMP.screens
fi

allscreens=$(cat $TMP.screens | wc -l)

[ "$fantomscreen" = "right" -o "$fantomscreen" = "left"  ] && audioscreens=$(($allscreens + 1)) || audioscreens=$allscreens


count=$(cat $TMP.list | wc -l)
[ $count -lt $windows ] 2>/dev/null && windows=$count && max=$count && SINGLELOOP=true
if istrue $SINGLELOOP
then
	if ! isnum $max
	then
		isnum $windows && max=$windows || max=$count
	fi
 	[ $count -lt $max ] && max=$count
	windows=$max
fi

log windows $windows
log max $max
log count $count
log singleloop $SINGLELOOP
# end DEBUG

if [ "$windows" ] && [ $windows -lt 0 ]
then
  windows=1
  crossscreen=true
  [ ! "$screen" ] && screen=0
  singlescreen=$screen
  screen=0
  screens=1
  PANSCAN=true
  cat $TMP.screens | cut -d " " -f 1 | tr "+x" " " | while read sx sy px py
  do
    echo $((sx + px)) >> $TMP.x
    echo $((sy + py)) >> $TMP.y
  done
  cx=$(sort -n $TMP.x | tail -1)
  cy=$(sort -n $TMP.y | tail -1)
else
  if [ $screen ]
  then
    singlescreen=$screen
    screen=0
    screens=1
  else
    unset singlescreen
    screen=0
    screens=$allscreens
  fi
fi
[ ! $windows ] && windows=$screens
[ $windows -eq 0 ] && windows=1
videosPerScreen=$((windows%screens?windows/screens+1:windows/screens))
[ $videosPerScreen -gt 4 ] && quality="--ytdl-format=0" \
|| [ $videosPerScreen -gt 1 ] && quality="--ytdl-format=1" \
|| quality="--ytdl-format=1"
[ "$SMARTVOLUME" = "true" ] \
  && volume=$(echo "$VOLUME / sqrt($videosPerScreen)" | bc) \
  || volume=$VOLUME

emptyslots=$(($videosPerScreen * $screens - $windows))

# echo "screens: $screens"
# echo "windows: $windows"
# echo "win/scr: $videosPerScreen"
maxperside_horiz=0
maxperside_vert=0
maxperscreen=0
while [ $maxperscreen -lt $videosPerScreen ]
do
	if [ $videosPerScreen -eq 3 ]
	then
		maxperside_vert=1
		maxperside_horiz=3
	elif [ "$growy" ]
	then
 		maxperside_vert=$(($maxperside_vert+1))
		growy=
	else
 		maxperside_horiz=$(($maxperside_horiz+1))
		growy=yes
	fi
  maxperscreen=$(($maxperside_horiz*$maxperside_vert))
done
wt=0; i=0;

# [ "$RANDOMIZE" = true ] && sort -R $TMP.list > $TMP.randomized && mv $TMP.randomized $TMP.list
cp $TMP.list $TMP.play

offset=$(cat $TMP.screens | grep primary | cut -d " " -f 1 | cut -d + -f 2,3)
offsetx=$(echo $offset | cut -d+ -f 1 | grep [0-9] || echo 0)
offsety=$(echo $offset | cut -d+ -f 2 | grep [0-9] || echo 0)

s=-1
cat $TMP.screens | while read geometry f
do
	s=$(($s + 1))
  [ "$singlescreen" ] && [ $singlescreen -ge 0 ] && [ $screen -ne $singlescreen ] && screen=$(($screen + 1)) && continue
  [ "$SINGLELOOP" = "true" ] && [ $i -gt $count ] && break
  SCRsize=$(echo $geometry | cut -d "+" -f 1)
  SCRsizex=$(echo $SCRsize | cut -d "x" -f 1)
  echo "$SCRsizex" | egrep -q "[a-z]" && continue
  SCRsizey=$(echo $SCRsize | cut -d "x" -f 2)
	SCRpos=$(echo $geometry | cut -d "+" -f 2-)
	SCRposx=$(echo $geometry | cut -d "+" -f 2)
	SCRposx=$(($SCRposx - $offsetx))
  SCRposy=$(echo $geometry | cut -d "+" -f 3)
	SCRposy=$(($SCRposy - $offsety))
  slotWidth=$(($SCRsizex / $maxperside_horiz))
  slotHeight=$(($SCRsizey / $maxperside_vert))
  x=0; ws=0;
	videosPerScreenslots=$(($maxperside_horiz * $maxperside_vert - $videosPerScreen))

  # echo "s: $s"
  while [ $x -lt $maxperside_horiz -a $ws -lt $videosPerScreen -a $wt -lt $windows ]
  do
		skipnext=false
    [ "$SINGLELOOP" = "true" ] && [ $i -gt $count ] && break
    y=0
    while [ $y -lt $maxperside_vert -a $ws -lt $videosPerScreen -a $wt -lt $windows ]
    do
			if [ "$skipnext" = "true" ]
			then
				y=$(($y + 1))
	      # ws=$(($ws + 1))
	      # wt=$(($wt + 1))
				skipnext=false
				continue
			fi
      if [ "$SINGLELOOP" = "true" ]
      then
        i=$(($i + 1))
        [ $i -gt $count ] && break
        printf "$i\t" >&2
        head -$i $TMP.list | tail -1 | tee $TMP.play >&2
      else
        [ "$RANDOMIZE" = "true" ] && shuffle="--shuffle"
      fi
      [ "$fantomscreen" = "left" ] && audioscreen=$(($screen + 1)) || audioscreen=$screen
      balance=$(bc -l <<< "scale=2;($audioscreen * $maxperside_horiz + $x) / ($audioscreens * $maxperside_horiz - 1) * 2 - 1")
			if [ $videosPerScreenslots -gt 0 -a $y -lt $(($maxperside_vert - 1)) ]
			then
				windowHeight=$(($slotHeight * 2))
				skipnext=true
				videosPerScreenslots=$(($videosPerScreenslots - 1))
			else
				windowHeight=$slotHeight
			fi
      # echo screens: $screens balance: $balance
			WINposx=$(($SCRposx + $x * $slotWidth))
			WINposy=$(($SCRposy + $y * $slotHeight))
      case $player in
        mplayer)
        # [ "$PANSCAN" = "true" ] && fit="-panscan 1"
        # echo mplayer;
        cat $TMP.play | mplayer -noborder -xineramascreen -2 $fit -geometry ${slotWidth}x${slotHeight}+${WINposx}+${WINposy} -playlist - &
        ;;
        mpv)
        # echo mpv;
        # [ "$PANSCAN" = "true" ] && fit="--panscan=1"
        # cat $TMP.play | mpv --ytdl-format=worst --af=stereotools=balance_out=$balance --no-border --screen $screen --fs-screen $screen --panscan 1 -geometry ${slotWidth}x${slotHeight}+${WINposx}+${WINposy} --playlist - --loop-playlist=inf $shuffle  & break
        geometry=${slotWidth}x${windowHeight}+${WINposx}+${WINposy}
				# --screen $screen --fs-screen
				# echo "$XDG_DATA_DIRS" | grep -Eo 'xfce|kde|gnome' && scrparam="--screen=0 --fs-screen=$screen"
        [ "$crossscreen" ] && geometry=${cx}x${cy}-${offsetx}-${offsety} && balance=0 && scrparam="--screen=$screen --fs-screen=$screen"
        [ "$BALANCE" = "true" ] && balanceparams=" --af=loudnorm,stereotools=balance_out=$balance"
        if [ "$os" = "linux" ]
        then
          mpvcmd="mpv --no-keepaspect-window --input-ipc-server=/tmp/$PGM-socket.$s.$x.$y --screen=0 --fs-screen=$s --volume=$volume  $quality $balanceparams --no-border $fit --loop-playlist=inf $shuffle --playlist=-"
          # if [ ! "$crossscreen" ]
          # then
            mpvcmd="$mpvcmd $scrparam -geometry=$geometry"
          # fi
        else
			geometry=${slotWidth}x${slotHeight}
        	mpvcmd="mpv --no-keepaspect-window --input-ipc-server=/tmp/$PGM-socket.$s.$x.$y --screen=$screen --fs-screen=$s --volume=$volume $quality $stereo --no-border $fit --loop-playlist $shuffle --playlist=-"
            mpvcmd="$mpvcmd $scrparam -geometry=$geometry"
        fi
        log "mpvcmd $mpvcmd"
        cat $TMP.play | $mpvcmd >/dev/null 2>/dev/null &
        # [ "$crossscreen" ] && sleep 0.25 && echo "wmctrl -xa gl.mpv -e 5,0,0,$cx,$cy" && wmctrl -xa gl.mpv -e 5,0,0,$((1920 * 4)),$cy
        ;;
        # *)
        # echo not supported
        # ;;
      esac
      y=$(($y + 1))
      ws=$(($ws + 1))
      wt=$(($wt + 1))
      sleep 0.05
    done
    x=$(($x + 1))
  done

  screen=$(($screen + 1))
  # s=$(($s + 1))
done

[ "$pids" ] && kill $pids 2>/dev/null
