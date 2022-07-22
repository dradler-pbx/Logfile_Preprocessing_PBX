import csv
import json

logfile_version = "LF01"
logfile_def_file = "logfile_def_csv_files/LF01.csv"

with open(logfile_def_file, "r", encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    header_dict = {rows[0]: rows[1] for rows in reader}

with open(logfile_version+".json", "w") as f:
    json.dump(header_dict, f)
