#!/usr/bin/env python
#
#

import yaml
import json
import sys
import csv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date

try:
    import requests
except ImportError:
    print("Please install the python-requests module.")
    sys.exit(-1)
from requests_oauthlib import OAuth1

# URL to your Satellite 6 server
satellite_url = "https://satellite.example.com"
# URL for API
satellite_api = "%s/api/v2/" % satellite_url
# Katello API
katello_api = "%s/katello/api/" % satellite_url
# Satellite 6 OAuth credentials
oauth_secret = ""
oauth_key = ""
# Enable SSL
ssl_verify = True
mail_server = "mail.example.com"
to_address = "user@example.com"
from_address = "satellite@example.com"

# connect to Satellite API and pull information
def get_data(url):
    # Performs a GET using the passed URL location
    satellite = requests.get(url,
            auth=(OAuth1(oauth_key, oauth_secret)),
            verify=ssl_verify)
    return satellite.json()

# pull information and set as json
def get_results(url):
    jsn_results = get_data(url)
    if jsn_results.get('error'):
        print("Error: " + jsn_results['error']['message'])
    else:
        if jsn_results.get('results'):
            return jsn_results['results']
        elif 'results' not in jsn_results:
            return jsn_results
        else:
            print("No results found")
    return None

# return results value
def return_all_results(url):
    results = get_results(url)
    if results:
        return results

def display_info_for_hosts(url):
    # set host values to hosts
    hosts = get_results(url)
    if hosts:
        # loop through all hosts
        for host in hosts:
            # set hostname to name
            name = host['name']
            try:
                # set host last checkin date
                last_checkin = host['subscription_facet_attributes']['last_checkin']
                # set errata_counts
                errata = host['content_facet_attributes']['errata_counts']
            except:
                # error checking
                last_checkin = "error"
                errata = "error"

            # set number of bugfixes per host
            bugfixes = errata['bugfix']
            # set number of security patches per host
            security_patches = errata['security']
            # set total patches per host
            total_patches = errata['total']
            # print hostname, lastcheckin, bugfixes, securityPatches and totalPatches
            print("%-40s %-30s %-10s %-10s %-10s" % (name,
                last_checkin,
                bugfixes,
                security_patches,
                total_patches))

def return_info_for_hosts(url):
    # set host values to hosts
    hosts = get_results(url)
    # set empty list for later
    outputData = []
    if hosts:
        # loop through all hosts
        for host in hosts:
            # set hostname to name
            name = host['name']
            try:
                # set host last checkin date
                last_checkin = host['subscription_facet_attributes']['last_checkin']
                # set errata_counts
                errata = host['content_facet_attributes']['errata_counts']
            except:
                # error checking
                last_checkin = "error"
                errata = "error"

            # set number of bugfixes per host
            bugfixes = errata['bugfix']
            # set number of security patches per host
            security_patches = errata['security']
            # set total patches per host
            total_patches = errata['total']

            outputData.append(
                    {
                        'hostname': name,
                        'last_checkin': last_checkin,
                        'bugfixes': bugfixes,
                        'security_patches': security_patches,
                        'total_patches': total_patches
                    }
            )

    # return list of dictionaries
    return outputData

def return_html_format(server_list):
    # initialize variables
    body = ""
    html = "<html>"
    header = "<h1>Satellite Host Report</h1>"
    # HTML Table Styling
    table_style = """\
    <head>
    <style>
    table {
        font-family: Arial, Helvetica, Open Sans, sans-serif;
        width: 100%;
        border-collapse: collapse;
    }
    th {
        background-color: #1E4B5E;
        color: #dddddd;
    }
    td, th {
        text-align: left;
        padding: 8px;
        border: 1px solid #dddddd;
    }
    .nth-table tr:nth-child(even) {
        color: #5cb85c;
    } 
    </style>
    </head>
    """
    # HTML Table Headers
    table_header = """\
    <tr>
        <th>Hosts</th>
        <th>Last Checkin</th>
        <th>Security</th>
        <th>Bugfixes</th>
        <th>Upgradable</th>
    </tr>
    """
    for server in server_list:
        # pull checkin date for comparison later
        checkin_date = server['checkin'].split(' ')[0]
        # set to date format to compare later
        checkin_date = date.fromisoformat(checkin_date)
        # compare dates to set the rwo background color
        # `style` requires "" around key/value pair
        # this method allows us to do alternate backgrounds
        if checkin_date < date.today():
            row_style = ' style="background-color: #ba2d37"'
        else:
            row_style = ""

        table_body = """\
    <tr>
        <td{5}>{0}</td>
        <td{5}>{1}</td>
        <td{5}>{2}</td>
        <td{5}>{3}</td>
        <td{5}>{4}</td>
    </tr>
        """.format(server['hostname'], server['checkin'],
                server['security_patches'], server['bugfixes'], server['total_patches'], row_style)

        body += table_body
        
    # Concate all HTML output together
    html += '\n' + table_style
    html += '\n' + header
    html += '\n' + '<table class="nth-table">'
    html += '\n' + table_header
    html += '\n' + body
    html += '\n' + '</table>'
    html += '\n' + '</html>'

    return html


def main():
    # pull all information from API
    results = get_data(satellite_api + 'hosts')
    # pull total number of hosts
    total_hosts = results['total']
    # pull per_page value
    per_page = results['per_page']
    # test static per_page
#    per_page = 50
    # calculate total number of pages based on hosts/per_page
    pages = total_hosts // per_page

#    print("Display all hosts")
    page = 0

    # loop through pages to display all hosts and information
    # set organization to "Ivy Tech Community College"
    # filter requires "" within the string
    organization = '"Ivy Tech Community College"'


    # declare variable to be used later to email output
    server_output = []

    # loop through pages
    while (page < pages):
        page += 1
        host_info = return_info_for_hosts(satellite_api +
                'hosts?page=' +
                str(page) +
                '&search=organization=' +
                str(organization) +
                '&per_page=' +
                str(per_page))
        for servers in host_info:
            # Place server information into list for later use
            server_output.append(
                    {
                        'hostname': servers['hostname'],
                        'checkin': servers['last_checkin'],
                        'bugfixes': servers['bugfixes'],
                        'security_patches': servers['security_patches'],
                        'total_patches': servers['total_patches']
                    }
            )

    # input server list to get an HTML format output
    html_output = return_html_format(server_output)

    # create message to send via email
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Satellite Host Report"
    msg['From'] = from_address
    msg['To'] = to_address
    mail_body = MIMEText(html_output, 'html')
    msg.attach(mail_body)

    # Send via SMTP server
    smtp = smtplib.SMTP(mail_server)
    # sendmail
    smtp.sendmail(from_address, to_address, msg.as_string())
    smtp.quit()

if __name__ == "__main__":
    main()
