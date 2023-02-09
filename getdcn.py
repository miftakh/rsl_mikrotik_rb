# Author: Miftakhurrokhman
# Date: January 26, 2023
# Version: 1
# Purpose: This script is used to retrieve SNMP data from DCN devices

from pysnmp.hlapi import *
import pysnmp
from datetime import timedelta
import pandas as pd
from pandas import DataFrame
import datetime 
import mysql.connector
from mysql.connector import  Error
import csv
from sqlalchemy import create_engine
from tqdm import tqdm
import re
import time

start_time = time.time()

with open('ips_dcn.csv', mode='r') as file:
    csvFile = csv.DictReader(file)
    ip_address_sources = [row['ip_address'] for row in csvFile]

community = 'public'

# Retrieve current time
retrieved_at_date = datetime.datetime.now().strftime("%Y-%m-%d")
retrieved_at_time = datetime.datetime.now().strftime("%H:%M:%S")
# SNMP OID for uptime
uptime_oid = '.1.3.6.1.2.1.1.3.0'
# SNMP OID for hostname
hostname_oid = '.1.3.6.1.2.1.1.5.0'
# SNMP OID for IP address
ip_address_oid = '1.3.6.1.2.1.4.20.1.1.'
# SNMP OID for hardware
hardware_oid = '1.3.6.1.2.1.1.1.0'
# SNMP OID for serial number
# serial_number_oid = '1.3.6.1.4.1.14988.1.1.7.3.0'
# SNMP OID for sfp_temperature_oid
temperature_oid_10 = '.1.3.6.1.4.1.6339.100.30.1.1.2.10'
# # SNMP OID for sfp_tx_power
sfp_tx_power_oid_10 = '.1.3.6.1.4.1.6339.100.30.1.1.22.10'
# # SNMP OID for sfp_rx_power
sfp_rx_power_oid_10 = '.1.3.6.1.4.1.6339.100.30.1.1.17.10'
temperature_oid_9 = '.1.3.6.1.4.1.6339.100.30.1.1.2.9'
sfp_tx_power_oid_9 = '.1.3.6.1.4.1.6339.100.30.1.1.22.9'
sfp_rx_power_oid_9 = '.1.3.6.1.4.1.6339.100.30.1.1.17.9'
# # SNMP OID for sfp_rx_power


