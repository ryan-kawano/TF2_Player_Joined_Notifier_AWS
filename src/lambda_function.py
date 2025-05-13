"""The main AWS Lambda function. See the README.md file for more information.
"""
from src.internal.utility import (
    generate_return_message,
)
from src.internal import constants
from src.internal.config import Config
from src.modes.all_mode import all_mode
from src.modes.threshold_mode import threshold_mode


def lambda_handler(event, context):
    """Main function that will be run by Lambda.
    """
    print("Entered lambda_handler")

    if Config.get_env_variables() != 0:
        print("Error when retrieving environment variables.")
        return generate_return_message(constants.StatusCodes.FAILURE, "Error when retrieving environment variables")

    Config.verify_env_variables()

    if Config.MODE == constants.Modes.ALL:
        return all_mode()
    elif Config.MODE == constants.Modes.THRESHOLD:
        return threshold_mode()
