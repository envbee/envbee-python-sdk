"""
Example of using the envbee SDK to get a single variable.
"""

from envbee_sdk import Envbee

# Initialize application credentials
api_key = "1__local"  # Application and Environment ID
api_secret = b"key---1"  # Secret key for authentication

# Create an instance of the Envbee class
eb = Envbee(api_key, api_secret)

# Get a specific variable using the SDK
var1 = eb.get("DB_HOST")
print("Using envbee SDK - get_variable")
print(var1)
