""" The main Lambda function. It will first retrieve a list of players on a server. If there are players, it will check
if notifications were already sent for those players by checking against a database. It will also check if, any players
that notifications were already sent for, in a previous iteration, disconnected. Then, when appropriate, it will send
an email notification saying that players have joined the server and a list of names.
"""

import os
import time
import boto3
import botocore.client
from utility import (
    convert_minutes_to_seconds,
    generate_return_message,
    handle_error,
    send_email
)
from constants import (
    PRIMARY_KEY,
    PRIMARY_KEY_TYPE,
    SUCCESS_STATUS_CODE,
    FAILURE_STATUS_CODE,
    TIMER_FILE,
    EMAIL_SUBJECT_PREFIX
)
from timer import handle_timer_file_not_found
from sourceserver.sourceserver import SourceServer
from config import Config
from time_type import TimeType

Config.MODE = os.environ["MODE"] # Possible values: "threshold" or "all". This value is always required, which is why we always retrieve it here.


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
        elif not Config.THRESHOLD_TIMER_MINUTES or not 0 <= Config.THRESHOLD_TIMER_MINUTES <= 120:
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


def all_mode():
    print("Creating SNS and DynamoDB clients")
    sns_client = boto3.client('sns')
    dynamo_db_client = boto3.client('dynamodb')

    print("Getting player info from server")
    srv = SourceServer(Config.SERVER_IP)
    player_count, current_players = srv.getPlayers()

    # Save just the names in a list for easier access
    current_player_names = []
    for player in current_players:
        if player[1] != "":
            current_player_names.append(player[1])
    print(f"Player count: {player_count}")

    # Access database to get players that we have already sent notifications for in order to not send
    # duplicate notifications
    is_db_empty = None
    dynamo_db_data = dynamo_db_client.scan(TableName=Config.DYNAMO_DB_TABLE)
    if "Items" in dynamo_db_data and len(dynamo_db_data["Items"]) > 0:
        is_db_empty = False
    else:
        is_db_empty = True

    pending_player_names = []  # Holds new players that we haven't sent notifications for
    should_notify = False
    # If there are no players and the database is empty, then no need to do anything
    if player_count == 0 and is_db_empty:
        print("There are no players in the server and the database is empty. Don't do anything.")

        return {
            'statusCode': 200,
            'body': 'There were no players'
        }
    # If there are no players, but there are names in the database, we need to clear the database
    elif player_count == 0 and not is_db_empty:
        print("There are no players in the server, but there are names in the database. Clearing database")
        for item in dynamo_db_data["Items"]:
            name = item[PRIMARY_KEY][PRIMARY_KEY_TYPE]
            print(f"Deleting item \"{name}\" from database")
            key = {PRIMARY_KEY: item[PRIMARY_KEY]}
            dynamo_db_client.delete_item(TableName=Config.DYNAMO_DB_TABLE, Key=key)
            print(f"Successfully deleted item \"{name}\" from DB")

        return {
            'statusCode': 200,
            'body': 'There were no players. Cleared DB'
        }
    # If there are more than 0 players, then process the data
    elif player_count > 0:
        print("There are players in the server")
        print(f"Current players: {current_player_names}")

        # Check if anyone disconnected and remove them from DB if they did
        if not is_db_empty:
            print("DB is not empty. Checking if anyone disconnected")
            for item in dynamo_db_data["Items"]:
                name = item[PRIMARY_KEY][PRIMARY_KEY_TYPE]
                print(f"Checking if \"{name}\" disconnected")

                if name not in current_player_names:
                    print(f"Deleting item \"{name}\" from DB")
                    key = {PRIMARY_KEY: {PRIMARY_KEY_TYPE: name}}
                    dynamo_db_client.delete_item(TableName=Config.DYNAMO_DB_TABLE, Key=key)
                    print(f"Successfully deleted item \"{name}\" from DB")

        # Check if there are any new players by checking if they are in the database
        for name in current_player_names:
            key = {PRIMARY_KEY: {PRIMARY_KEY_TYPE: name}}
            response = dynamo_db_client.get_item(TableName=Config.DYNAMO_DB_TABLE, Key=key)
            if "Item" in response:
                print(f"Already sent notification for player \"{name}\"")
            else:
                print(f"Haven't sent notification for player \"{name}\" yet. Adding to pending list and creating entry in database")
                should_notify = True
                pending_player_names.append(name)
                item = { PRIMARY_KEY: { PRIMARY_KEY_TYPE : name } }
                print(f"Updating database with player \"{name}\"")
                response = dynamo_db_client.put_item(TableName=Config.DYNAMO_DB_TABLE, Item=item)
                print(f"Finished updating database with player \"{name}\". Response: {response}")

    if not should_notify:
        return {
            'statusCode': 200,
            'body': 'Don\'t need to notify'
        }

    subject = f"{EMAIL_SUBJECT_PREFIX}Player has joined your server"
    message = "Players: \n"
    for name in pending_player_names:
        message += "[" + name + "]\n"
    sns_client.publish(
        TopicArn=Config.SNS_TOPIC_ARN,
        Subject=subject,
        Message=message
    )

    return {
        'statusCode': 200,
        'body': 'Email sent successfully'
    }


