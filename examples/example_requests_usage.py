"""
Example of manually using requests to interact with the envbee API.
"""

import hashlib
import hmac
import json
import time

import requests

# Initialize application credentials
api_key = "1__local"  # Application and Environment ID
api_secret = b"key---1"  # Secret key for authentication
url_server = "http://app.envbee.dev"  # Base URL for the API
url_path = b"/variables"  # API endpoint for fetching variables

# Create HMAC object for authentication
hmac_obj = hmac.new(api_secret, digestmod=hashlib.sha256)
current_time = str(int(time.time() * 1000))  # Current time in milliseconds

# Update the HMAC object with request details
hmac_obj.update(current_time.encode("utf-8"))
hmac_obj.update(b"GET")
hmac_obj.update(url_path)

# Prepare the content for hashing
content = json.dumps({}).encode("utf-8")
content_hash = hashlib.md5()
content_hash.update(content)
hmac_obj.update(content_hash.hexdigest().encode("utf-8"))

# Build the authorization header
auth_header = "HMAC %s:%s" % (current_time, hmac_obj.hexdigest())
final_url = f"{url_server}{url_path.decode()}"  # Complete URL for the request

# Send the GET request to the API
content = requests.get(
    final_url, headers={"Authorization": auth_header, "x-api-key": api_key}
)

# Check the response status and print the result
if content.status_code == 200:
    print(content.json())  # Print the JSON response if successful
else:
    print(content)  # Print the response object
    print(content.text)  # Print the error message if the request failed
