""" The main Lambda function. It will first retrieve a list of players on a server. If there are players, it will check
if notifications were already sent for those players by checking against a database. It will also check if, any players
that notifications were already sent for, in a previous iteration, disconnected. Then, when appropriate, it will send
an email notification saying that players have joined the server and a list of names.
"""

import os
import boto3
from sourceserver.sourceserver import SourceServer
from constants import PRIMARY_KEY, PRIMARY_KEY_TYPE

SERVER_IP = os.environ["SERVER_IP"]
DYNAMO_DB_TABLE = os.environ["DYNAMO_DB_TABLE"]
SNS_TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]

def lambda_handler(event, context):
    print("lambda_handler enter")

    if not SERVER_IP:
        print("Error, server ip was not provided. Please provide one in the variable \"SERVER_IP\", in constants.py")
        return {
            'statusCode': 300,
            'body': 'Missing server ip'
        }
    if not DYNAMO_DB_TABLE:
        print("Error, DynamoDb table name was not provided. Please provide one in the variable \"DYNAMO_DB_TABLE\", in constants.py")
        return {
            'statusCode': 300,
            'body': 'Missing DynamoDb table name'
        }
    if not SNS_TOPIC_ARN:
        print("Error, SNS topic ARN was not provided. Please provide one in the variable \"SNS_TOPIC_ARN\", in constants.py")
        return {
            'statusCode': 300,
            'body': 'Missing SNS ARN'
        }

    print("Creating SNS and DynamoDB clients")
    sns_client = boto3.client('sns')
    dynamo_db_client = boto3.client('dynamodb')

    print("Getting player info from server")
    srv = SourceServer(SERVER_IP)
    count, current_players = srv.getPlayers()

    # Save just the names in a list for easier access
    current_player_names = []
    for player in current_players:
        if player[1] != "":
            current_player_names.append(player[1])
    print(f"Player count: {count}")

    # Access database to get players that we have already sent notifications for in order to not send
    # duplicate notifications
    is_db_empty = None
    dynamo_db_data = dynamo_db_client.scan(TableName=DYNAMO_DB_TABLE)
    if "Items" in dynamo_db_data and len(dynamo_db_data["Items"]) > 0:
        is_db_empty = False
    else:
        is_db_empty = True

    pending_player_names = []  # Holds new players that we haven't sent notifications for
    should_notify = False
    # If there are no players and the database is empty, then no need to do anything
    if count == 0 and is_db_empty:
        print("There are no players in the server and the database is empty. Don't do anything.")

        return {
            'statusCode': 200,
            'body': 'There were no players'
        }
    # If there are no players, but there are names in the database, we need to clear the database
    elif count == 0 and not is_db_empty:
        print("There are no players in the server, but there are names in the database. Clearing database")
        for item in dynamo_db_data["Items"]:
            name = item[PRIMARY_KEY][PRIMARY_KEY_TYPE]
            print(f"Deleting item \"{name}\" from database")
            key = {PRIMARY_KEY: item[PRIMARY_KEY]}
            dynamo_db_client.delete_item(TableName=DYNAMO_DB_TABLE, Key=key)
            print(f"Successfully deleted item \"{name}\" from DB")

        return {
            'statusCode': 200,
            'body': 'There were no players. Cleared DB'
        }
    # If there are more than 0 players, then process the data
    elif count > 0:
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
                    dynamo_db_client.delete_item(TableName=DYNAMO_DB_TABLE, Key=key)
                    print(f"Successfully deleted item \"{name}\" from DB")

        # Check if there are any new players by checking if they are in the database
        for name in current_player_names:
            key = {PRIMARY_KEY: {PRIMARY_KEY_TYPE: name}}
            response = dynamo_db_client.get_item(TableName=DYNAMO_DB_TABLE, Key=key)
            if "Item" in response:
                print(f"Already sent notification for player \"{name}\"")
            else:
                print(f"Haven't sent notification for player \"{name}\" yet. Adding to pending list and creating entry in database")
                should_notify = True
                pending_player_names.append(name)
                item = { PRIMARY_KEY: { PRIMARY_KEY_TYPE : name } }
                print(f"Updating database with player \"{name}\"")
                response = dynamo_db_client.put_item(TableName=DYNAMO_DB_TABLE, Item=item)
                print(f"Finished updating database with player \"{name}\". Response: {response}")

    if not should_notify:
        return {
            'statusCode': 200,
            'body': 'Don\'t need to notify'
        }

    # Include "URGENT" in the email subject, so push notifications will get sent for it. Otherwise, it might not get
    # flagged as important and a notification won't get sent
    subject = "URGENT - Player has joined your server"
    message = "Players: \n"
    for name in pending_player_names:
        message += "[" + name + "]\n"

    sns_client.publish(
        TopicArn=SNS_TOPIC_ARN,
        Subject=subject,
        Message=message
    )

    return {
        'statusCode': 200,
        'body': 'Email sent successfully'
    }
