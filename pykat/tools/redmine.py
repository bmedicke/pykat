"""
This file contains various functions for processing the Redmine download data for Finesse.
"""

import fileinput
from dateutil.parser import parse
import json
import urllib

def processRedmineProductionLog(log, output):
    """
    This function parses the Redmine production log for all Finesse
    downloads. The output is a text file that contains the file
    downloaded, the IP address and the date.
    
    Production log file is typically big (e.g. 10GB), this takes awhile
    to run.
    
    log: path and filename to log file
    output: path and filename of output text file to create
    """
    found = -1

    with open(output, "w") as ofile:
        for line in fileinput.input(log_filename):

            if found > 0 and found+1 == fileinput.lineno():
                try:
                    file = line.lstrip().split()[3]
                    file = file.split("=>")[1][1:-2]
                    found = -2
                except:
                    print("Couldn't parse download, probably a traceback")
                    print(line)
                    
                    found = -1
    
            elif line.startswith("Processing AttachmentsController#download"):
                found = fileinput.lineno()
    
                ip = line.split()[3]
                date = line.split()[5]

            if found == -2:
                ext = file.split(".")[-1]
    
                if ext == "zip" or ext == "tar" or ext == "pdf":
                    ofile.write("%s %s %s\n" %(file, ip, date))
        
                    print file, ip, date
        
                found = -1
                

def readFinesseDownloadData(data_filename, unique=True, geo_filename=None):
    """
    Reads the data files generated by processRedmineProductionLog
    and getFinesseDownloadIPGeoData.
    
    File download data is returned in a dictionary with filenames as the
    key. This then contains another dictionary with the date of downloads
    and number of downloads that day, and a list of IP addresses that
    downloaded it.
    
    If Geo data filename is provided another dictionary will be returned.
    The keys of which are the IP addresses and the latitude and longitude
    values.
    
    data_filename: filename and path of processRedmineProductionLog output file
    unique: If true only unique IP addresses for each file download are read
    geo_filename: filename and path of getFinesseDownloadIPGeoData output file
    """
    files = {}
    IPGeo = {}

    with open(data_filename, "r") as data:
        for line in data:
            split = line.split()
            file = split[0].lower()
            ip = split[1]
            date = parse(split[2])
        
            if split[0] not in files:
                files[split[0]] = ([], {})
       
            if unique and ip in files[split[0]][0]:
                continue
            
            files[split[0]][0].append(ip)
        
            if date not in files[split[0]][1]:
                files[split[0]][1][date] = 0
            
            files[split[0]][1][date] += 1
        
    if geo_filename != None:
        with open(geo_filename, "r") as data:
            for line in data:
                split = line.split()
                IPGeo[split[0]] = (float(split[1]), float(split[2]))
        
        return files, IPGeo
    else:
        return files
    
def getFinesseDownloadIPGeoData(input_file, output_file):
    """
    Using the information outputted to the file by the function processRedmineProductionLog
    this will function will call various free IP to Latitude/Longitude web services.
    The file outputted will contain a list of unique IP addresses and it's coordinates.
    
    Note: This takes a long time to run! Free webservice may kick you off too if too many
    requests are made per hour.
    
    input_file: filename and path to processRedmineProductionLog output file
    output_file: Output filename and path
    """

    with open(input_file, "r") as data:
        with open(output_file, "w") as w:
            for line in data:
                split = line.split()
                file = split[0].lower()
                ip = split[1]
                date = parse(split[2])
                
                if ip not in IPGeo:
                    IPGeo[ip] = ([], [])
            
                    response = urllib.urlopen('http://api.hostip.info/get_html.php?ip=%s&position=true' % ip).read()
        
                    lat = response.split('\n')[3].split()
                    lon = response.split('\n')[4].split()
            
                    if len(lat) == 2 and len(lon) == 2:
                        w.write("%s %g %g\n" % (ip, float(lat[1]), float(lon[1]) ))
                    else:
                        response = json.loads(urllib.urlopen('https://freegeoip.net/json/%s' % ip).read())

                        if 'latitude' in response:
                            w.write("%s %g %g\n" % (ip, float(response['latitude']), float(response['longitude'])))
                    
                    print(response)
