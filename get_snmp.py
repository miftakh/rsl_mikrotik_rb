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
    
df_list = []
failed_ips = []
for ip_address_source in tqdm(ip_address_sources,desc='Retrieving SNMP data'):
    if ip_address_source in failed_ips:
        continue
    try:
        uptime = get_snmp_value(ip_address_source, community, uptime_oid)
        uptime_read = convert_uptime(uptime)
        hostname = get_snmp_value(ip_address_source, community, hostname_oid)
        if hostname == "RequestTimedOut('No SNMP response received before timeout')":
            hostname = None
        ip_address = get_snmp_value(ip_address_source, community, ip_address_oid + '.' + ip_address_source)
        hardware = get_snmp_value(ip_address_source, community, hardware_oid)
        serial_number = get_snmp_value(ip_address_source, community, serial_number_oid)
        if serial_number == "RequestTimedOut('No SNMP response received before timeout')":
            serial_number = None
        temperature = get_snmp_value(ip_address_source, community, temperature_oid)
        if temperature == "RequestTimedOut('No SNMP response received before timeout')":
            temperature = None
        else:
            temperature = float(temperature)
            temperature = temperature / 10
        sfp_tx_power = get_snmp_value(ip_address_source, community, sfp_tx_power_oid)
        if sfp_tx_power == "RequestTimedOut('No SNMP response received before timeout')":
            sfp_tx_power = None
        else:
            sfp_tx_power = float(sfp_tx_power)
            sfp_tx_power = sfp_tx_power / 1000
        sfp_rx_power = get_snmp_value(ip_address_source, community, sfp_rx_power_oid)
        if sfp_rx_power == "RequestTimedOut('No SNMP response received before timeout')":
            sfp_rx_power = None
        else:
            sfp_rx_power = float(sfp_rx_power)
            sfp_rx_power = sfp_rx_power / 1000

        data = {
                'retrieved_at_date': retrieved_at_date,
                'retrieved_at_time': retrieved_at_time,
                'uptime':uptime_read, 
                'hostname': [hostname],
                'ip_address': [ip_address], 
                'hardware': [hardware],
                'serial_number': [serial_number],
                'temperature': [temperature],
                'sfp_tx_power': [sfp_tx_power], 
                'sfp_rx_power': [sfp_rx_power],
                }

        df = DataFrame(data)
        df_list.append(df)
        # result_df = pd.concat(df_list)

    except Exception as e:
        failed_ips.append(ip_address_source)
        print(f'Error retrieving data from {ip_address_source}: {e}')
result_df = pd.concat(df_list)
print(result_df)


with tqdm(total=100, desc="Connecting to MySQL") as pbar:
    try:
        engine = create_engine('mysql+mysqlconnector://<username>:<password>@<host>:3306/<db>')
        connection = engine.connect()
        pbar.update(100)
        # print("Connection to MySQL database established.")
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        exit()

for df in tqdm(df_list,desc='Running append to database'):
    check = df != 'RequestTimedOut'
    if check.all().all():
        try:
            df.to_sql(name='table_name', con=engine, if_exists='append', index=False)
        except Exception as e:
            print(f'Error appending data to MySQL table: {e}')
            continue
    else:
        check =0
        # print(f'Data not appended to MySQL table, IP address: {df.iloc[0]["ip_address"]} returned RequestTimedOut')
