#!/bin/bash

plotdir='.'

start_date='20220122'
end_date='20220122'

date=$start_date
until [ $date -gt $end_date ]
do
	echo $date
	python ~/scripts/drumplot_MSVF.py -d $date -p $plotdir -m 1 -f lp -1 0.03
	date=`date --date="$date 1 day" +%Y%m%d`
done

