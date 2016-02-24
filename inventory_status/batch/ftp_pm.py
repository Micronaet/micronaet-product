#!/usr/bin/python
import ftplib
import os

filename = 'esistenze.csv'
ftp = ftplib.FTP('pm.server.it')
ftp.login('giacenze', 'password')

#ftp.cwd('.')
os.chdir('/home/administrator/photo/xls/')
ftp.storlines("STOR " + filename, open(filename, 'r'))
os.system('wget http://pm.server.it/importGPBtoPM.php')
