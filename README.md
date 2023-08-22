SNMP Data Retrieval and Storage Script
This repository contains a Python script designed to streamline the retrieval of SNMP (Simple Network Management Protocol) data from a list of router IP addresses. The script utilizes the pysnmp library to establish SNMP communication with the routers, extract specific information, and store the acquired data in a CSV file. Additionally, there is an optional feature to import the gathered data into a MySQL database for further analysis.

Features and Usage
Efficient Data Gathering:

The script reads router IP addresses from a router_ips.csv file, allowing you to easily manage and update the list.
SNMP data retrieval is orchestrated using the pysnmp library, ensuring efficient communication with the routers.
Customizable Configuration:

Modify the SNMP community string in the script to match your network configuration.
Customize SNMP OIDs (Object Identifiers) to target specific data points on the routers.
Data Extraction and Transformation:

The script extracts various information from the routers, including uptime, hostname, IP address, hardware details, serial number, temperature, and SFP module power levels.
Uptime values are converted into human-readable format for easy interpretation.
Output Generation:

Retrieved data is compiled into a Pandas DataFrame for organized storage and analysis.
If successful, the script generates a CSV file named mikrotik.csv containing the gathered data.
MySQL Database Integration (Optional):

Uncomment the relevant line in the script to enable data import into a MySQL database.
Provides the option to establish a connection to a MySQL database, allowing for long-term data storage and more advanced analysis.
Error Handling:

The script handles cases where SNMP data retrieval fails for specific IP addresses and maintains a record of failed attempts.
Prerequisites
Python 3.6 or later installed.
Required Python packages installed (pysnmp, pandas, mysql-connector-python, sqlalchemy, tqdm).
Usage Instructions
Prepare a router_ips.csv file with a column named ip_address containing the IP addresses of the routers to be queried.

Configure the script by modifying the SNMP community string and, if necessary, the MySQL database connection details.

Run the script using the command: python script_name.py (replace script_name.py with the actual script filename).

Check the generated mikrotik.csv file for the retrieved data and optionally verify the MySQL database for imported data.

Disclaimer
This script is provided for educational and informational purposes only. Users are responsible for ensuring proper authorization to access SNMP devices and adhering to network security best practices. The script is offered without warranties, and users should exercise caution when handling sensitive information.
