"""
Example of using the envbee SDK to get multiple variables.
"""

from envbee_sdk import Envbee

# Initialize application credentials
api_key = "1__local"  # Application and Environment ID
api_secret = b"key---1"  # Secret key for authentication

# Create an instance of the Envbee class
eb = Envbee(api_key, api_secret)

# Get all variables using the SDK
print("Using envbee SDK - get_variables")
for v in eb.get_variables():
    print(v)
