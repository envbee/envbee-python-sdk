# envbee Python SDK

envbee SDK is a Python client for interacting with the envbee API (see [https://envbee.dev](https://envbee.dev)).
This SDK provides methods to retrieve variables and manage caching for improved performance.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Environment Variables](#environment-variables)
- [Methods](#methods)
- [Encryption](#encryption)
- [Logging](#logging)
- [Caching](#caching)
- [API Documentation](#api-documentation)
- [License](#license)

## Installation

To install the envbee SDK, use pip:

```bash
pip install envbee-sdk
```

## Usage

Instantiate the `Envbee` class with your API credentials (either as parameters or via environment variables):

```python
from envbee_sdk import Envbee

client = Envbee(
    api_key="your_api_key",
    api_secret=b"your_api_secret",
    enc_key=b"32-byte-encryption-key-goes-here"  # optional, could be a string or a 32 bytes buffer
)

# Retrieve a variable
value = client.get("VariableName")

# Retrieve multiple variables
variables, metadata = client.get_variables()
```

## Environment Variables

Instead of passing credentials and configuration parameters directly when instantiating the `Envbee` client, you can optionally use environment variables:

- `ENVBEE_API_KEY`: your API key (required if `api_key` is not passed explicitly)
- `ENVBEE_API_SECRET`: your API secret (required if `api_secret` is not passed explicitly)
- `ENVBEE_ENC_KEY`: optional encryption key for decrypting encrypted variables

Example using environment variables:

```bash
export ENVBEE_API_KEY="your_api_key"
export ENVBEE_API_SECRET="your_api_secret"
export ENVBEE_ENC_KEY="32-byte-encryption-key-goes-here"
```

Then initialize the client with no parameters:

```python
from envbee_sdk import Envbee

client = Envbee()

value = client.get("VariableName")
```

Explicit parameters take precedence over environment variables if both are provided.

## Methods

- `get(variable_name: str) -> any`: fetch a variable value.
- `get_variables(offset: int = None, limit: int = None) -> tuple[list[dict], Metadata]`: fetch multiple variable definitions with pagination.

## Encryption

Some variables stored in envbee are encrypted using AES-256-GCM (via the [cryptography](https://cryptography.io/en/latest/) library). Encrypted values are prefixed with `envbee:enc:v1:`.

- If an encrypted variable is fetched and you provide a correct decryption key (`enc_key`), the SDK will decrypt it automatically.
- If no key or a wrong key is provided, a `RuntimeError` will be raised on decryption.
- The encryption key is never sent to the API; all decryption is performed locally.
- Cached values are stored exactly as received from the API (encrypted or plain-text).

Example with encryption key:

```python
client = Envbee(
    api_key="your_api_key",
    api_secret=b"your_api_secret",
    enc_key=b"32-byte-encryption-key-goes-here"
)
```

## Logging

Configure logging as needed. The SDK logger name is `envbee_sdk`. Example:

```python
import logging

logging.basicConfig(level=logging.ERROR)

sdk_logger = logging.getLogger("envbee_sdk")
sdk_logger.setLevel(logging.DEBUG)  # for detailed logs

# Example usage within the SDK
sdk_logger.debug("This is a debug message from the SDK.")
sdk_logger.info("Informational message from the SDK.")
```

## Caching

The SDK caches variables locally to provide fallback data when offline or the API is unreachable. The cache is updated after each successful API call. Local cache stores variables as received from the API, encrypted or plain.

- Encryption key is never stored in cache or sent to API.
- All encryption/decryption happens locally with AES-256-GCM.

## API Documentation

For more information on envbee API endpoints and usage, visit the [official API documentation](https://docs.envbee.dev).

## License

This project is licensed under the MIT License. See the LICENSE file for details.