def threshold_mode():
    """This mode will retrieve the player count from the server and will only send a notification if the player count is
    greater than or equal to the threshold.
    """
    print("Creating SNS and S3 clients")
    sns_client = boto3.client('sns')
    s3_client = boto3.client('s3')

    print("Checking if timer has finished i.e. the target time has passed")
    print("Getting current time")
    current_time = TimeType()
    print(f"Current time is {current_time.current_time_human_readable}")

    print("Retrieving target time from S3")
    try:
        s3_client.get_object(Bucket=Config.S3_BUCKET_NAME, Key=TIMER_FILE)
        s3_client.download_file(Bucket=Config.S3_BUCKET_NAME, Key=TIMER_FILE, Filename=f'/tmp/{TIMER_FILE}')
    except Exception as e:
        # If the file doesn't exist on S3, create one and upload it
        if isinstance(e, botocore.client.ClientError) and e.response["Error"]["Code"] == "NoSuchKey":
            return handle_timer_file_not_found(s3_client, sns_client, current_time)
        else:
            return handle_error(sns_client, f"Caught exception when downloading timer file from S3. Exception: {e}")

    print("Extracting target time from the timer file and comparing it to current time")
    with open(f"/tmp/{TIMER_FILE}", mode="r") as timer_file:
        # There should only be one line in the file, the target time
        target_time = int(timer_file.readline())
        if not target_time:
            return handle_error(sns_client, "Timer file was empty")
        print(f"Comparing time in timer file: {time.ctime(target_time)} to current time: {current_time.current_time_human_readable}. The difference is (target time - current time): {round(abs((target_time - current_time.current_time_seconds_int) / 3600.0), 2)} hours")
        passed_target_time = current_time.current_time_seconds_int >= target_time

    if not passed_target_time:
        print("We haven't passed the target time yet. Don't do anything.")
        return generate_return_message(200, "We haven't passed the target time yet. Don't do anything.")
    else:
        print("We've passed the target time")

    print(f"Checking if there are players and if it's above the threshold value: {Config.PLAYER_COUNT_THRESHOLD}")
    print("Getting player info from server")
    srv = SourceServer(Config.SERVER_IP)
    player_count, current_players = srv.getPlayers()

    # Save just the names in a list for easier access
    current_player_names = []
    for player in current_players:
        if player[1] != "":
            current_player_names.append(player[1])
    print(f"Player count: {player_count}")

    # Process based on player count relative to threshold
    if player_count == 0:
        print("There are no players in the server. Don't do anything.")

        return {
            'statusCode': 200,
            'body': 'There were no players'
        }
    elif player_count < Config.PLAYER_COUNT_THRESHOLD:
        print(f"There are {player_count} players, but the threshold is {Config.PLAYER_COUNT_THRESHOLD}, so don't send an email")

        return {
            'statusCode': 200,
            'body': f"There are {player_count} players, but the threshold is {Config.PLAYER_COUNT_THRESHOLD}, so don't send an email"
        }
    elif player_count >= Config.PLAYER_COUNT_THRESHOLD:
        print(f"There are {player_count} players and the threshold is {Config.PLAYER_COUNT_THRESHOLD}, so we need to send an email")

        # Add the timer value to the current time to get the target time
        new_target_time = TimeType()
        new_target_time.set_time(current_time.current_time_seconds_float + float(convert_minutes_to_seconds(Config.THRESHOLD_TIMER_MINUTES)))
        print(f"Updating the timer file on S3 with the time {new_target_time.current_time_human_readable} first")
        with open(f"/tmp/{TIMER_FILE}", "w") as timer_file:
            timer_file.write(str(new_target_time.current_time_seconds_int))
        try:
            s3_client.upload_file(f"/tmp/{TIMER_FILE}", Config.S3_BUCKET_NAME, TIMER_FILE)
        except Exception as e:
            return handle_error(sns_client, f"Caught exception when uploading. Exception: {e}")
        print(f"Uploaded timer file to S3 with time {new_target_time.current_time_human_readable}")

        subject = f"{EMAIL_SUBJECT_PREFIX}Player count has reached the threshold"
        message = f"Players count is {player_count} in server {Config.SERVER_IP}. The next check will happen after {new_target_time.current_time_human_readable}\n"
        send_email(sns_client,
                   subject=subject,
                   message=message)

        return generate_return_message(SUCCESS_STATUS_CODE, "Email sent successfully")
