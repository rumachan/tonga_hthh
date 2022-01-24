#!/usr/bin/env python

from obspy.core import UTCDateTime, Stream
from obspy.clients.fdsn import Client
from obspy.signal.detrend import spline
import numpy as np
import sys
import os, getopt
import matplotlib.pyplot as plt
import pandas as pd
import datetime as dt

#initialise variables
date = ''
filter = ''
f = ''
f1 = ''
f2 = ''
corners = 2
zerophase = False
plot_dir = ''
defscale_seis = 200
defscale_acou = 0.5
magn = 1

#large trace clip
clip_seis = 100000
clip_acou = 2

titlesize = 24

#IRIS FDSN web server
client = 'IRIS'

#arguments
myopts, args = getopt.getopt(sys.argv[1:],"d:f:1:2:p:m:")
# o == option
# a == argument passed to the o
for o, a in myopts:
    if o == '-d':
        date = a
    elif o == '-f':
        filter = a
    elif o == '-1':
        f1 = float(a)
    elif o == '-2':
        f2 = float(a)
    elif o == '-p':
        plot_dir = a
    elif o == '-m':
        magn = float(a)
    else:
        print("Usage: %s -d date(20150619) -f filter(bp,lp,hp) -1 f1 -2 f2 -p plot_dir -m magnification" % sys.argv[0])

#check arguments
#minimum requirement is a site and plot directory
if (plot_dir == ''):
    print("Usage: %s -d date(20150619) -f filter(bp,lp,hp) -1 f1 -2 f2 -p plot_dir -m magnification" % sys.argv[0])
    sys.exit()
if (date == ''):
    current = True

site = 'MSVF.10.BHZ.II'

stn = site.split(".")[0]
loc = site.split(".")[1]
cmp = site.split(".")[2]
net = site.split(".")[3]


#format neic query for label on drumplot, as list of dict
df = pd.read_csv('/home/sherburn/Dropbox/work/tonga_neic/query.csv', parse_dates=True, index_col='time', usecols=['time','mag'])

datef = dt.datetime.strptime(date, '%Y%m%d').strftime('%Y-%m-%d')

events = df[datef:datef]
events.reset_index(inplace=True)
events = events.rename(columns={'mag':'text'})

events['time'] = events['time'].dt.tz_convert(None)
events['time'] += pd.Timedelta(minutes=3) #add 3 mins as approx travel time to site
events['time'] = events['time'].apply(UTCDateTime)

evlist = events.to_dict('records')

#retrieve waveform data
time = UTCDateTime(date)
try:
    client = Client(client)
    st = client.get_waveforms(str(net), str(stn), str(loc), str(cmp), time, time + 86400, attach_response=True)
    print('arc client successful')
except:
    print('client not successful')
    exit()

st.merge(fill_value = 'interpolate') #merge streams, fill gaps with zeros
#st.merge(fill_value = 0.0) #merge streams, fill gaps with zeros
st.remove_sensitivity()
tr = st[0]
print ('data retrieved')

#specific trace management, seismic vs acoustic
if cmp != 'HDF':
    #seismic
    tr.data *= 1e9 #convert from m/s to nm/s
    tr.data = np.clip(tr.data, clip_seis*-1, clip_seis)
    scale = defscale_seis / magn
if cmp == 'HDF':
    #acoustic
    tr.detrend(type='linear')
    tr.filter('highpass', freq=hdfhp, corners=corners, zerophase=zerophase)
    tr.data = np.clip(tr.data, clip_acou*-1, clip_acou)
    scale = defscale_acou / magn
print (tr)

if filter == 'lp':
    tr.filter("lowpass", freq=f1, corners=corners, zerophase=zerophase)
elif filter == 'hp':
    tr.filter("highpass", freq=f1, corners=corners, zerophase=zerophase)
elif filter == 'bp':
    tr.filter('bandpass', freqmin=f1, freqmax=f2, corners=corners, zerophase=zerophase)

#plot title
if (filter == 'bp'):
    strf1 = '%.2f' %f1
    strf2 = '%.2f' %f2 
    title = site+'_'+date+'_bandpass_'+str(f1)+'-'+str(f2)+'_plot-gain_'+str(magn)
elif (filter == 'lp'):
    strf1 = '%.2f' %f1
    title = site+'_'+date+'_lowpass_'+str(f1)+'_plot-gain_'+str(magn)
elif (filter == 'hp'):
    strf1 = '%.2f' %f1
    title = site+'_'+date+'_highpass_'+str(f1)+'_plot-gain_'+str(magn)
else:
    title = site + '_' + date + '_nofilt'+'_plot-gain_'+str(magn)

outfile = os.path.join(plot_dir,title+'.drum.png')
fig = plt.figure(figsize=(15,20))
tr.plot(fig=fig, type='dayplot', linewidth = 0.3, vertical_scaling_range= scale, color=('navy','blue','blue','blue'), title=title, outfile=outfile, title_size=titlesize, events=evlist)
