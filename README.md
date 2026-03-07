# envbee Python SDK

envbee SDK is a Python client for interacting with the envbee API (see [https://envbee.dev](https://envbee.dev)).
This SDK provides methods to retrieve variables,
manage caching for improved performance, and populate environment
variables directly from envbee.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Environment Variables](#environment-variables)
- [Methods](#methods)
- [Data Models](#data-models)
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

The SDK is tested with:

- Python 3.10
- Python 3.11
- Python 3.12
- Python 3.13
- Python 3.14

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

# Retrieve multiple variables definitions
variables, metadata = client.get_variables()
```

You can also retrieve variables along with their values:

```python
variables, metadata = client.get_variables_values()
```

Or automatically populate OS environment variables:

```python
client.fill_env_vars()
```

This will fetch all variables and set them in the current process as
environment variables.

You can also restrict which variables should be exported:

```python
client.fill_env_vars(["DATABASE_URL", "REDIS_URL"])
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

### get

```python
get(variable_name: str) -> Any
```

Fetch a variable value by name.\
If the API request fails, the SDK attempts to retrieve the value from
the local cache.

### get_variables

```python
get_variables(offset: int | None = None, limit: int | None = None) -> tuple[list[Variable], Metadata]
```

Fetch variable definitions from the API.

Supports pagination using `offset` and `limit`.

### get_variables_values

```python
get_variables_values(offset: int | None = None, limit: int | None = None) -> tuple[list[VariableValue], Metadata]
```

Fetch variables along with their stored values.

Supports pagination.

### fill_env_vars

```python
fill_env_vars(variable_names: list[str] | None = None) -> None
```

Fetch variables and set them as environment variables in the current
process.

Behavior:

- If `variable_names` is `None`, all variables are exported.
- If `variable_names` is provided, only those variables are exported.
- Encrypted values are automatically decrypted before being set.
- If the API is unavailable, the SDK attempts to load values from the
  local cache.

Environment variables are always stored as **strings**.

## Data Models

The SDK returns typed dataclasses defined in:

    envbee_sdk.model

These include:

- `Variable`
- `VariableValue`
- `Metadata`
- `VariableType`

Refer to the source file for the canonical definitions:

[`envbee_sdk/model.py`](envbee_sdk/model.py)

## Encryption

Some variables stored in envbee are encrypted using AES-256-GCM (via the [cryptography](https://cryptography.io/en/latest/) library). Encrypted values are prefixed with `envbee:enc:v1:`.

Behavior:

- If an encrypted variable is fetched and you provide a correct decryption key (`enc_key`), the SDK decrypts it automatically.
- If no key or an incorrect key is provided, a `RuntimeError` will be raised during decryption.
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
```

## Caching

The SDK caches variables locally to provide fallback data when:

- The API is unreachable
- The client is offline

The cache is updated after each successful API call.

Properties:

- Cached values are stored exactly as returned by the API.
- Encryption keys are **never stored in cache**.
- Decryption always happens locally.

## API Documentation

For more information on envbee API endpoints and usage, visit the [official API documentation](https://docs.envbee.dev).

## License

This project is licensed under the MIT License. See the LICENSE file for details.
