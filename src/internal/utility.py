"""Holds various utility functions.
"""
from botocore.client import BaseClient

from . import constants
from .time_type import TimeType


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
    return generate_return_message(constants.StatusCodes.FAILURE, error_message)


def send_email(sns_client: BaseClient, subject: str, message: str) -> None:
    """Sends an email using the SNS client with the provided subject and message.

    :param sns_client: The SNS client to send emails with.
    :type sns_client: BaseClient
    :param subject: The subject line of the email.
    :type subject: str
    :param message: The body of the email.
    :type message: str
    """
    from .config import Config

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
    :param player_names: The list of the names of the players in the server.
    :type: list[str]
    :param new_target_time: The new target time for the timer. Only applicable in "threshold" mode.
    :type: TimeType
    :return: The formatted string.
    :rtype: str
    """
    from .config import Config

    if Config.MODE == constants.Modes.ALL:
        player_names_formatted = ""
        for idx, name in enumerate(player_names):
            player_names_formatted += f"{idx + 1}: {name}\n"

        return (
            f"Player has joined the server\n\n"
            f"Server name: {server_name}\n"
            f"IP: {Config.SERVER_IP}\n"
            f"Player count: {player_count}\n\n"
            f"Player names:\n{player_names_formatted}")
    elif Config.MODE == constants.Modes.THRESHOLD:
        player_names_formatted = ""
        for idx, name in enumerate(player_names):
            player_names_formatted += f"{idx + 1}: {name}\n"

        return (
            f"The player count has reached the threshold: {Config.PLAYER_COUNT_THRESHOLD}\n\n"
            f"Server name: {server_name}\n"
            f"IP: {Config.SERVER_IP}\n"
            f"Player count: {player_count}\n\n"
            f"Player names:\n{player_names_formatted}\n\n"
            f"The next check will happen after {new_target_time.current_time_human_readable}\n"
        )
    else:
        return ""
