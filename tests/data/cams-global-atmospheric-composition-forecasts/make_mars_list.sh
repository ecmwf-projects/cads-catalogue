#!/bin/bash

set -eux

list=1
cat=1

result=mars.list

if [[ -e $result ]] ; then
  rm -i $result
fi

# NRT forecasts started on this date...
#month=201207
# ... but only documented from this date...
month=201501

thismonth=$(date +%Y%m)
while (( $month <= $thismonth )) ; do
  echo $month
 
  start_date=${month}01
  next_month=$(dateincr -d $start_date +32 | cut -c 1-6) 
  end_date=$(dateincr -d ${next_month}01 -1)

  target=./mars_lists/mars_${month}.list

  if [[ ! -e $target && $list == 1 ]] ; then
    mars <<EOF
list,
class=mc,
stream=oper,
expver=1,
date=$start_date/to/$end_date,
levtype=ml/pl/sfc,
method=all,
origin=all,
param=all,
step=all,
system=all,
dataset=all,
time=all,
type=an/fc,
output=tree,
target="$target"
EOF
  fi

  if (( $cat )) ; then
    cat $target >> $result
  fi

  month=$next_month
done


