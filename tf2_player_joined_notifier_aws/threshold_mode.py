"""Threshold mode of operation.
"""
import time

import boto3
import botocore.client
from sourceserver.sourceserver import SourceServer

from utility import (
    convert_minutes_to_seconds,
    generate_return_message,
    handle_error,
    send_email,
    format_server_info_to_string
)
import constants
from timer import handle_timer_file_not_found
from config import Config
from time_type import TimeType


def threshold_mode() -> dict:
    """This mode will retrieve the player count from the server and will only send a notification if the player count is
    greater than or equal to the threshold.

    :return: A status message of the result.
    :rtype: dict
    """
    print("Executing in THRESHOLD mode")

    print("Creating SNS and S3 clients")
    sns_client = boto3.client(constants.Boto.SNS)
    s3_client = boto3.client(constants.Boto.S3)

    print("Checking if timer has finished i.e. the target time has passed")
    current_time = TimeType()
    print(f"Current time is {current_time.current_time_human_readable}")

    print("Retrieving target time from S3")
    try:
        s3_client.get_object(Bucket=Config.S3_BUCKET_NAME, Key=constants.Misc.TIMER_FILE)
        s3_client.download_file(Bucket=Config.S3_BUCKET_NAME, Key=constants.Misc.TIMER_FILE, Filename=f"/tmp/{constants.Misc.TIMER_FILE}")
    except Exception as e:
        # If the file doesn't exist on S3, create one and upload it
        if isinstance(e, botocore.client.ClientError) and e.response["Error"]["Code"] == "NoSuchKey":
            return handle_timer_file_not_found(s3_client, sns_client, current_time)
        else:
            return handle_error(sns_client, f"Caught exception when downloading timer file from S3. Exception: {e}")

    print("Extracting target time from the timer file and comparing it to current time")
    with open(f"/tmp/{constants.Misc.TIMER_FILE}", mode="r") as timer_file:
        # There should only be one line in the file, the target time
        target_time_sec = int(timer_file.readline())
        if not target_time_sec:
            return handle_error(sns_client, "Timer file was empty")
        print(
            f"Comparing time in timer file: {time.ctime(target_time_sec)} to current time: "
            f"{current_time.current_time_human_readable}. The difference is (current time - target time): "
            f"{round(((current_time.current_time_seconds_int - target_time_sec) / 3600.0), 2)} hours"
        )
        passed_target_time = current_time.current_time_seconds_int >= target_time_sec

    if not passed_target_time:
        print("We haven't passed the target time yet. No need to do anything.")
        return generate_return_message(
            constants.StatusCodes.SUCCESS,
            "We haven't passed the target time yet. No need to do anything."
        )
    else:
        print("We've passed the target time. Continuing with execution")

    print(f"Checking if there are players and if it's above the threshold value: {Config.PLAYER_COUNT_THRESHOLD}")
    print("Getting player info from server")
    srv = SourceServer(Config.SERVER_IP)
    player_count, current_players = srv.getPlayers()
    server_name = srv.info.get("name")

    # Save just the names in a list for easier access
    current_player_names = []
    for player in current_players:
        if player[1] != "":
            current_player_names.append(player[1])
    print(f"Player count: {player_count}")

    # Process based on player count relative to threshold
    if player_count == 0:
        print("There are no players in the server. No need to do anything.")
        return generate_return_message(constants.StatusCodes.SUCCESS, "There were no players")
    elif player_count < Config.PLAYER_COUNT_THRESHOLD:
        print(f"There are {player_count} players, but the threshold is {Config.PLAYER_COUNT_THRESHOLD}, so don't send an email")
        return generate_return_message(
            constants.StatusCodes.SUCCESS,
            f"There are {player_count} players, but the threshold is {Config.PLAYER_COUNT_THRESHOLD}, so don't send an email"
        )
    elif player_count >= Config.PLAYER_COUNT_THRESHOLD:
        print(f"There are {player_count} players and the threshold is {Config.PLAYER_COUNT_THRESHOLD}, so we need to send an email")

        # Add the timer value to the current time to get the target time
        new_target_time = TimeType()
        new_target_time.set_time(current_time.current_time_seconds_float + float(convert_minutes_to_seconds(Config.THRESHOLD_TIMER_MINUTES)))
        print(f"First, updating the timer file on S3 with the time {new_target_time.current_time_human_readable}")
        with open(f"/tmp/{constants.Misc.TIMER_FILE}", "w") as timer_file:
            timer_file.write(str(new_target_time.current_time_seconds_int))
        try:
            s3_client.upload_file(f"/tmp/{constants.Misc.TIMER_FILE}", Config.S3_BUCKET_NAME, constants.Misc.TIMER_FILE)
        except Exception as e:
            return handle_error(sns_client, f"Caught exception when uploading. Exception: {e}")
        print(f"Uploaded timer file to S3 with time {new_target_time.current_time_human_readable}")

        print("Sending email")
        subject = f"{constants.Misc.EMAIL_SUBJECT_PREFIX}Player count has reached the threshold"
        message = format_server_info_to_string(
            server_name=server_name,
            player_count=player_count,
            new_target_time=new_target_time
        )
        send_email(
            sns_client,
            subject=subject,
            message=message
        )
        print("Sent email")

        return generate_return_message(constants.StatusCodes.SUCCESS, "Email sent successfully")
