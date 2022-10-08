#!/bin/bash

# Run this on a compute node

set -eux

#dir=/scratch/rd/nal/ads/$(basename $(dirname $(readlink -m $0)))
#mkdir -p $dir
#cd $dir

if [[ -e mars.list ]] ; then
  mv mars.list mars.list.old
fi

month=200301
#while (( $month <= 200301 )) ; do
while (( $month <= 202112 )) ; do
 
  start_date=${month}01
  next_month=$(date -d "${month}01+1 month" +%Y%m)

  mars <<EOF
list,
database=cdsmars,
date=$start_date,
target=mars_${month}.list,
class=mc,
dataset=reanalysis-monthly-means-of-daily-means/reanalysis-synoptic-monthly-means,
type=an,
levtype=ml/pl/sfc,
method=all,
origin=all,
param=all,
step=all,
system=all,
time=all,
output=tree
EOF

#expver=eac4,
#stream=mnth/moda,

  #cat mars_${month}.list >> mars.list

  # For some reason MARS doesn't put the date in the output so we do it
  # manually.
  date="${start_date:0:4}-${start_date:4:2}-${start_date:6:2}"
  while IFS= read -r line ; do
    echo "$line,date=$date" >> mars.list
  done < mars_${month}.list

  month=$next_month
done

