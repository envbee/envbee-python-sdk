# envbee SDK

envbee SDK is a Python client for interacting with the envbee API (see https://envbee.dev). This SDK provides methods to retrieve variables and manage caching for improved performance.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Methods](#methods)
- [Testing](#testing)
- [License](#license)

## Installation

To install the envbee SDK, use pip:

```bash
pip install envbee-sdk
```

## Usage

To use the envbee SDK, instantiate the envbee class with your API credentials:

```python
from envbee_sdk.main import Envbee

eb = Envbee(api_key="your_api_key", api_secret=b"your_api_secret")

# Retrieve a variable
value = eb.get_variable("VariableName")

# Retrieve multiple variables
variables = eb.get_variables()
```

## Methods

### `get_variable(variable_name: str) -> str`

Fetches the value of a variable by its name. If the API request fails, it retrieves the value from the cache.

### `get_variables(offset: int = None, limit: int = None) -> list[dict]`

Fetches a list of variables from the API with optional pagination parameters.

### Caching

The SDK uses local caching to store variable values, improving efficiency by reducing API calls.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
