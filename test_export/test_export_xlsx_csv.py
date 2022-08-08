import pandas as pd
from time import time
from numpy import mean


# Test how much time the pandas export functions to_csv, to_xlsx and to_pickle take

filepath = r"C:\Users\dominik\Downloads\apple.csv"

data = pd.read_csv(filepath)
dt_csv_list = []
dt_xlsx_list = []
dt_pkl_list = []


for i in range(100):
    start_csv = time()
    data.to_csv('testfile.csv')
    dt_csv = time()-start_csv
    # print('csv written, time elapsed: ' + str(dt_csv))
    dt_csv_list.append(dt_csv)

    start_xlsx = time()
    data.to_excel('testfile.xlsx')
    dt_xlsx = time() - start_xlsx
    # print('excel written, time elapsed: ' + str(dt_xlsx))
    dt_xlsx_list.append(dt_xlsx)

    start_pkl = time()
    data.to_pickle('testfile.pkl')
    dt_pkl = time() - start_pkl
    # print('excel written, time elapsed: ' + str(dt_xlsx))
    dt_pkl_list.append(dt_pkl)

print('Mean time csv: \t\t{:.5f} s'.format(mean(dt_csv_list)))
print('Mean time xlsx: \t{:.5f} s'.format(mean(dt_xlsx_list)))
print('Mean time pkl: \t\t{:.5f} s'.format(mean(dt_pkl_list)))
