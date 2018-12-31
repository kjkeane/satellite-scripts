#!/usr/bin/env python
#
#
# This script assumes ALL Composite Content Views will auto-publish
# This script will publish all Content Views
# Excluding the ones set by EXCLUDED_CVS
# It will also promote all Composite Content Views to all environments
# Excluding the ones set by EXCLUDED_ENVS


import json
import sys
import time
from datetime import datetime
from pprint import pprint
try:
    import requests
except ImportError:
    print("Please install the python-requests module.")
    sys.exit(-1)
try:
    from requests_oauthlib import OAuth1
except ImportError:
    print("Please install the python-requests-oauthlib module.")
    sys.exit(-1)

# URL to your Satellite 6 server
SAT_URL = "https://satellite.example.com"
# URL for API
SAT_API = "%s/api/v2/" % SAT_URL
# Katello API
KAT_API = "%s/katello/api/" % SAT_URL
post_headers = {'content-type': 'application/json'}
# Satellite 6 OAuth credentials
oauth_secret = ""
oauth_key = ""
# Enable SSL
SSL_VERIFY = True
# organization
ORG_NAME = "ORGANIZATION NAME"
# Dictionary for lifecycle environments
ENVIRONMENTS = {}
# exclude these Content Views
EXCLUDED_CVS = ['rhel-5-base', 'rhel-6-hotfix', 'rhel-7-hotfix']
# exclude Lifecycle Environments
EXCLUDED_ENVS = ['Library']
# search string to list currently running publish/sync/promote tasks
promote_tasks = "/foreman_tasks/api/tasks?search=label+%3D+Actions%3A%3AKatello%3A%3AContentView%3A%3APromote+and+state+%3D+running"
publish_tasks = "/foreman_tasks/api/tasks?search=label+%3D+Actions%3A%3AKatello%3A%3AContentView%3A%3APublish+and+state+%3D+running"

# connect to Satellite API
def get_json(url):
    # connect and pull JSON data from Satellite API
    satellite = requests.get(url,
            auth=(OAuth1(oauth_key, oauth_secret)),
            verify=SSL_VERIFY)
    return satellite.json()

def post_json(url, json_data):
    # POST to given URL
    result = requests.post(
            url,
            data = json_data,
            auth=(OAuth1(oauth_key, oauth_secret)),
            verify=SSL_VERIFY,
            headers=post_headers)
    return result.json()

def wait_for_publish(seconds):
    # Wait for all publishing tasks to terminate. Search string is:
    # label = Actions::Katello::ContentView::Publish and state = running

    count = 0
    print("Waiting for publish tasks to finish...")

    # Make sure that the publish tasks gets the chance to appear before looking for them
    time.sleep(2)

    while get_json(SAT_URL + publish_tasks)["subtotal"] != 0:
        time.sleep(seconds)
        count += 1

    print("Finished waiting after " + str(seconds * count) + " seconds")

def wait_for_promote(seconds):
    # Wait for all promoting tasks to terminate. Search string is:
    # label = Actions::Katello::ContentView::Promote and state = running
    
    count = 0
    print("Waiting for promote tasks to finish...")
    # Make sure that the promote tasks gets the chance to appear before looking for them
    time.sleep(2)

    while get_json(SAT_URL + promote_tasks)['subtotal'] != 0:
        time.sleep(seconds)
        count += 1

    print("Finished waiting after " + str(seconds + count) + " seconds")

def return_org_id(url):
    org = get_json(url)
    # check for existing organizations
    if org.get('error', None):
        print("Error getting organization.")
        sys.exit(-1)

    # organization id
    org_id = org['id']

    return org_id

def return_ccv_content(url):
    # pull Composite Content View content
    # initalize empty list
    ccv_content = []
    ccvs_json = get_json(url)
    for ccv in ccvs_json['results']:
        ccv_id = ccv['id']
        ccv_latest_version = ccv['versions']
        ccv_name = ccv['name']
        for env in ccv['environments']:
            env_id = env['id']
            env_name = env['name']
            ccv_content.append(
                    {
                        'ccv_id': ccv_id,
                        'ccv_name': ccv_name,
                        'ccv_latest_version': ccv_latest_version[-1]['id'],
                        'env_id': env_id,
                        'env_name': env_name
                    }
            )
    # Sort based on 'env_id' because of the promotion restriction
    sorted_ccv_content = sorted(ccv_content, key=lambda k: k['env_id'])
    return sorted_ccv_content

def main():
    # pull organization JSON
    org = get_json(SAT_API + "organizations/" + ORG_NAME)

    # check for existing organizations
    if org.get('error', None):
        print("Error getting organization.")
        sys.exit(-1)

    # organization id
    org_id = org['id']

    # pull content views
    cvs_json = get_json(
        KAT_API +
        "organizations/" +
        str(org_id) +
        "/content_views?noncomposite=true&nondefault=true")

    # Publish new versions of CVs that have new content in the underlying repos
    published_cv_ids = []
    for cv in cvs_json['results']:
        if cv['name'] not in EXCLUDED_CVS:
            # print out the current time and Content View being published
            print(time.strftime('%Y-%m-%d %X') +
                " " +
                "Publish " + cv['name'])
            # publish the current Content View
            post_json(KAT_API +
                "content_views/" +
                str(cv['id']) +
                "/publish",
            json.dumps({'description': 'Automatic publish over API'}))
            # wait 10 seconds for each publish
            wait_for_publish(10)

    # pull Composite Content Views
    ccv_content = return_ccv_content(KAT_API +
            "organizations/" +
            str(org_id) +
            "/content_views?composite=true")

    # loop through Composite Content Views
    # promote them into all environments
    for info in ccv_content:
        if info['env_name'] not in EXCLUDED_ENVS:
            # Promote Content View to environment
            post_json(KAT_API +
                    "content_view_versions/" +
                    str(info['ccv_latest_version']) +
                    "/promote", json.dumps(
                        {
                            'environment_id': info['env_id'],
                            # force promotion because of restriction
                            'force': True
                        }
                        ))
            # print current time and which Content View was promoted
            print(time.strftime('%Y-%m-%d %X') +
                    " " +
                    "Promoted " +
                    str(info['ccv_name']) +
                    " " +
                    "to the " +
                    str(info['env_name']) +
                    " " +
                    "environment")
            # wait 5 seconds for each promotion
            wait_for_promote(5)

if __name__ == "__main__":
    main()

