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
import time

start_time = time.time()

with open('router_ips.csv', mode='r') as file:
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
serial_number_oid = '1.3.6.1.4.1.14988.1.1.7.3.0'
# SNMP OID for sfp_temperature_oid
temperature_oid = '.1.3.6.1.4.1.14988.1.1.3.10.0'
# SNMP OID for sfp_tx_power
sfp_tx_power_oid = '1.3.6.1.4.1.14988.1.1.19.1.1.9.6'
# SNMP OID for sfp_rx_power
sfp_rx_power_oid = '.1.3.6.1.4.1.14988.1.1.19.1.1.10.6'

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
    hardware = get_snmp_value(ip_address, community, hardware_oid)
    serial_number = get_snmp_value(ip_address, community, serial_number_oid)
    temperature = get_snmp_value(ip_address, community, temperature_oid)
    sfp_tx_power = get_snmp_value(ip_address, community, sfp_tx_power_oid)
    sfp_rx_power = get_snmp_value(ip_address, community, sfp_rx_power_oid)

    data = {
        'retrieved_at_date': retrieved_at_date,
        'retrieved_at_time': retrieved_at_time,
        'uptime': uptime_read, 
        'hostname': [hostname],
        'ip_address': [ip_address], 
        'hardware': [hardware],
        'serial_number': [serial_number],
        'temperature': [temperature],
        'sfp_tx_power': [sfp_tx_power], 
        'sfp_rx_power': [sfp_rx_power]
    }

    return data

def import_to_mysql(df):
    try:
        engine = create_engine('mysql+mysqlconnector://<username>:<password>@<host>:3306/<db>')
        df.to_sql(name='rsl_mikrotik', con=engine, if_exists='append', index=False)
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
    print(df)
else:
    print("No dataframes to concatenate")

df.to_csv('mikrotik.csv', index=False)
# import_to_mysql(df)

elapsed_time = time.time() - start_time

minutes, seconds = divmod(elapsed_time, 60)
print(f"Time elapsed: {int(minutes)} minutes and {int(seconds)} seconds")
