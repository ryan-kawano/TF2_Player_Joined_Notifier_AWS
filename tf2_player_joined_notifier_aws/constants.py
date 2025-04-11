"""Various constants used throughout the program.
"""

class Modes:
    THRESHOLD = "threshold"
    ALL = "all"

class Boto:
    SNS = "sns"
    DYNAMO_DB = "dynamodb"
    S3 = "s3"

class DynamoDB:
    PRIMARY_KEY = "name" # The primary key for the DynamoDB table that holds the player names
    PRIMARY_KEY_TYPE = "S" # S for String

class Environment:
    SERVER_IP = "SERVER_IP"
    DYNAMO_DB_TABLE = "DYNAMO_DB_TABLE"
    SNS_TOPIC_ARN = "SNS_TOPIC_ARN"
    PLAYER_COUNT_THRESHOLD = "PLAYER_COUNT_THRESHOLD"
    MIN_THRESHOLD = 0
    MAX_THRESHOLD = 100
    THRESHOLD_TIMER_MINUTES = "THRESHOLD_TIMER_MINUTES"
    MIN_TIMER_MINUTES = 2
    MAX_TIMER_MINUTES = 10080
    S3_BUCKET_NAME = "S3_BUCKET_NAME"

class StatusCodes:
    SUCCESS = 200
    FAILURE = 300

class Misc:
    PROJECT_NAME = "TF2 Player Joined Notifier"
    TIMER_FILE = "timer.txt" # The name of the file on S3 that will contain the target time that must be reached before sending a notification again.
    MINUTES_TO_SECONDS_MULTIPLIER = 60 # Multiplier to convert from minutes to seconds.
    EMAIL_SUBJECT_PREFIX = "[URGENT]" # Include "URGENT" in the email subject, so push notifications will get sent for it. Otherwise, it might not get flagged as important and a notification won't get sent.
