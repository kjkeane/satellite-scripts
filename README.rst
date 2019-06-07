==========
satellite-scripts
==========
Scripts used to manage Red Hat Satellite server.

Workflow
--------
This repository contains scripts used to manage different aspects of Red Hat Satellite 6.x.

cv-publish.py
-------------
This script will pull all Composite Content Views (CCVs) from the API.  Then for each CCV, it will promote them to each environment. This script makes the assumption that all CCVs are autopublishing when the Composite Views (CVs) are promoted.

Prerequisites
-------------
* Login user to Satellite
* Organization Name
* Python
* `python-requests <https://github.com/requests/requests>`_
* `python-requests-oauthlib <https://github.com/requests/requests-oauthlib>`_

Usage
-----
```
python cv-publish.py
```

Known Issues
------------
* All CCVs are published everytime the script is ran, even if they are not changed.  This can be improved by only publishing and promoting CCVs where any of the components have actually changed.

host-report.py
--------------
This script will pull all Content Hosts, format it into HTML and email it out.

Prerequisites
-------------
* Login use to Satellite
* Organization Name
* Python
* `python-requests <https://github.com/requests/requests>`_
* `python-requests-oauthlib <https://github.com/requests/requests-oauthlib`_

Usage
-----
```
python host-report.py
```

Known Issues
------------
* Currently does not support multiple `to_addresses`.  This can be improved by looping through the list provided.