# convert_uptime
def convert_uptime(uptime):
    # convert uptime value from hundredths of seconds to seconds
    uptime_in_seconds = int(uptime) / 100
    # create a timedelta object with the uptime in seconds
    uptime_delta = timedelta(seconds=uptime_in_seconds)
    # extract days, hours, minutes, and seconds
    days, remainder = divmod(uptime_delta.seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    # return the uptime in a human-readable format
    return f'{days}d {hours}:{minutes}:{seconds}'

def get_snmp_value(ip_address, community, oid):
    errorIndication, errorStatus, errorIndex, varBinds = next(
        getCmd(SnmpEngine(),
            CommunityData(community, mpModel=0),
            UdpTransportTarget((ip_address, 161)),
            ContextData(),
            ObjectType(ObjectIdentity(oid))
        )
    )
    if errorIndication:
        return errorIndication
    elif errorStatus:
        return '%s at %s' % (errorStatus.prettyPrint(),
                            errorIndex and varBinds[int(errorIndex) - 1][0] or '?')
    else:
        return varBinds[0][1].prettyPrint()

def get_data(ip_address, community):
    uptime = get_snmp_value(ip_address, community, uptime_oid)
    uptime_read = convert_uptime(uptime)
    hostname = get_snmp_value(ip_address, community, hostname_oid)
    ip_address = get_snmp_value(ip_address, community, ip_address_oid + '.' + ip_address)
    hardware_info = get_snmp_value(ip_address, community, hardware_oid)
    temperature_9 = get_snmp_value(ip_address, community, temperature_oid_9)
    sfp_tx_power_9 = get_snmp_value(ip_address, community, sfp_tx_power_oid_9)
    sfp_rx_power_9 = get_snmp_value(ip_address, community, sfp_rx_power_oid_9)
    temperature_10 = get_snmp_value(ip_address, community, temperature_oid_10)
    sfp_tx_power_10 = get_snmp_value(ip_address, community, sfp_tx_power_oid_10)
    sfp_rx_power_10 = get_snmp_value(ip_address, community, sfp_rx_power_oid_10)

    # Extract device info
    match_name = re.search(r'(.+?)Device', hardware_info)
    hardware = match_name.group(1) if match_name else 'Null'

    match_sn = re.search(r'Serial No.:(.+)', hardware_info)
    serial_number = match_sn.group(1) if match_sn else 'Null'

    data = {
        'retrieved_at_date': retrieved_at_date,
        'retrieved_at_time': retrieved_at_time,
        'uptime': uptime_read, 
        'hostname': [hostname],
        'ip_address': [ip_address], 
        'hardware': [hardware],
        'serial_number': serial_number,
        'desc_port9': ['Ethernet 9'],
        'temp_port9': [temperature_9],
        'tx_power_port9': [sfp_tx_power_9], 
        'rx_power_port9': [sfp_rx_power_9],
        'desc_port10': ['Ethernet 10'],
        'temp_port10': [temperature_10],
        'tx_power_port10': [sfp_tx_power_10], 
        'rx_power_port10': [sfp_rx_power_10],
    }

    return data

def import_to_mysql(df):
    try:
        engine = create_engine('mysql+mysqlconnector://<username>:<password>@<host>:3306/<db>')
        df.to_sql(name='rsl_dcn', con=engine, if_exists='append', index=False)
        print("Data successfully imported to MySQL")
    except Exception as e:
        print("Error occurred while importing data to MySQL:", str(e))

df_list = []
failed_ips = []
for ip_address_source in tqdm(ip_address_sources, desc='Retrieving SNMP data'):
    if ip_address_source in failed_ips:
        continue
    try:
        snmp_data = get_data(ip_address_source,community)
        df = pd.DataFrame(snmp_data)
        df_list.append(df)
    except Exception as e:
        failed_ips.append(ip_address_source)
        print(f"Failed to retrieve SNMP data for {ip_address_source}: {e}")


df = pd.concat(df_list, ignore_index=True)
if len(df_list) > 0:
    df = pd.concat(df_list, ignore_index=True)
    df = df[['retrieved_at_date','retrieved_at_time','uptime','hostname','ip_address','hardware','serial_number','desc_port9','temp_port9','tx_power_port9','rx_power_port9','desc_port10','temp_port10','tx_power_port10','rx_power_port10']]
    print(df)
else:
    print("No dataframes to concatenate")

df.to_csv('dcn.csv', index=False)
import_to_mysql(df)

elapsed_time = time.time() - start_time

minutes, seconds = divmod(elapsed_time, 60)
print(f"Time elapsed: {int(minutes)} minutes and {int(seconds)} seconds")


# with tqdm(total=100, desc="Connecting to MySQL") as pbar:
#     try:
#         engine = create_engine('mysql+mysqlconnector://admin:special-project-2020@10.13.14.50:3306/mikrotik_rsl')
#         connection = engine.connect()
#         pbar.update(100)
#         # print("Connection to MySQL database established.")
#     except Error as e:
#         print(f"Error connecting to MySQL database: {e}")
#         exit()

# for df in tqdm(df_list,desc='Running append to database'):
#     check = df != 'RequestTimedOut'
#     if check.all().all():
#         try:
#             df.to_sql(name='rsl_dcn', con=engine, if_exists='append', index=False)
#         except Exception as e:
#             print(f'Error appending data to MySQL table: {e}')
#             continue
#     else:
#         check =0
#         # print(f'Data not appended to MySQL table, IP address: {df.iloc[0]["ip_address"]} returned RequestTimedOut')
