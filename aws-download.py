# Copyright (C) 2019  Alexandre Gans <alexandre@presslab.com.br>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""Command line tool to help verify bucket objects and organize then"""
import os
import sys
import re
import logging
import argparse
import boto3
from datetime import datetime
from gsuitetool import send_mail


## parsing shell arguments
parser = argparse.ArgumentParser(description="Edition pdf downloader S3 bucket command line tool")
parser.add_argument("-i", "--aws_id", help="awc access key id", required=True)
parser.add_argument("-k", "--aws_key", help="awc secret access key", required=True)
parser.add_argument("-b", "--aws_bucket", help="awc bucket name", required=True)
parser.add_argument("-d", "--date", help="working date YYYYMMDD", required=True)
parser.add_argument("-p", "--prefix", help="bucket prefix AN|DC|SC", required=True)
parser.add_argument("-e", "--email", help="email support", required=True)

args = parser.parse_args()
try:
    date = datetime.strptime(args.date, "%Y%m%d")
except:
    raise Exception("Date param must be YYYYMMDD")

if not args.prefix in ["AN", "DC", "SC", "JSC", "HSC"]:
    raise Exception("Prefix must be one of AN, DC, SC")

# get logger to debug actions
logging.basicConfig(filename="dw.{}-{}.log".format(args.date, args.prefix),
                    filemode="w",
                    format='%(asctime)s - %(message)s',
                    level=logging.DEBUG)

# get aws client
logging.info("PRESSLAB: Connection to aws bucket")
client = boto3.client("s3", aws_access_key_id=args.aws_id,
                            aws_secret_access_key=args.aws_key)

# retrieve objects from bucket prefix
prefix = "{}/{}/".format(date.strftime("%Y/%m/%d"), args.prefix)
logging.info("PRESSLAB: retrieving bucket objects {}".format(prefix))
try:
    response = client.list_objects(Bucket=args.aws_bucket, Prefix=prefix)
except:
    logging.error("PRESSLAB: Cannot retrieve bucket file list")
    sys.exit()

# create edition folder to work with
dir_name = date.strftime("%Y%m%d")
if not os.path.exists(dir_name):
    os.mkdir(dir_name)

# organize file names
logging.info("PRESSLAB: organizing files")
dic_files = {}
dic_files_ex = {}
pattern = re.compile("[A-Za-z0-9\/]+_[A-Za-z0-9]+\.[A-Za-z]")
for item in response.get('Contents', []):
    key = item["Key"]

    #print(key, pattern.match(key))
    if not pattern.match(key):
        continue

    key_number =  key.split("_")[1].split(".")[0]  #key[27:30]
    page_number = key_number[key_number.find('0'):][:-1]
    caderno = key_number[:key_number.find('0')]
    if caderno.lower() in ["an", "dc", 'st']: # main
        if not dic_files.get(page_number):
            dic_files[page_number] = []
        dic_files[page_number].append(key)
    else:
        if not dic_files_ex.get(caderno):
            dic_files_ex[caderno] = []
        dic_files_ex[caderno].append(key)

# title eds
titles = open("{}/cadernos.txt".format(dir_name), "w")
index = 0
list_download = []
#
files = [i for i in dic_files.keys()]
files.sort()
for key in files:
    list_download.append(dic_files[key])

    found = {}
    for keyy in dic_files_ex.keys():
        vals = dic_files_ex[keyy]
        vals.sort()
        first_item = vals[0]
        key_number =  first_item.split("_")[1].split(".")[0]  #key[27:30]
        page_number = key_number[key_number.find('0'):][:-1]  
        if page_number == key:
            for i in vals:
                key_number =  i.split("_")[1].split(".")[0]  #key[27:30]
                page_number = key_number[key_number.find('0'):][:-1]
                if not found.get(page_number):
                    found[page_number] = []
                found[page_number].append(i)
        if found:
            keys = [i for i in found.keys()]
            keys.sort()
            for i in keys:
                list_download.append(found[i])

for key in list_download:
    index += 1
    dir_file = "{}/{}".format(dir_name, index)
    if not os.path.exists(dir_file):
        os.mkdir(dir_file)

    file_name = "{}/2render.pdf".format(dir_file)

    # here starts the human-error variable    
    key.sort()
    preferable_file = key[-1]
    # ends here

    # download file
    logging.info("PRESSLAB: downloading {} to {}".format(preferable_file, file_name))
    with open(file_name, 'wb') as data:
        client.download_fileobj(args.aws_bucket, preferable_file, data)
        titles.write("Page {}\n".format(index))

titles.close()
open("{}/download.ok".format(dir_name), "w").write("ok")
