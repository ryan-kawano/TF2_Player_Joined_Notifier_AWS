"""Holds various utility functions.
"""
import os
from botocore.client import BaseClient
import constants
from config import Config
from time_type import TimeType

def get_env_variables(mode: str) -> int:
    """Retrieves the environment variables.

    :param mode: The mode of execution that was set in the MODE environment variable.
    :type mode: str
    :return: 0 if successful. 1 if failed.
    :rtype: int
    """
    if mode == constants.Modes.ALL:
        print(f"Retrieving environment variables for \"{constants.Modes.ALL}\" mode")
        Config.SERVER_IP = os.environ[constants.Environment.SERVER_IP]
        Config.DYNAMO_DB_TABLE = os.environ[constants.Environment.DYNAMO_DB_TABLE]
        Config.SNS_TOPIC_ARN = os.environ[constants.Environment.SNS_TOPIC_ARN]
        return 0
    elif mode == constants.Modes.THRESHOLD:
        print(f"Retrieving environment variables for \"{constants.Modes.THRESHOLD}\" mode")
        Config.SERVER_IP = os.environ[constants.Environment.SERVER_IP]
        Config.SNS_TOPIC_ARN = os.environ[constants.Environment.SNS_TOPIC_ARN]
        Config.PLAYER_COUNT_THRESHOLD = int(os.environ[constants.Environment.PLAYER_COUNT_THRESHOLD])
        Config.THRESHOLD_TIMER_MINUTES = int(os.environ[constants.Environment.THRESHOLD_TIMER_MINUTES])
        Config.S3_BUCKET_NAME = os.environ[constants.Environment.S3_BUCKET_NAME]
        return 0
    else:
        print("Invalid mode provided.")
        return -1


def verify_env_variables(mode: str) -> dict | None:
    """Verifies environment variables by checking that they are present. For certain variables, it will also check
    whether they are within a valid range.

    :param mode: The mode of execution that was set in the MODE environment variable.
    :type mode: str
    :return: `None` if environment variables were valid. An error message if they weren't valid.
    :rtype: None, dict
    """
    if mode == constants.Modes.ALL:
        if not Config.SERVER_IP:
            print(
                f"Error, server ip was not provided. Please provide one in the Lambda environment variable "
                f"\"{constants.Environment.SERVER_IP}\""
            )
            return generate_return_message(constants.StatusCodes.FAILURE, "Missing server ip")
        elif not Config.DYNAMO_DB_TABLE:
            print(
                f"Error, DynamoDB table name was not provided. Please provide one in the Lambda environment variable "
                f"\"{constants.Environment.DYNAMO_DB_TABLE}\""
            )
            return generate_return_message(constants.StatusCodes.FAILURE, "Missing DynamoDB table name")
        elif not Config.SNS_TOPIC_ARN:
            print(
                f"Error, SNS topic ARN was not provided. Please provide one in the Lambda environment variable "
                f"\"{constants.Environment.SNS_TOPIC_ARN}\""
            )
            return generate_return_message(constants.StatusCodes.FAILURE, "Missing SNS ARN")
        else:
            return None
    elif mode == constants.Modes.THRESHOLD:
        if not Config.SERVER_IP:
            print(
                f"Error, server ip was not provided. Please provide one in the Lambda environment variable "
                f"\"{constants.Environment.SERVER_IP}\""
            )
            return generate_return_message(constants.StatusCodes.FAILURE, "Missing server ip")
        elif not Config.SNS_TOPIC_ARN:
            print(
                f"Error, SNS topic ARN was not provided. Please provide one in the Lambda environment variable "
                f"\"{constants.Environment.SNS_TOPIC_ARN}\""
            )
            return generate_return_message(constants.StatusCodes.FAILURE, "Missing SNS Topic ARN")
        elif (
                not Config.PLAYER_COUNT_THRESHOLD
                or not constants.Environment.MIN_THRESHOLD <= Config.PLAYER_COUNT_THRESHOLD <= constants.Environment.MAX_THRESHOLD
        ):
            print(
                f"Error, valid player count threshold was not provided. Please provide one in the Lambda environment "
                f"variable \"{constants.Environment.PLAYER_COUNT_THRESHOLD}\" with a "
                f"number between {constants.Environment.MIN_THRESHOLD} and {constants.Environment.MAX_THRESHOLD} "
                f"({constants.Environment.MIN_THRESHOLD} meaning disabled)"
            )
            return generate_return_message(constants.StatusCodes.FAILURE, "Missing player count threshold")
        elif (
                not Config.THRESHOLD_TIMER_MINUTES
                or not constants.Environment.MIN_TIMER_MINUTES <= Config.THRESHOLD_TIMER_MINUTES <= constants.Environment.MAX_TIMER_MINUTES
        ):
            print(
                f"Error, valid threshold timer value was not provided. Please provide one in the Lambda environment "
                f"variable \"{constants.Environment.THRESHOLD_TIMER_MINUTES}\" with a "
                f"number between {constants.Environment.MIN_TIMER_MINUTES} and {constants.Environment.MAX_TIMER_MINUTES} "
                f"({constants.Environment.MIN_THRESHOLD} meaning disabled)")
            return generate_return_message(constants.StatusCodes.FAILURE, "Missing valid threshold timer")
        elif not Config.S3_BUCKET_NAME:
            print(
                f"Error, S3 bucket name was not provided. Please provide one in the Lambda environment variable "
                f"\"{constants.Environment.S3_BUCKET_NAME}\""
            )
            return generate_return_message(constants.StatusCodes.FAILURE, "Missing S3 bucket name")
        else:
            return None
    else:
        return generate_return_message(constants.StatusCodes.FAILURE, "No mode passed in to verify_env_variables")


