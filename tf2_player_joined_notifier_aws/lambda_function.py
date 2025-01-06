""" File for the main Lambda function. See the README.md file for more information.
"""
import os
from utility import (
    generate_return_message,
    get_env_variables,
    verify_env_variables
)
from constants import (
    FAILURE_STATUS_CODE,
)
from config import Config
from all_mode import all_mode
from threshold_mode import threshold_mode
Config.MODE = os.environ["MODE"] # Possible values: "threshold" or "all". This value is always required, which is why we always retrieve it here, at the start.


def lambda_handler(event, context):
    """Main function that will be run by Lambda.
    """
    print("lambda_handler enter")

    if Config.MODE != "all" and Config.MODE != "threshold":
        print("Error, valid mode was not provided. Please provide one in the variable \"MODE\", in the Lambda's environment variables. The possible values are: \"all\" and \"threshold\"")
        return generate_return_message(FAILURE_STATUS_CODE, "Missing valid mode")

    if get_env_variables(Config.MODE) != 0:
        print("Error when retrieving environment variables.")
        return generate_return_message(FAILURE_STATUS_CODE, "Error when retrieving environment variables")

    verify_status_error = verify_env_variables(Config.MODE)
    if verify_status_error is not None:
        print("Error when verifying environment variables.")
        return verify_status_error

    if Config.MODE == "all":
        return all_mode()
    elif Config.MODE == "threshold":
        return threshold_mode()
