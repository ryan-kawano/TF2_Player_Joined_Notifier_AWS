"""Holds various utility functions.
"""
import os
from botocore.client import BaseClient
from constants import MINUTES_TO_SECONDS_MULTIPLIER, EMAIL_SUBJECT_PREFIX, FAILURE_STATUS_CODE
from config import Config
from time_type import TimeType

def get_env_variables(mode) -> int:
    """Retrieves the environment variables.

    :param mode: The mode of execution that was set in the MODE environment variable.
    :type mode: str
    :return: 0 if successful. 1 if failed.
    :rtype: int
    """
    if mode == "all":
        print("Retrieving environment variables for \"all\" mode")
        Config.SERVER_IP = os.environ["SERVER_IP"]
        Config.DYNAMO_DB_TABLE = os.environ["DYNAMO_DB_TABLE"]
        Config.SNS_TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]
        return 0
    elif mode == "threshold":
        print("Retrieving environment variables for threshold mode")
        Config.SERVER_IP = os.environ["SERVER_IP"]
        Config.SNS_TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]
        Config.PLAYER_COUNT_THRESHOLD = int(os.environ["PLAYER_COUNT_THRESHOLD"])
        Config.THRESHOLD_TIMER_MINUTES = int(os.environ["THRESHOLD_TIMER_MINUTES"])
        Config.S3_BUCKET_NAME = os.environ["S3_BUCKET_NAME"]
        return 0
    else:
        print("Invalid mode provided.")
        return -1


def verify_env_variables(mode) -> dict | None:
    """Verifies environment variables by checking that they are present. For certain variables, it will also check
    whether they are within a valid range.

    :param mode: The mode of execution that was set in the MODE environment variable.
    :type mode: str
    :return: `None` if environment variables were valid. An error message if they weren't valid.
    :rtype: None, dict
    """
    if mode == "all":
        if not Config.SERVER_IP:
            print("Error, server ip was not provided. Please provide one in the variable \"SERVER_IP\", in the Lambda's environment variables")
            return generate_return_message(FAILURE_STATUS_CODE, "Missing server ip")
        elif not Config.DYNAMO_DB_TABLE:
            print("Error, DynamoDb table name was not provided. Please provide one in the variable \"DYNAMO_DB_TABLE\", in the Lambda's environment variables")
            return generate_return_message(FAILURE_STATUS_CODE, "Missing DynamoDb table name")
        elif not Config.SNS_TOPIC_ARN:
            print("Error, SNS topic ARN was not provided. Please provide one in the variable \"SNS_TOPIC_ARN\", in the Lambda's environment variables")
            return generate_return_message(FAILURE_STATUS_CODE, "Missing SNS ARN")
        else:
            return None
    elif mode == "threshold":
        if not Config.SERVER_IP:
            print(
                "Error, server ip was not provided. Please provide one in the variable \"SERVER_IP\", in the Lambda's environment variables")
            return generate_return_message(FAILURE_STATUS_CODE, "Missing server ip")
        elif not Config.SNS_TOPIC_ARN:
            print(
                "Error, SNS topic ARN was not provided. Please provide one in the variable \"SNS_TOPIC_ARN\", in the Lambda's environment variables")
            return generate_return_message(FAILURE_STATUS_CODE, "Missing SNS ARN")
        elif not Config.PLAYER_COUNT_THRESHOLD or not 0 <= Config.PLAYER_COUNT_THRESHOLD <= 100:
            print(
                "Error, valid player count threshold was not provided. Please provide one in the variable \"PLAYER_COUNT_THRESHOLD\", in the Lambda's environment variables, with a number between 0 and 100 (0 means disabled)")
            return generate_return_message(FAILURE_STATUS_CODE, "Missing player count threshold")
        elif not Config.THRESHOLD_TIMER_MINUTES or not 2 <= Config.THRESHOLD_TIMER_MINUTES <= 10080:
            print(
                "Error, valid threshold timer value was not provided. Please provide one in the variable \"THRESHOLD_TIMER_MINUTES\", in the Lambda's environment variables, with a number between 0 and 100 (0 means disabled)")
            return generate_return_message(FAILURE_STATUS_CODE, "Missing valid threshold timer")
        elif not Config.S3_BUCKET_NAME:
            print(
                "Error, S3 bucket name was not provided. Please provide one in the variable \"S3_BUCKET_NAME\", in the Lambda's environment variables")
            return generate_return_message(FAILURE_STATUS_CODE, "Missing S3 bucket name")
        else:
            return None
    else:
        return generate_return_message(FAILURE_STATUS_CODE, "No mode passed in to verify_env_variables")


def handle_error(sns_client, error_message) -> dict:
    """Handles errors by sending an email of the error and generating an error return-message.

    :param sns_client: The SNS client to send emails with.
    :type sns_client: BaseClient
    :param error_message: The message to display in the email and the error return-message.
    :type error_message: str
    :return: A return message, meant for use with "return" in the main lambda function.
    :rtype: dict
    """
    print(error_message)
    send_email(sns_client,
               subject=f"{EMAIL_SUBJECT_PREFIX}TF2 Update Notifier had an error",
               message=error_message)
    return generate_return_message(300, error_message)


def send_email(sns_client, subject: str, message: str) -> None:
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
    return minutes * MINUTES_TO_SECONDS_MULTIPLIER


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
    if Config.MODE == "all":
        output: str = (
            f"Player has joined the server\n\n"
            f"Server name: {server_name}\n"
            f"IP: {Config.SERVER_IP}\n"
            f"Player count: {player_count}\n"
            f"Player names:\n"
        )
        for name in player_names:
            output += "[" + name + "]\n"
        return output
    elif Config.MODE == "threshold":
        output: str = (
            f"The player count has reached the threshold: {Config.PLAYER_COUNT_THRESHOLD}\n\n"
            f"Server name: {server_name}\n"
            f"IP: {Config.SERVER_IP}\n"
            f"Player count: {player_count}\n\n"
            f"The next check will happen after {new_target_time.current_time_human_readable}\n"
        )
        return output
    else:
        return ""
