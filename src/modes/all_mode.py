"""ALL mode of operation.
"""
import boto3
from sourceserver.sourceserver import SourceServer

from ..internal import constants
from ..internal.config import Config
from ..internal.utility import (
    generate_return_message,
    format_server_info_to_string
)


def all_mode() -> dict:
    """Executes the application in "all" mode. It will send notifications for all players that join the server. It won't
    send repeat notifications for the same player unless they disconnect and join the server again, shortly after.

    :return: A status message of the result.
    :rtype: dict
    """
    print("Executing in ALL mode")

    print("Creating SNS and DynamoDB clients")
    sns_client = boto3.client(constants.Boto.SNS)
    dynamo_db_client = boto3.client(constants.Boto.DYNAMO_DB)

    print("Getting player info from the server")
    srv = SourceServer(Config.SERVER_IP)
    player_count, current_players = srv.getPlayers()
    server_name = srv.info.get("name")

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
        print("There are no players in the server and the database is empty. Ending program.")

        return generate_return_message(constants.StatusCodes.SUCCESS, "There were no players")
    # If there are no players, but there are names in the database, we need to clear the database
    elif player_count == 0 and not is_db_empty:
        print("There are no players in the server, but there are names in the database. Clearing database")
        for item in dynamo_db_data["Items"]:
            name = item[constants.DynamoDB.PRIMARY_KEY][constants.DynamoDB.PRIMARY_KEY_TYPE]
            print(f"Deleting item \"{name}\" from database")
            key = {constants.DynamoDB.PRIMARY_KEY: item[constants.DynamoDB.PRIMARY_KEY]}
            dynamo_db_client.delete_item(TableName=Config.DYNAMO_DB_TABLE, Key=key)
            print(f"Successfully deleted item \"{name}\" from database")

        return generate_return_message(constants.StatusCodes.SUCCESS, "There were no players in the server. Cleared database")
    # If there are more than 0 players, then process the data
    elif player_count > 0:
        print("There are players in the server. Processing player data")
        print(f"Current players: {current_player_names}")

        # Check if anyone disconnected and remove them from DB if they did
        if not is_db_empty:
            print("DB is not empty. Checking if any players disconnected")
            for item in dynamo_db_data["Items"]:
                name = item[constants.DynamoDB.PRIMARY_KEY][constants.DynamoDB.PRIMARY_KEY_TYPE]
                print(f"Checking if \"{name}\" disconnected")

                if name not in current_player_names:
                    print(f"Deleting item \"{name}\" from database")
                    key = {constants.DynamoDB.PRIMARY_KEY: {constants.DynamoDB.PRIMARY_KEY_TYPE: name}}
                    dynamo_db_client.delete_item(TableName=Config.DYNAMO_DB_TABLE, Key=key)
                    print(f"Successfully deleted item \"{name}\" from database")

        # Check if there are any new players by checking if they are in the database
        for name in current_player_names:
            key = {constants.DynamoDB.PRIMARY_KEY: {constants.DynamoDB.PRIMARY_KEY_TYPE: name}}
            response = dynamo_db_client.get_item(TableName=Config.DYNAMO_DB_TABLE, Key=key)
            if "Item" in response:
                print(f"Already sent notification for player \"{name}\"")
            else:
                print(f"Haven't sent notification for player \"{name}\" yet. Adding to pending list and creating entry in database")
                should_notify = True
                pending_player_names.append(name)
                item = {constants.DynamoDB.PRIMARY_KEY: {constants.DynamoDB.PRIMARY_KEY_TYPE : name}}
                print(f"Updating database with player \"{name}\"")
                response = dynamo_db_client.put_item(TableName=Config.DYNAMO_DB_TABLE, Item=item)
                print(f"Successfully updated database with player \"{name}\". Response: {response}")

    if not should_notify:
        print("Notification doesn't need to be sent. Ending program.")
        return generate_return_message(constants.StatusCodes.SUCCESS, "Notification doesn't need to be sent")

    print(f"Notification needs to be sent. Sending notifications for: {pending_player_names}")
    subject = f"{constants.Misc.EMAIL_SUBJECT_PREFIX}Player has joined the server"
    message = format_server_info_to_string(
        server_name=server_name,
        player_count=player_count,
        player_names=pending_player_names
    )
    sns_client.publish(
        TopicArn=Config.SNS_TOPIC_ARN,
        Subject=subject,
        Message=message
    )
    print("Sent notification")

    return generate_return_message(constants.StatusCodes.SUCCESS, "Email sent successfully")
