import os


print('Logfile renaming tool für PBX Logfiles.\nACHTUNG: Die Logfiles im angegebenen Ordner werden nicht umkehrbar umbenannt.\n')
logfile_directory = input('Absoluter Link zu den Logfiles:')
if logfile_directory[-1] not in ['\\', '/']:
    logfile_directory = logfile_directory + '/'
# replace the backslash
logfile_directory = os.path.join(logfile_directory).replace('\\', '/')
file_list = os.listdir(logfile_directory)

for old_name in file_list:
    if not old_name[:4] == 'Log_':
        continue
    split_list = old_name.split('.')[0]
    split_list = split_list.split('_')
    new_name_list = ['ecosM24', split_list[3], 'LF01', '02', split_list[4][2:]+split_list[5]+split_list[6] + '_' + split_list[7]+split_list[8]+split_list[9]]
    new_name = '-'.join(new_name_list) + '.csv'
    # print(new_name)
    os.rename(os.path.join(logfile_directory, old_name), os.path.join(logfile_directory, new_name))

print('{} files umbenannt'.format(len(file_list)))
