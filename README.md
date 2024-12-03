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
variables, metadata = eb.get_variables()
```

### Logging

The root logger name is "envbee_sdk". You can configure the default logging level for the SDK and handle logs as needed. Here's an example of how to set up basic logging for your application using the SDK:

```python
# Basic logging configuration for your application
logging.basicConfig(
    level=logging.ERROR,  # Set default log level for the root logger
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],  # Send logs to stdout
)

# Get the SDK logger (specific to envbee_sdk)
sdk_logger = logging.getLogger("envbee_sdk")
sdk_logger.setLevel(logging.DEBUG)  # You can set the SDK logger to DEBUG for detailed logs

# Example usage within the SDK
sdk_logger.debug("This is a debug message from the SDK.")
sdk_logger.info("Informational message from the SDK.")
```

## Methods

### `get_variable(variable_name: str) -> str`

Fetches the value of a variable by its name. If the API request fails, it retrieves the value from the cache.

### `get_variables(offset: int = None, limit: int = None) -> tuple[list[dict], Metadata]`

Fetches a list of variables from the API with optional pagination parameters.

### Caching

The SDK uses local caching to store variable values, improving efficiency by reducing API calls.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
