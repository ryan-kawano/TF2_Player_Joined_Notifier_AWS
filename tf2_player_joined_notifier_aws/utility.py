"""Holds various utility functions.
"""
from botocore.client import BaseClient
from constants import MINUTES_TO_SECONDS_MULTIPLIER, EMAIL_SUBJECT_PREFIX
from config import Config


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
