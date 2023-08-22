SNMP Data Retrieval and Storage Script
This script is designed to retrieve SNMP (Simple Network Management Protocol) data from a list of router IP addresses, extract specific information, and store the gathered data in a CSV file. Additionally, there is an option to import the data into a MySQL database.

Prerequisites
Before using this script, make sure you have the following:

Python installed on your system (version 3.6 or later).
Required Python packages installed. You can install them using the following command:
pip install pysnmp pandas mysql-connector-python sqlalchemy tqdm

Usage
Data Preparation:

Prepare a CSV file named router_ips.csv containing a column named ip_address listing the IP addresses of the routers you want to query using SNMP.
Configuration:

Modify the community variable to match the SNMP community string used by the routers. Replace 'public' with your actual SNMP community string if it's different.

Modify the MySQL database connection details in the import_to_mysql function. Replace <username>, <password>, <host>, <db> with your MySQL database credentials and details.

Running the Script:

Open a terminal or command prompt.

Navigate to the directory containing the script and the router_ips.csv file.

Run the script using the following command:
python script_name.py
Output:

The script will retrieve SNMP data from the routers listed in the router_ips.csv file. If successful, it will generate a CSV file named mikrotik.csv containing the gathered data.

Optionally, if you uncomment the import_to_mysql(df) line, the script will attempt to import the data into the specified MySQL database.

The script will also print the time elapsed during the data retrieval and processing.

Notes
The script uses the pysnmp library to perform SNMP queries to retrieve data from routers.

SNMP OIDs (Object Identifiers) are used to query specific information from routers. You can modify the OIDs to gather different types of data based on your requirements.

The script provides error handling for cases where SNMP data retrieval fails for specific IP addresses. Failed IP addresses will be recorded in the failed_ips list.

Be cautious when using the import_to_mysql function to store data in a MySQL database. Make sure to secure your database credentials and validate the data being imported.

Disclaimer
This script is provided as-is and without any warranties. Use it at your own risk. Always ensure you have proper authorization to access the SNMP devices and follow best practices for data handling and security.
