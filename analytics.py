# coding=utf-8
import os;
import csv;
import subprocess;
import sys;
import codecs;
import numpy as np;
import pandas as pd;
import math;
import os;
import pathlib;
from typing import NamedTuple;

# If python says it cannot find module parse, you need to type "pip install parse" into the command line to install the proper module. It's not part of the default.
# Note that on newer MacOS versions (10.x), the command might be "pip3 install parse" as the executable has been renamed. If pip is not found, try pip3.
from parse import parse
from datetime import date
from datetime import time
from datetime import datetime
from datetime import timedelta
import decimal
import locale
import configparser
import io

date_fmt_intern = '%Y-%m-%d %H:%M:%S'

def logexport( csvfilename, header, rows):
    "Schreibt eine Logdatei im CSV-Format"
        
    print(" === Begin Export === ")
    with open(csvfilename, "wt", newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(header)    
        for row in rows[0:len(rows)]:
            writer.writerow(row)        
        
    
def logimport( csvfilename ):
    "Liest eine Logdatei im CSV-Format ein"        
    rows = []
    header = [];
    
    # Sanitize file (remove whitespace from each row and replace "," with "."    
    csvtempfilename = csvfilename.replace(".csv", "_clean.csv");    
    with open(csvfilename, "rt+") as csvfile:
        with open(csvtempfilename, "wt+") as csvcleanfile:           
            csvcleanfile.seek(0)
            csvcleanfile.truncate()        
            line = csvfile.readline();
            #print(str(line))
            line = line.replace(";" + chr(10), chr(10))
            #print(str(line))
            stripline = line.strip().replace('\00','')
            while line:        
                csvcleanfile.write(stripline.replace(',','.') +"\n")   
                line = csvfile.readline().replace('\00','')
                line = line.replace(";" + chr(10), chr(10))
                stripline = line.strip().replace('\00','')
    rownum = 0
    with open(csvtempfilename, "rt") as csvfile:
        reader = csv.reader(csvfile, delimiter=';', quotechar='"')        
        for row in reader:        
            is_valid_row = 1
            if (rownum > 0):
                if (is_valid_row > 0):
                    alen = len(row)        
                    rows.append(row)
                else:
                    print("Warning: Skipped malformed row #" + rownum)
            else:
                header = row

            rownum = rownum+1;
    os.remove(csvtempfilename)    
    first_row = rows[0];
    last_row = rows[len(rows)-1]
    log_info = [csvfile, first_row[0], last_row[0]]
    
    return header, rows, log_info
    
def import_ext_logfiles( csvfilename ):
    "Liest eine Logdatei im CSV-Format ein"        
    # Sanitize file (remove whitespace from each row and replace "," with "."    
    csvtempfilename = csvfilename.replace(".csv", "_clean.csv");
    print("Sanitizing '" + str(csvfilename) + "' to '" + csvtempfilename + "'.")    
    with open(csvfilename, "rt+") as csvfile:
        with open(csvtempfilename, "wt+") as csvcleanfile:           
            csvcleanfile.seek(0)
            csvcleanfile.truncate()        
            line = csvfile.readline();
            dummy = csvfile.readline();
            dummy = csvfile.readline();
            dummy = csvfile.readline();
            dummy = csvfile.readline();
            #print(str(line))
            line = line.replace(" Â°C", "")            
            line = line.replace(",", ";")
            #print(str(line))
            stripline = line.strip().replace('\00','')
            while line:        
                csvcleanfile.write(stripline +"\n")   
                line = csvfile.readline()
                line = line.replace(" Â°C", "")
                line = line.replace(",", ";")
                stripline = line.strip().replace('\00','')
    rownum = 0
    rows = [];
    header = [];
    with open(csvtempfilename, "rt") as csvfile:
        reader = csv.reader(csvfile, delimiter=';', quotechar='"')        

        for row in reader:        
            if (rownum > 0):
                alen = len(row) 
                #print(str(row))                
                rows.append(row)
            rownum = rownum+1;
        else:
            header = row;
    
    for row in rows:
        del row[0]
    
    os.remove(csvtempfilename)
    return header, rows
        
    
def import_valve_log( csvfilename ):
    "Liest eine Logdatei mit SchaltvorgÃ¤ngen des Magnetventils im CSV-Format ein"
    rows = []
    
        # Sanitize file (remove trailing whitespace and replace "," with "."    
    csvtempfilename = csvfilename.replace(".csv", "_clean.csv");
    with open(csvfilename, "rt+") as csvfile:
        with open(csvtempfilename, "wt+") as csvcleanfile:           
            text = csvfile.read().rstrip().replace(',', '.')
            csvcleanfile.seek(0)
            csvcleanfile.truncate()
            csvcleanfile.write(text)   
    
    with open(csvtempfilename, "rt") as csvfile:
        reader = csv.redaer(csvfile, delimiter=';', quotechar='"')
        for row in reader:
            alen = len(row)
            field = row[1]
            vol = locale.atof(row[1], decimal.Decimal)
            print("Gasvolumen: " + str(vol))
    os.remove(csvtempfilename)
    return rows
    
    

def sort(config, header, rows):
    "Sortiert die inhalte mehrerer CSV-Dateien chronologisch"
    
    date_fmt = config['formats'].get('date', '%d.%m.%Y %H:%M:%S')

    
    rows_dict = {}
    rows_merged = []
    
    for row in rows[0:len(rows)]:
        row_time = row[0]    
        row_tm = datetime.strptime(row_time, date_fmt)
        rows_dict[row_tm] = row
        
    keys = []
    for key in rows_dict:
        keys.append(key);

    keys = sorted(keys);

    for key in keys:
        row = rows_dict[key]    
        rows_merged.append(row)
        
    #logexport("data_rows_merged.csv", rows_merged);

    #print("Merged row count: " + str(len(rows_merged)))
        
    return rows_merged
    
def clip(start_tm, end_tm, step_tm, rows_in, date_fmt):
    ""
    rows_out    = []
    
    lower_bound_tm = start_tm ;
    first_data_row = rows_in[1];
    first_time = first_data_row[0];
    first_tm = datetime.strptime(first_time, date_fmt);
    
    last_data_row = rows_in[len(rows_in)-1];
    last_time = last_data_row[0];
    last_tm = datetime.strptime(last_time, date_fmt);
    
    # Clip start and end times to avoid unneccesary looping    
    if start_tm < first_tm:
        start_tm = first_tm
        print("Start time (clipped): " + str(start_tm))
    else:
        print("Start time       : " + str(start_tm))
        
    if end_tm > last_tm:
        end_tm = last_tm
        print("End time (clipped): " + str(end_tm))
    else:
        print("End time         : " + str(end_tm))
    
    # Processing stuff in a german locale (',' instead of '.') is possibly malfunctioning
    # on different platforms (f.e. OSX) since the handling is very platform specific 
    # (and I can only test on windows)
    # Needs some homebrew solution, also it would probably be easier to 
    # avoid creating this situation on the source side by using the dot notation.
    locale.setlocale(locale.LC_NUMERIC, 'German_Germany.1252')
    rows_out.append(rows_in[0])
    print("HEADER: " + str(rows_in[0]));    
    while lower_bound_tm < end_tm:
        upper_bound_tm = lower_bound_tm + step_tm;    
        print("=== lower_bound = " + str(lower_bound_tm))
        row_count = 0;
        rows_sum = [0] * len(rows_in[0]);
        has_row = False;
        for row in rows_in[0:len(rows_in)]:        
            cur_tm = datetime.strptime(row[0], date_fmt)    
            
            if cur_tm >= lower_bound_tm and cur_tm >= start_tm and cur_tm < upper_bound_tm and cur_tm < end_tm:                
                has_row = True
                rows_sum[0] = row[0]
                for iRow in range(1, len(row)):
                    rows_sum[iRow] += locale.atof(row[iRow], decimal.Decimal)            
                row_count = row_count + 1;        
        
        print("=== upper_bound = " + str(upper_bound_tm))    
        if has_row == True:
            rows_mean = [rows_sum[0]] + [x / row_count for x in rows_sum[0:len(rows_sum)]]
            rows_out.append(rows_mean)
            
        lower_bound_tm = upper_bound_tm;
    #print("======== MERGED ========")
    #for row in rows_out:
    #    print(row)
    return rows_out    

def resample(config, header, rows):
    ""
    rows_resampled    = []
    header_row_out = [];
    header_row_out.append(header);


    date_fmt = config['formats'].get('date', '%d.%m.%Y %H:%M:%S')
    print("... using date format spec: " + str( date_fmt ));
    
    step_time_abs = config['resampling'].get('dt', '00:00:01')
    step_tm_abs = datetime.strptime(step_time_abs, '%H:%M:%S')
    step_tm = step_tm_abs - datetime.strptime("00:00:00", '%H:%M:%S')
    
    print("... new datapoint interval: " + str(step_tm_abs));

    start_time = config['resampling'].get('tstart', '01.01.0001 00:00:00');
    start_tm = datetime.strptime(start_time, date_fmt);    
    end_time = config['resampling'].get('tend', '31.12.2100 23:59:59');
    end_tm = datetime.strptime(end_time, date_fmt);

    first_data_row = rows[0];
    first_time = first_data_row[0];    
    first_tm = datetime.strptime(first_time, date_fmt);
    
    last_data_row = rows[len(rows)-1];
    last_time = last_data_row[0];
    last_tm = datetime.strptime(last_time, date_fmt);
    
    # Clip start and end times to avoid unneccesary looping    
    if start_tm < first_tm:
        start_tm = first_tm
        print("...using experiment start time: " + str(start_tm))
    else:
        print("...using start time from configuration: " + str(start_tm))
        
    if end_tm > last_tm:
        end_tm = last_tm
        print("...using experiment end time: " + str(end_tm))        
    else:
        print("...using end time from configuration: " + str(end_tm))

        
    
    # Processing stuff in a german locale (',' instead of '.') is possibly malfunctioning
    # on different platforms (f.e. OSX) since the handling is very platform specific 
    # (and I can only test on windows)
    # Needs some homebrew solution, also it would probably be easier to 
    # avoid creating this situation on the source side by using the dot notation.
    #locale.setlocale(locale.LC_NUMERIC, 'German_Germany.1252')
    #rows_resampled.append(rows_in[0])
    #print("HEADER: " + str(rows_in[0]));    

    col_count = len(rows[0]);
    nan_row = [""] + [(str("NaN")) for i in range(col_count)]
    #print("Column count: " + str(col_count));
    #os.system("pause")
    
    lower_bnd_tm = start_tm
    upper_bnd_tm = lower_bnd_tm + step_tm
    
    

    last_progress = -1;
    progress = 0;
    progress_count = 0
    progress_total = len(rows)
    row_count = 0;
    row_sum = [0] * len(rows[0]);
    has_row = False;
    for row in rows[0:len(rows)]:    
        
        progress_count = progress_count + 1;
        
        progress = round(100 * progress_count / progress_total);
        if (progress != last_progress):
            print("...progress: " + str(progress) + " % \r", end='');
            last_progress = progress;
    

        cur_tm = datetime.strptime(row[0], date_fmt)    
        if cur_tm <= end_tm and cur_tm > lower_bnd_tm and cur_tm <= upper_bnd_tm:
            has_row = True         
            row_sum[0] = row[0]
            row_count = row_count + 1;
            for iRow in range(1, len(row)):
                row_sum[iRow] += locale.atof(row[iRow], decimal.Decimal)                
                        
        if cur_tm >= upper_bnd_tm:
            intermediate_tm = lower_bnd_tm + ((upper_bnd_tm - lower_bnd_tm) / 2)
            lower_bnd_tm = upper_bnd_tm
            upper_bnd_tm = lower_bnd_tm + step_tm

            if has_row == True:                               
                row_mean = [datetime.strftime(intermediate_tm, date_fmt_intern)] + [field / row_count for field in row_sum[1:len(row_sum)]]                            
            else:
                row_mean = [datetime.strftime(intermediate_tm, date_fmt_intern)] + ["NaN" for field in row_sum[1:len(row_sum)]]
                print("WARNING: No data in slot " + str(lower_bnd_tm) + " - " +str(upper_bound_tm) + ".")

            rows_resampled.append(row_mean)            
            row_sum = [0] * len(rows[0]);
            row_count = 0
            has_row = False
                

    return start_tm, end_tm, header_row_out, rows_resampled    
    


def resample2(config, header, rows):
    ""
    rows_resampled    = []
    header_row_out = header;
    

    date_fmt = config['formats'].get('date', '%d.%m.%Y %H:%M:%S')
    print("... using date format spec: " + str( date_fmt ));
    
    step_time_abs = config['resampling'].get('dt', '00:00:01')
    step_tm_abs = datetime.strptime(step_time_abs, '%H:%M:%S')
    step_tm = step_tm_abs - datetime.strptime("00:00:00", '%H:%M:%S')
    
    print("... new datapoint interval: " + str(step_tm_abs));

    start_time = config['resampling'].get('tstart', '01.01.0001 00:00:00');
    start_tm = datetime.strptime(start_time, date_fmt);    
    end_time = config['resampling'].get('tend', '31.12.2100 23:59:59');
    end_tm = datetime.strptime(end_time, date_fmt);

    first_data_row = rows[0];
    first_time = first_data_row[0];    
    first_tm = datetime.strptime(first_time, date_fmt);
    
    last_data_row = rows[len(rows)-1];
    last_time = last_data_row[0];
    last_tm = datetime.strptime(last_time, date_fmt);
    
    # Clip start and end times to avoid unneccesary looping    
    if start_tm < first_tm:
        start_tm = first_tm
        print("...using experiment start time: " + str(start_tm))
    else:
        print("...using start time from configuration: " + str(start_tm))
        
    if end_tm > last_tm:
        end_tm = last_tm
        print("...using experiment end time: " + str(end_tm))        
    else:
        print("...using end time from configuration: " + str(end_tm))

    interval_list = [];

    cur_tm = start_tm;
    while cur_tm < end_tm:
        lower_bound_tm = cur_tm
        cur_tm = cur_tm + step_tm
        upper_bound_tm = cur_tm
        interval_list.append([pd.to_datetime(lower_bound_tm), pd.to_datetime(upper_bound_tm)])

    df = pd.DataFrame.from_records(rows, coerce_float=True);
    df.columns = header;
    df['count'] = pd.Series(["1" for x in range(len(df.index))])
    df['Date'] = pd.to_datetime(df['Date'], format=date_fmt);
    #print(df);

    data_cols = [i for i in df.columns if i not in ["Date"]]
    for col in data_cols:
        df[col]=pd.to_numeric(df[col])

    df2 = df.resample(step_tm, on='Date').sum();

    data_cols = [i for i in df.columns if i not in ["Date", "count"]]
    df2.loc[:, data_cols] = df2.loc[:, data_cols].div(df2['count'], axis=0)
    df2 = df2.drop(labels=['count'], axis=1);

    print(df2);
    df2.insert(0, 'Date', df2.index);

    rows_resampled = df2.values.tolist();
    rowsxx = [];
    row_idx = 0;
    rowx = rows_resampled[2];
    for row in rows_resampled:
        row_idx = row_idx + 1;1
        x = row[0].strftime(date_fmt_intern)
        row[0] = x;
        rowsxx.append(row);
    
    first_row = rowsxx[0];
    print(first_row);
    return start_tm, end_tm, header_row_out, rowsxx    
    
def insert_runtime_column(config, header_in, rows_in, first_tm):
    "Berechnet die Laufzeit ab startzeit und trÃ¤gt diese als neue Spalte ein"
    
    header_out = [];
    header_out.append("Time");
    for col in header_in:
        header_out.append(col);

    rows_out = []            

    for row in rows_in[0:len(rows_in)]:
        data_time = row[0]
        data_tm = datetime.strptime(data_time, date_fmt_intern)
        delta_tm = data_tm - first_tm
        duration_mins = delta_tm.days*24*60 + delta_tm.seconds / 60;
        row_out = [str(duration_mins)] + row 
        rows_out.append(row_out)
        
    
    return header_out, rows_out
    
def nearest_value(items, pivot):
    return min(items, key=lambda x: abs(x - pivot))    

def nearest_index(items, pivot):
    time_diff = np.abs([date - pivot for date in items])
    return time_diff.argmin(0)
        
    
def insert_ext_measurement_column(config, header_in, rows_in, ext_rows_in):
    "FÃ¼gt eine Spalte mit externen messungen ein"
    rows_out = []
    date_rows = []        
    header_row_out = [];
    for col in header_in:        
        header_row_out.append(col);

    value_rows = ext_rows_in
    ext_col_idx = 1;
    ext_first_row = ext_rows_in[0];
    for col in ext_first_row:
        header_row_out.append("EXT " + str(ext_row_idx))
        ext_row_idx = ext_row_idx + 1;

    for row in ext_rows_in:        
        tm_str = row[0]        
        tm = datetime.strptime(tm_str, date_fmt_intern)
        date_rows.append(tm);
                
    for row in rows_in[1:len(rows_in)]:
    
        tm_str = row[1]
        #print (tm_str)
        tm = datetime.strptime(tm_str, date_fmt_intern)
        closest_index = nearest_index(date_rows, tm)
        closest_value = nearest_value(date_rows, tm)
        #print("TM: " + str(tm) + " cv: " + str(closest_value) + " ci: " + str(closest_index))
        #print(str(len(ext_rows_in)))
        #closest_date = ext_rows_in[closest_index][1]
        
        
        ext_nearest_row = ext_rows_in[closest_index];
        #print(str(ext_nearest_row))        
        ext_value = ext_rows_in[closest_index][1]
        #print(str(ext_value))
        row_out = row + [str(ext_value)]
        #print(str(row_out))
        rows_out.append(row_out)
    return header_row_out, rows_out

class DatetimeValueTuple:
    """Container für Tupel von Zeitstempel und Wert"""
    def __init__(self, time, value):
        self.tm = time
        self.v = value


def is_in_window(window_start_tm, x):
    if (x.tm < window_start_tm):
        return True
    return False
    

def insert_volume_flow_column(config, header_in, rows_in, valve_rows_in, start_tm, end_tm):
    "Berechnet das wÃ¤hrend der Laufzeit injezierte gasvolumen"
    
    print("Calculating volume flow....")
    
    logexport("data_valve_rows.csv", header_in, valve_rows_in)


    # ensure proper chronological ordering of the valve records
    valve_rows_dict = {}
    valve_rows_sorted = []
    date_fmt = config['formats'].get('date', '%d.%m.%Y %H:%M:%S')

    for valve_row in valve_rows_in[0:len(valve_rows_in)]:
        valve_row_time = valve_row[0]    
        valve_row_tm = datetime.strptime(valve_row_time, date_fmt)
        valve_rows_dict[valve_row_tm] = valve_row
            
    keys = []
    for key in valve_rows_dict:
        keys.append(key);

    keys = sorted(keys);

    for key in keys:
        valve_row = valve_rows_dict[key]    
        valve_rows_sorted.append(valve_row)

    valve_rows_in = valve_rows_sorted
    
    # User supplied co2 volume per injection millisecond
    co2_volume_per_msec_str = config['resampling'].get('dV_co2', '2.5')
    co2_volume_per_msec = locale.atof(co2_volume_per_msec_str)
    print ("Assuming a CO2 injection volume per millisecond of :" + str(co2_volume_per_msec))
    # User supplied weight per volume of co2
    co2_volume_constant_str = config['resampling'].get('dLtog_co2', config['resampling'].get('dLtog_vo2', '1.7777'))    
    co2_volume_constant = locale.atof(co2_volume_constant_str)
    print ("Assuming a CO2 weight-to-volume ratio of :" + str(co2_volume_constant) + "g/L")

    # User supplied loss-of-co2 per hour

    
    co2_volume_loss_per_hour = 0.0;
    co2_volume_equiv_capacity = 0.0;
    # User supplied conversion rate (g C / g CO2)
    co2_to_c_factor = 1.0;

    if config.has_section('bookkeeping'):
        co2_volume_loss_per_hour = float(config['bookkeeping'].get('dCO2VolumeLossPerHour', 0.0));
        co2_volume_equiv_capacity = float(config['bookkeeping'].get('dCO2VolumeEquivCapacity', 0.0));
        co2_to_c_factor = 12.0/44.0;
    co2_volume_loss_per_sec = float(co2_volume_loss_per_hour) / (60 * 60);
    print ("Assuming a loss of CO2 volume per hour of :" + str(co2_volume_loss_per_hour) + "ml/h")
    print ("...Resulting in a loss of CO2 volume per second of :" + str(co2_volume_loss_per_sec) + "ml/s")    
    print ("Assuming a CO2 capacity of :" + str(co2_volume_equiv_capacity) + "g")

    

    valve_time_total_msec = 0
    valve_cycle_count =    1
    valve_cycle_time_msec = 0
    valve_time_msec = 0
    valve_total_time_msec = 0
    valve_cycle_volume = 0
    valve_volume = 0
    valve_total_volume = 0
    
    co2_factor_str = config['resampling'].get('dV_co2', '2')
    co2_factor = locale.atof(co2_factor_str)
    rows_out = []
    
    date_fmt = config['formats'].get('date', '%d.%m.%Y %H:%M:%S')

    header_row_out =[];
    header_row_out = \
        header_in \
        + ['valve_total_time'] \
        + ['valve_time'] \
        + ['valve_cycle_count'] \
        + ['valve_mass'] \
        + ['valve_total_mass'] \
        + ['loss_total_mass'] \
        + ['fixated_total_mass'] \
        + ['mass flow rate /h'] \
        + ['date'] \

    iRowFrom = 0
    iRowTo = 1
    iValveRowFrom = 1
    valve_gas_volume_sum = 0
    
    valve_total_time_msec = 0
    valve_total_volume = 0
    valve_total_bin_count = 0
    valve_total_cycle_count = 0
    
    
    #start_time = config['resampling'].get('tstart', '01.01.0001 00:00:00');
    #start_tm = datetime.strptime(start_time, date_fmt);
    #end_time = config['resampling'].get('tend', '31.12.2100 23:59:59');
    #end_tm = datetime.strptime(end_time, date_fmt);

    injectionsinwindow = list();
    window_td = timedelta(seconds=(3600));
    

    loss_volume_total = 0
    for row in rows_in[1:len(rows_in)]:
        #reset integration variables and counters
        
        valve_bin_volume = 0
        valve_bin_time_msec = 0
        valve_bin_cycle_count = 0
        
        row_time = row[1]
        row_tm = datetime.strptime(row_time, date_fmt_intern)        
        if row_tm >= start_tm and row_tm < end_tm:
            #extract bin start and end times
            tm_from_str = rows_in[iRowFrom][1]    
            tm_to_str = rows_in[iRowTo][1]
            tm_from = datetime.strptime(tm_from_str, date_fmt_intern);
            tm_to = datetime.strptime(tm_to_str, date_fmt_intern);

            delta_tm = tm_to - start_tm;
            size_before = len(injectionsinwindow)
            # loop over valve events
            tm = None
            if (iValveRowFrom < len(valve_rows_in)):
                
                
                valve_row = valve_rows_in[iValveRowFrom]
                tm_str = valve_row[0]
                tm = datetime.strptime(tm_str, date_fmt)
                #loop over remaining valve events, terminate if valve event is outside bin time
                while ((iValveRowFrom < len(valve_rows_in)) and (tm < tm_to)):
                    valve_cycle_time_msec = 0
                    valve_cycle_volume = 0
                    
                    # extract duration from string ("open for ... ms"), 
                    cycle_tm_field_str = valve_row[0]
                    cycle_tm_field = datetime.strptime(cycle_tm_field_str, date_fmt)
                    # only consider lines with timestamps after the start time
                    if cycle_tm_field >= start_tm:

                        
                        field = valve_row[1]        
                        num_str = field.replace("open", "").replace("for", "").replace("ms", "").replace(" ", "")
                        # convert to number 
                        valve_cycle_time_msec = int(num_str);           
                        #calculate flow volume per-cycle
                        valve_cycle_volume = co2_volume_per_msec * valve_cycle_time_msec
                        
                        #integrate values over bin
                        valve_bin_volume += valve_cycle_volume
                        valve_bin_time_msec += valve_cycle_time_msec
                        valve_bin_cycle_count = valve_bin_cycle_count + 1;

                        
                        # insert into deque
                        injectionsinwindow.append(DatetimeValueTuple(cycle_tm_field, valve_cycle_volume))                      

                        #co2_amount_total_L = co2_volume_per_msec * valve_time_total_msec * 0.001
                        #co2_amount_total_g = co2_volume_constant * co2_amount_total_L
                        #print ("(Cycle #" + str(valve_bin_cycle_count) + ", " + str(cycle_tm_field_str) + ") dur=" + str(valve_cycle_time_msec) + " ms, V=" + str(valve_cycle_volume) +" mL")
                        # next cycle
                        iValveRowFrom = iValveRowFrom + 1
                        if (iValveRowFrom < len(valve_rows_in)):
                            valve_row = valve_rows_in[iValveRowFrom]
                            tm_str = valve_row[0]
                            tm = datetime.strptime(tm_str, date_fmt)
                    else:
                        iValveRowFrom = iValveRowFrom + 1                            #integrate values total
                        if (iValveRowFrom < len(valve_rows_in)):
                            valve_row = valve_rows_in[iValveRowFrom]
                            tm_str = valve_row[0]
                            tm = datetime.strptime(tm_str, date_fmt)
            # Compute earliest and latest time stamps in window (row_tm - 1 hour : row_tm)
            if tm is None:
                continue
            window_end_tm = tm
            window_start_tm = window_end_tm - window_td;
            size_during = len(injectionsinwindow)
            injectionsinwindow = [x for x in injectionsinwindow if not is_in_window(window_start_tm, x)]
            size_after = len(injectionsinwindow)
            current_volume_rate = 0
            #print("In window: " + str(size_before) + " " + str(size_during) + " " + str(size_after)+ "\r\n")
            for x in injectionsinwindow:
                #print("@"+str(x.tm)+": " + str(x.v) + "\r\n")    
                current_volume_rate += x.v            
            
                                          
            valve_total_time_msec += valve_bin_time_msec
            valve_total_volume += valve_bin_volume
            valve_total_cycle_count += valve_bin_cycle_count
            #increment bin counter for printing
            valve_total_bin_count += 1
            #print ("(Bin #" + str(valve_total_bin_count) + " FROM: " + str(tm_from) + " TO " + str(tm_to) + ") dur=" + str(valve_bin_time_msec) + " ms, Vrate=" + str(current_volume_rate) + " V=" + str(valve_bin_volume) + " L, cycles=" + str(valve_bin_cycle_count))
            #if (valve_volume > 0):
            added_volume_total = valve_total_volume;
            time_sec = delta_tm.total_seconds();
            loss_volume_total = time_sec * co2_volume_loss_per_sec;
            fixated_volume_total = max(0.0, added_volume_total - (loss_volume_total + co2_volume_equiv_capacity));
            #print("(t) t=" + str(time_sec) + "s, Va=" + str(added_volume_total) + " mL, Vl=" + str(loss_volume_total) + " mL, Vf=" + str(fixated_volume_total))            
            #print("(Total) t=" + str(valve_total_time_msec) + "ms, V=" + str(valve_total_volume) + " mL, cycles=" + str(valve_total_cycle_count))            
            row_out = \
                row \
                + [str(valve_total_time_msec)] \
                + [str(valve_bin_time_msec)] \
                + [str(valve_total_cycle_count)] \
                + [str(valve_bin_volume         * co2_volume_constant * co2_to_c_factor)] \
                + [str(valve_total_volume       * co2_volume_constant * co2_to_c_factor)] \
                + [str(loss_volume_total        * co2_volume_constant * co2_to_c_factor)] \
                + [str(fixated_volume_total     * co2_volume_constant * co2_to_c_factor)] \
                + [str(current_volume_rate      * co2_volume_constant * co2_to_c_factor)] \
                + [str(tm)]
            rows_out.append(row_out)
            iRowFrom = iRowFrom + 1
            iRowTo = iRowTo + 1

    return header_row_out, rows_out
    
    
    
def select_column_list(rows_in, column_index_list):
    ""
    rows_out = []    
    for row in rows_in[0:len(rows_in)]:
        row_out = [row[column] for column in column_index_list]
        rows_out.append(row_out)
    
    return rows_out

    common_header = [];
def import_logfiles(csv_files, rows, headers):

    common_header = [];

    log_infos = [];
    for csv_file in csv_files:    
        print("* " + str(csv_file), end='')    

        file_header = [];
        file_rows = [];

        file_header, file_rows, log_info= logimport(csv_file)
        if (len(common_header) == 0):
            common_header = file_header;
        else:
            if(str(common_header) != str(file_header)):
                print("\r\n !!! WARNING: Inconsistent file headers")           
        
        first_data_row = file_rows[1];
        last_data_row = file_rows[len(file_rows)-1];
        print(" [" + str(len(file_rows)-1) + " rows]", end='')
        print(" [" + str(first_data_row[0]) + " - " + str(last_data_row[0]) + "]");

        rows.extend(file_rows[0:len(file_rows)])
        headers.append(file_header)
        log_infos.append(log_info)

                
    return log_infos

    
def main_analytics(config_file, data_dir):
    "Einsprungpunkt"
    #if (len(sys.argv) < 2):
    #    print("Missing argument: please specify a configuration file (.ini)")
    #    sys.exit()
    #config_file = sys.argv[1];
    
    print("Using config:" + config_file)
    config = configparser.ConfigParser(interpolation=None)
    with open(config_file, 'r', encoding='utf-8') as f:
        config.read_file(f)


    config_values_file_pattern = config['source'].get('file_pattern_values', '_values.csv')
    config_valve_file_pattern = config['source'].get('file_pattern_valve', '_valve.csv')
    config_heating_file_pattern = config['source'].get('file_pattern_heating', '_heating.csv')

    config_source_path = config['source'].get('source_dir', '.')

    input_values_files = [];
    input_valve_files = [];
    input_heating_files = [];

    csv_files = [];

    # If the user specified any csv file, then use that (backwards compatibility)
    value_csv_files_str = config['source'].get('value_csv', '')    
    valve_csv_files_str = config['source'].get('valve_csv', '')
    heating_csv_files_str = config['source'].get('heating_csv', '')
    #
    if data_dir is not None:#        
        #prepend data_dir to all elements of valve_csv_files
        if value_csv_files_str != "":
            value_csv_files_str = ",".join([data_dir + "/" + x for x in value_csv_files_str.split(",")])
        if valve_csv_files_str != "":
            valve_csv_files_str = ",".join([data_dir + "/" + x for x in valve_csv_files_str.split(",")])
        if heating_csv_files_str != "":
            heating_csv_files_str = ",".join([data_dir + "/" + x for x in heating_csv_files_str.split(",")])

    # Otherwise, enumerate files
    # if value_csv_files_str == "":
    #     for entry in os.scandir(config_source_path):
    #         if entry.is_file and entry.name.endswith(config_values_file_pattern):            
    #             csv_files.append(str(entry.path))
    #     # enumerate files
    #     for values_file in csv_files:
    #         input_values_file = values_file.replace(config_values_file_pattern, config_values_file_pattern);
    #         input_valve_file = values_file.replace(config_values_file_pattern, config_valve_file_pattern);
    #         input_heating_file = values_file.replace(config_values_file_pattern, config_heating_file_pattern);
    #         if (os.path.exists(input_values_file)):
    #             input_values_files.append(input_values_file);
    #         else:
    #             print("Error: VALUES Source file does not exists: " + input_valve_file);
    #             exit(0);

    #         if (os.path.exists(input_valve_file)):            
    #             input_valve_files.append(input_valve_file);
    #         else:
    #             print("Info: VALVE Source file does not exists: " + input_valve_file);

    #         if (os.path.exists(input_heating_file)):
    #             input_heating_files.append(input_heating_file);
    #         else:
    #             print("Info: HEATING Source file does not exists: " + input_valve_file);        

    
    
    # Assign depending on wheter we had a list of files or use the enumerated option
    if value_csv_files_str != "":
        print("From files: " + str(value_csv_files_str))
        value_csv_files = value_csv_files_str.split(',')
    else:
        value_csv_files = input_values_files;

    if (len(value_csv_files) == 0):
        print("Error: No source VALUES files detected.");




    if(value_csv_files_str != "" and valve_csv_files_str != ""):
        print("From files: " + str(valve_csv_files_str))
        valve_csv_files = valve_csv_files_str.split(',')
    else:
        valve_csv_files = input_valve_files
    

    
    if (value_csv_files_str != "" and heating_csv_files_str != ""):
        print("From files: " + str(heating_csv_files_str))
        heating_csv_files = heating_csv_files_str.split(',')
    else:
        heating_csv_files = input_heating_files;
    

    date_fmt = config['formats'].get('date', '%d.%m.%Y %H:%M:%S')
    print("Date format spec: " + str( date_fmt ));

    print("\r\n\r\n");

    print("Reading [EXT]");
    ext_csv_files_str = config['source'].get('tinytag_csv', '');
    ext_rows = []
    ext_headers = []      
    if (ext_csv_files_str != ""):
        print("From files: " + str(ext_csv_files_str))
        ext_csv_files = ext_csv_files_str.split(',')
        ext_rows = import_ext_logfiles(ext_csv_files[0]);


    print("Reading [VALVE]");        
    # User supplied co2 volume per injection millisecond
    co2_volume_per_msec_str = config['resampling'].get('dV_co2', '2.5')
    co2_volume_per_msec = locale.atof(co2_volume_per_msec_str)
    print ("Assuming a CO2 injection volume per millisecond of :" + str(co2_volume_per_msec))
    # User supplied weight per volume of co2
    co2_volume_constant_str = config['resampling'].get('dLtog_vo2', '1.7777')
    co2_volume_constant = locale.atof(co2_volume_constant_str)
    print ("Assuming a CO2 weight-to-volume ratio of :" + str(co2_volume_constant) + "g/L")
        
    
    valve_rows = []
    valve_headers = []    
    valve_infos = import_logfiles(valve_csv_files, valve_rows, valve_headers);

    valve_time_total_msec = 0
    valve_cycle_count = 1
    valve_interval_total_s = 0;
    valve_interval_night_threshold = int(config['resampling'].get('co2_night_intervall_threshold', '1000'))

    start_time = config['resampling'].get('tstart', '01.01.0001 00:00:00');
    start_tm = datetime.strptime(start_time, date_fmt);
    end_time = config['resampling'].get('tend', '31.12.2100 23:59:59');
    end_tm = datetime.strptime(end_time, date_fmt);



    first_row = valve_rows[0];
    #print("VALVE_FIRST_ROW: " + str(first_row))
    last_cycle_time = first_row[0];
    #print("VALVE_FIRST_CYCLE_TIME: " + str(last_cycle_time))
    last_cycle_tm = datetime.strptime(last_cycle_time, date_fmt)
    #print("VALVE_FIRST_CYCLE_TM: " + str(last_cycle_tm))
    for row in valve_rows:
        this_cycle_time = row[0];
        this_cycle_tm = datetime.strptime(this_cycle_time, date_fmt)
        if this_cycle_tm < start_tm or this_cycle_tm >= end_tm:
            print(str(this_cycle_time) + ": skipped");
        if this_cycle_tm >= start_tm and this_cycle_tm < end_tm:
            interval = this_cycle_tm - last_cycle_tm;
            last_cycle_tm = this_cycle_tm;
            valve_interval_s = interval.days*24*60*60 + interval.seconds;
            if valve_interval_s < valve_interval_night_threshold:
                            valve_interval_total_s += valve_interval_s
            num_str = row[1].replace("open", "").replace("for", "").replace("ms", "").replace(" ", "")
            valve_cycle_count = valve_cycle_count + 1;
            valve_time_current_msec = int(num_str)    
            valve_time_total_msec += valve_time_current_msec
        
    valve_interval_total_s /= valve_cycle_count;
        
    valve_time_total_sec = float(valve_time_total_msec) / 1000
    valve_time_avg = (float(valve_time_total_msec) / float(valve_cycle_count))
    co2_amount_total_L = co2_volume_per_msec * valve_time_total_msec * 0.001
    co2_amount_total_g = co2_volume_constant * co2_amount_total_L
    
    print (str.format("Average CO2 injection interval: {:.2f} ", float(valve_interval_total_s)))
    print(str.format("Summed CO2 injection duration: {:.2f} secs",  float(valve_time_total_sec )))
    print(str.format("Average CO2 injection duration: {:.2f} msecs", float(1000*valve_time_total_sec) / float(valve_cycle_count)))
    print(str.format("CO2 injection cycle count: {:.0f}", float(valve_cycle_count)))

    print(str.format("Amount CO2 injected [L]: {:.2f} L", float(co2_amount_total_L)))
    print(str.format("Amount CO2 injected [g]: {:.2f} g", float(co2_amount_total_g)))

    print("\r\n\r\n");

    print("Reading [VALUE]");
    value_rows = []
    value_headers = []
    value_infos = import_logfiles(value_csv_files, value_rows, value_headers);
    if "time elapsed" not in value_headers[0]:
        print("WARNING: No time elapsed column found in [VALUE] log file. Appending fake column. May take a while.")
        value_headers[0].append("time elapsed")
        i = 0
        for row in value_rows:
            row.append(str(i+1))
            i = i+1

    if "box_humidity" not in value_headers[0]:
        print("WARNING: No box_humidity column found in [VALUE] log file. Appending fake column. May take a while.")
        value_headers[0].append("box_humidity")
        i = 0
        for row in value_rows:
            row.append(0)
            i = i+1
    
    if "box_temperature" not in value_headers[0]:
        print("WARNING: No box_temperature column found in [VALUE] log file. Appending fake column. May take a while.")
        value_headers[0].append("box_temperature")
        i = 0
        for row in value_rows:
            row.append(0)
            i = i+1        

    print("--- Ensuring chronologic order ---")    
    rows_ordered = sort(config, value_headers[0], value_rows)
    value_rows = rows_ordered;
    print("...Total number of rows: " + str(len(value_rows)))

    first_data_row = rows_ordered[1];
    header_row = value_headers[0];

    print("...number of columns: " + str(len(first_data_row)))
    print("...contained columns [" + str(len(first_data_row)) + "]: ");
    

    print("--- Resampling rows ---")
    start_tm, end_tm, header_row2, value_rows = resample2(config, header_row, value_rows)
    print("...Total number of rows after resampling: " + str(len(value_rows)))


    print("--- Adding runtime column ---")
    header_row, value_rows = insert_runtime_column(config, header_row2, value_rows, start_tm)

    print("--- Adding volume flow and growth estimate columns ---")
    header_row, value_rows = insert_volume_flow_column(config, header_row, value_rows, valve_rows, start_tm, end_tm);
    
    if (ext_csv_files_str != ""):
        print("--- Adding external columns ---")
        header_row, value_rows = insert_ext_measurement_column(config, header_row, value_rows, ext_rows);
    
    #logexport("data_final.csv", rows_final);
    first_row = value_rows[0]
    last_row = value_rows[len(value_rows)-1];
    #print("LAST_ROW: " + str(last_row))
    #valve_time_total_msec = last_row[11];
    #co2_amount_total_ml = last_row[14];    
    heating_time_total = 0
    heating_cycle_count = 0

    print("\r\n\r\n");
    
    print("Reading [HEATING]");    
    heating_rows = []
    heating_headers = []    
    import_logfiles(heating_csv_files, heating_rows, heating_headers);

    heating_time_total = 0
    heating_cycle_count = 0

    heating_start_tm_str = first_row[1]
    print("...using start time: " + str(heating_start_tm_str))
    heating_start_tm = datetime.strptime(heating_start_tm_str, date_fmt_intern)
    heating_end_tm_str = last_row[1]
    print("...using end time: " + str(heating_end_tm_str))
    heating_end_tm = datetime.strptime(heating_end_tm_str, date_fmt_intern)
    
    hasFirstTime = 0
    lastState = "OFF"
    heating_time_total = 0
    heating_cycle_count = 1    
    for row in heating_rows:
        data_time = row[0]
        state = row[1]
        
        data_tm = datetime.strptime(data_time, date_fmt)
        if (data_tm >= heating_start_tm and data_tm < heating_end_tm):
            #print("data_time: " + str(data_time))
            if (hasFirstTime==1):
                delta_tm = data_tm - prev_tm
                delta_tm_mins = duration_mins = delta_tm.days*24*60 + delta_tm.seconds / 60;
                if(state == "on"):
                    heating_cycle_count = heating_cycle_count + 1            
                    heating_time_total = heating_time_total + delta_tm_mins;
                    prev_tm = data_tm;
            
            if (hasFirstTime==0):
                if (state == "on"):
                    hasFirstTime = 1
                    prev_tm = data_tm;
            
    heating_time_avg = 0
    
    if (heating_cycle_count > 0):
        heating_time_avg = heating_time_total / heating_cycle_count    
        print(str.format("Heating: Total {:.2f} mins, {} cycles, Avg {:.2f} mins\n", heating_time_total, heating_cycle_count, heating_time_total / heating_cycle_count))    
    
    
    
    print("--- Exporting plot script ---");
    write_gnuplot_script(
        config, 
        value_rows, 
        header_row, 
        value_infos,
        start_tm,
        end_tm,        
        float(valve_interval_total_s), 
        float(valve_time_total_sec),
        float(1000*valve_time_total_sec) / float(valve_cycle_count),
        float(valve_cycle_count),
        float(co2_amount_total_L), 
        float(co2_amount_total_g), 
        float(heating_time_avg), 
        float(heating_time_total), 
        float(heating_cycle_count)
    )
    
    print("--- Creating plot ---")
    execute_gnuplot_script(config)
    
    
    
    return 0

        
def write_gnuplot_script(config, rows, header, infos, start_timestamp, end_timestamp, co2_interval, co2_total_duration, co2_average_injection_duration, co2_cycle_count, co2_total_L, co2_total_g, heating_interval, heating_total_duration, heating_cycle_count):
    ""

    datafilename = "merged_log.csv"
        
    #logexport("data_out.csv", rows);

    first_row = rows[0];
    columns = config['plot'].get('data_columns', str(range(2,len(first_row))))
    column_list = columns.split(',')
    column_index_list = [int(column) for column in column_list];
    if (21 not in column_index_list):
        column_index_list.append(21)
    
    time_column = 0;
    time_column_header = header[time_column];
    data_column_header_list = [header[column] for column in column_index_list]
    
    #print("Using time column: " + str(time_column_header ))
    #print("Using Data columns: " + str(data_column_header_list))
    
    resulting_data_column_indices = range(1, len(data_column_header_list)+1)
    #print("Result data column list: " + str(resulting_data_column_indices));
    
    selected_columns = [0] + column_index_list;
    
    rows_selected = select_column_list(rows, selected_columns)

    #print("Selected columns: " + str(selected_columns))
    logexport(datafilename, header, rows_selected);
    

    
    scriptfilename = config['plot'].get('script_filename', 'plot.gnuplot')
    print("Using script filename: " + str(scriptfilename))

    plotformat = config['plot'].get('plot_format', '')
    
    plotfilebase = config['plot'].get('plot_filename', 'plot.pdf')
    
    if (plotformat == ''):
        print ("Using default plot format(pdf)")
        # All legacy inis use no format -> use pdf and do not append to output fil ename
        plotfilename = plotfilebase
    else:
        print ("Using plot format: " + str(plotformat))    
        # New inis may use format -> append format extension if format is specified
        plotfilename = plotfilebase + "." + plotformat
    print("Using plot filename: " + str(plotfilename))

    legend_pos = "top right outside"
    legend_pos = config['plot'].get('legend_pos', legend_pos)
    print("Using legend position: " + str(legend_pos))    
        
    title = config['plot'].get('plot_title', '')
    print("Using title: " + str(title))
    xlabel    = config['plot'].get('xlabel', '')
    print("Using x label: " + str(xlabel))
    ylabel = config['plot'].get('ylabel', '')
    print("Using y label: " + str(ylabel))    

    #print("TEND_ROW: " + str((rows[len(rows)-1])))
    #print("TEND_STR: " + ((rows[len(rows)-1])[0]))
    tplot = locale.atof((rows[len(rows)-1])[0])

    print("...available columns (*=selected)")    
    col_idx = 0;
    row = rows[0];
    for col_idx  in range (len(header)):
        header_col = header[col_idx];
        data_col = row[col_idx];
        if (col_idx in column_index_list):
            print("   [" + str(col_idx) + "] : " + str(header_col) + " | " + str(data_col));
        else:
            print(" * [" + str(col_idx) + "] : " + str(header_col) + " | " + str(data_col));



    # Calculate the number scaling of x (time axis)
    xtickunit = (config['plot'].get('xtick_unit', 'm')).upper()
    
    if xtickunit == 'M':
        xtickspan = 1
        xtickgrid = 60
    if xtickunit == 'H':
        xtickspan = 60    
        xtickgrid = 1
    if xtickunit == 'D':
        xtickspan = 24*60
        xtickgrid = 1
    if xtickunit == 'W':
        xtickspan = 24*60*7
        xtickgrid = 1
        
    # Calculate the number of ticks, rounded down
    xtickcount = round((tplot / (xtickgrid*xtickspan)) - 0.5);
    xticks = []
    for x in range(1, xtickcount):
        xticks.append(x * xtickgrid)
            
    print("xtickspan: " + str(xtickspan))
    print("xticks: " + str(xticks));
    
    duration_tm = end_timestamp-start_timestamp;
    duration = duration_tm.total_seconds() / (60*60)
    sysinfostring = str.format("--- Timestamps ----\\nStart {:}\\nEnd   {:}\\nDuration {:.2f} h\\n--- CO_2 supply ---\\nPulse interval\\t{:.0f} s\\nPulse count\\t{:.0f}\\nCO_2 volume\\t{:.2f} L\\nCO_2 mass\\t{:.2f} g\\n\\n--- Heating ---\\nIntervall:\\t\\t{:.2f} min\\nDuration:\t\t{:.2f} min\\nCycle count:\\t{:.0f}", start_timestamp, end_timestamp, duration, co2_interval, co2_cycle_count, co2_total_L, co2_total_g, heating_interval, heating_total_duration /60, heating_cycle_count)
    
    with open(scriptfilename, "wt") as scriptfile:                    

        scriptfile.write(str.format("set terminal {0} enhanced font \"arial,8\"\n", plotformat))
        scriptfile.write(str.format("set output '{0}'\n", plotfilename))
        scriptfile.write(str.format("set datafile separator ';'\n"))
        
        scriptfile.write(str.format("set rmargin screen 0.7\n"))
        
        scriptfile.write(str.format("set title '{0}'\n", title))
        scriptfile.write(str.format("set xlabel '{0}'\n", xlabel))    
        scriptfile.write(str.format("set xtics {0}\n", xtickgrid))        
                            
        y1_label = "Axis_Y1"
        y1_label = config['Axis_Y1'].get('label', str(y1_label));
        y1_unit = ""
        y1_unit = config['Axis_Y1'].get('unit', str(y1_unit))    
        y1_ticks= 10
        y1_ticks = config['Axis_Y1'].get('ticks', str(y1_ticks))
        y1_min = 0
        y1_min = config['Axis_Y1'].get('min', str(y1_min))    
        y1_max = 100
        y1_max = config['Axis_Y1'].get('max', str(y1_max))

        scriptfile.write(str.format("set ylabel \"{0}\"\n", y1_label))
        scriptfile.write(str.format("set ytics nomirror {0}\n", str(y1_ticks)))
        scriptfile.write(str.format("set yrange [{0}:{1}]\n", y1_min, y1_max))
        
        y2_label = "Axis_Y2"
        y2_label = config['Axis_Y2'].get('label', str(y2_label))
        y2_unit = ""
        y2_unit = config['Axis_Y2'].get('unit', str(y2_unit))    
        y2_ticks = 10
        y2_ticks = config['Axis_Y2'].get('ticks', str(y2_ticks))    
        y2_min = 0
        y2_min = config['Axis_Y2'].get('min', str(y2_min));    
        y2_max = 100
        y2_max = config['Axis_Y2'].get('max', str(y2_max));
        
        scriptfile.write(str.format("set grid ytics lt 0 lw 1 lc rgb \"#bbbbbb\"\n"))
        scriptfile.write(str.format("set grid xtics lt 0 lw 1 lc rgb \"#bbbbbb\"\n"))
        scriptfile.write(str.format("set y2label \"{0}\"\n", y2_label))    
        scriptfile.write(str.format("set y2tics nomirror {0}\n", str(y2_ticks)))
        scriptfile.write(str.format("set y2range [{0}:{1}]\n", y2_min, y2_max))
        
        #scriptfile.write(str.format("set object 1 rectangle from screen 0.8, screen 0.05 to screen 0.95, screen 0.3 fc rgb \"black\"\n"))
        scriptfile.write(str.format("set key left\n"))
        scriptfile.write(str.format("set label \"" + sysinfostring + "\" left at screen 0.8, screen 0.4\n"))
        scriptfile.write(str.format("set key right reverse at  screen 0.95, screen 0.95\n", legend_pos))
        
        date_fmt = config['formats'].get('date', '%d.%m.%Y %H:%M:%S')

        for log_info in infos:
            start_offset = datetime.strptime(log_info[1], date_fmt) - start_timestamp;
            end_offset = datetime.strptime(log_info[2], date_fmt) - start_timestamp;            
            scriptfile.write(str.format("set object rectangle from {0}, graph 0 to {1}, graph 1 fs transparent solid 0.25 noborder fc rgb \"#DDDDDD\"\r\n", (start_offset.total_seconds() / 60) / xtickspan, (end_offset.total_seconds() / 60) / xtickspan))            
            #scriptfile.write(str.format("set arrow from {0}, graph 0 to {1}, graph 1 nohead lw 0.2 lc rgb \'red\'\r\n", (start_offset.total_seconds() / 60) / xtickspan, (start_offset.total_seconds() / 60) / xtickspan))
            #scriptfile.write(str.format("set label at {0}, graph 0.5  rotate by -90 tc \'red\'\r\n", (start_offset.total_seconds() / 60) / xtickspan))

        #scriptfile.write(str.format("b = {1} * {2} / (12.0/44.0)", config['resampling'].get('dLtog_vo2', str(1.7777))))
        #scriptfile.write(str.format("f(X) = - a*x - b"))
        #scriptfile.write(str.format("fit [1:] f(x) \'{1}\' using ($1*60/1440):($7-0.5.$5) via a"))
        fac = (12.0/44.0) / float(config['resampling'].get('dLtog_vo2', 0.0))
        #scriptfile.write( str.format("set label \"--- CO2 loss estimate ---\\nml/ms: {0} \\nResidue: {1} ml ({2} mg) \\nHourly: {3} ml/h ( {4} mg/h)\" left at screen 0.8, screen 0.55\r\n", float(config['resampling'].get('dV_co2', str(0.215))), float(config['bookkeeping'].get('dCO2VolumeEquivCapacity', str(0))), float(config['bookkeeping'].get('dCO2VolumeEquivCapacity', str(0))) * fac, float(config['bookkeeping'].get('dCO2VolumeLossPerHour', str(0))), float(config['bookkeeping'].get('dCO2VolumeLossPerHour', str(0))) * fac))
    

        scriptfile.write(str.format("plot "))    
        
        for data_column in resulting_data_column_indices:
        
            x_axis = "1"
            y_axis = "1"
            
            
            data_column_int = int(data_column)
            orig_column = column_index_list[data_column_int-1]
            orig_column_int = int(orig_column)
            # Don't try to plot the number 21 (date column)
            if (orig_column_int != 21):
                line_title = str(header[orig_column_int])        
                line_denom = str(100.0)
                line_spec = "lines"
                if config.has_section(str(orig_column)):
                    line_title = config[str(orig_column)].get('legend', str(line_title));
                    line_denom = config[str(orig_column)].get('line_denom', str(line_denom));
                    line_spec = config[str(orig_column)].get('line_spec', str(line_spec));
                    y_axis = config[str(orig_column)].get('y_axis', str(y_axis))
                            
                axis_spec = "x" + x_axis + "y" + y_axis;
                            
                print(            str.format("'{0}' using (${1}/{2}):(${3}/{4}) title \"{5}\" with {6} axes {7}, \n", datafilename, time_column+1, xtickspan, int(data_column)+1, line_denom, line_title, line_spec, axis_spec))    
                scriptfile.write(    str.format("'{0}' using (${1}/{2}):(${3}/{4}) title \"{5}\" with {6} axes {7}, ", datafilename, time_column+1, xtickspan, int(data_column)+1, line_denom, line_title, line_spec, axis_spec))        
        extra = config['plot'].get('extra', '')
        print(extra)
        scriptfile.write(extra)  
        #scriptfile.write(", \'merged_log.csv\' using ($1/1440):(($6/1000)-f($1/(1440))) with lines lt 1 title \"FIT\"")
        scriptfile.write('\r\n')  

    return 
    
def execute_gnuplot_script(config):
    ""
    print(" === Begin Plot === ");
    scriptfilename = config['plot'].get('script_filename', 'plot.gnuplot')
    subprocess.run(["gnuplot", str(scriptfilename) ])
    
    return 0;

        
#  
# 
# Buildmain();