def handle_error(sns_client: BaseClient, error_message: str) -> dict:
    """Handles errors by sending an email of the error and generating an error return-message.

    :param sns_client: The SNS client to send emails with.
    :type sns_client: BaseClient
    :param error_message: The message to display in the email and the error return-message.
    :type error_message: str
    :return: A return message, meant for use with "return" in the main lambda function.
    :rtype: dict
    """
    print(error_message)
    send_email(
        sns_client,
        subject=f"{constants.Misc.EMAIL_SUBJECT_PREFIX}{constants.Misc.PROJECT_NAME} had an error",
        message=error_message
    )
    return generate_return_message(300, error_message)


def send_email(sns_client: BaseClient, subject: str, message: str) -> None:
    """Sends an email using the SNS client with the provided subject and message.

    :param sns_client: The SNS client to send emails with.
    :type sns_client: BaseClient
    :param subject: The subject line of the email.
    :type subject: str
    :param message: The body of the email.
    :type message: str
    """
    sns_client.publish(
        TopicArn=Config.SNS_TOPIC_ARN,
        Subject=subject,
        Message=message
    )


def generate_return_message(status_code: int, status_body: str) -> dict:
    """Generates a status message in order to return it from the main lambda function.

    :param status_code: The numerical status code.
    :type status_code: int
    :param status_body: The text that gives information about the status.
    :type status_body: str
    :return: A status message.
    :rtype: dict
    """
    return {
        'statusCode': status_code,
        'body': status_body
    }


def convert_minutes_to_seconds(minutes: int) -> int:
    """Converts minutes to seconds.

    :param minutes: The time in minutes to convert.
    :type minutes: float
    :return: The time converted to seconds.
    :rtype: float
    """
    return minutes * constants.Misc.MINUTES_TO_SECONDS_MULTIPLIER


def format_server_info_to_string(server_name: str, player_count: int = None, player_names: list[str] = None, new_target_time: TimeType = None):
    """Formats the provided server details into an easy-to-read, formatted string. Used in the body the email notification. Depending on the mode, only
    certain parameters are required and others can be omitted.

    :param server_name: The name of the server.
    :type: str
    :param player_count: The amount of players in the server.
    :type: int
    :param player_names: The list of the names of the players in the server. Only applicable in "all" mode.
    :type: list[str]
    :param new_target_time: The new target time for the timer. Only applicable in "threshold" mode.
    :type: TimeType
    :return: The formatted string.
    :rtype: str
    """
    if Config.MODE == constants.Modes.ALL:
        output = (
            f"Player has joined the server\n\n"
            f"Server name: {server_name}\n"
            f"IP: {Config.SERVER_IP}\n"
            f"Player count: {player_count}\n"
            f"Player names:\n"
        )
        for name in player_names:
            output += "[" + name + "]\n"
        return output
    elif Config.MODE == constants.Modes.THRESHOLD:
        output = (
            f"The player count has reached the threshold: {Config.PLAYER_COUNT_THRESHOLD}\n\n"
            f"Server name: {server_name}\n"
            f"IP: {Config.SERVER_IP}\n"
            f"Player count: {player_count}\n\n"
            f"The next check will happen after {new_target_time.current_time_human_readable}\n"
        )
        return output
    else:
        return ""
