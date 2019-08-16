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
for item in response.get('Contents', []):
    key = item["Key"]
    page_number =  key.split("_")[1].split(".")[0]  #key[27:30]
    page_number = page_number[page_number.find('0'):][:-1]
    if not dic_files.get(page_number):
        dic_files[page_number] = []
    dic_files[page_number].append(key)

# title eds
titles = open("{}/cadernos.txt".format(dir_name), "w")
index = 0

for key, values in dic_files.items():
    index += 1
    dir_file = "{}/{}".format(dir_name, int(key))
    if not os.path.exists(dir_file):
        os.mkdir(dir_file)

    file_name = "{}/2render.pdf".format(dir_file)

    # here starts the human-error variable    
    preferable_file = {}
    for i in values:
        preferable_file[i.lower()] = i
    temp = [i for i in preferable_file.keys()]
    temp.sort()
    preferable_file = preferable_file[temp[-1]]
    # ends here

    # download file
    logging.info("PRESSLAB: downloading {} to {}".format(preferable_file, file_name))
    with open(file_name, 'wb') as data:
        client.download_fileobj(args.aws_bucket, preferable_file, data)
        titles.write("Page {}\n".format(index))

titles.close()
open("{}/download.ok".format(dir_name), "w").write("ok")
