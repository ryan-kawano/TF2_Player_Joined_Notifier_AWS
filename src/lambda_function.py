"""The main AWS Lambda function. See the README.md file for more information.
"""
import os

from utility import (
    generate_return_message,
    get_env_variables,
    verify_env_variables
)
import constants
from config import Config
from all_mode import all_mode
from threshold_mode import threshold_mode

Config.MODE = os.environ["MODE"] # This value is always required, which is why it's retrieved here at the start.


def lambda_handler(event, context):
    """Main function that will be run by Lambda.
    """
    print("Entered lambda_handler")

    if Config.MODE != constants.Modes.ALL and Config.MODE != constants.Modes.THRESHOLD:
        print(
            f"Error, the mode \"{Config.MODE}\" is invalid. Please provide one in the variable \"MODE\" in "
            f"AWS Lambda's environment variables. The possible values are: \"{constants.Modes.ALL}\" and "
            f"\"{constants.Modes.THRESHOLD}\""
        )
        return generate_return_message(constants.StatusCodes.FAILURE, "Invalid mode")

    if get_env_variables(Config.MODE) != 0:
        print("Error when retrieving environment variables.")
        return generate_return_message(constants.StatusCodes.FAILURE, "Error when retrieving environment variables")

    verify_status_result = verify_env_variables(Config.MODE)
    if verify_status_result is not None:
        print("Error when verifying environment variables.")
        return verify_status_result

    if Config.MODE == constants.Modes.ALL:
        return all_mode()
    elif Config.MODE == constants.Modes.THRESHOLD:
        return threshold_mode()
