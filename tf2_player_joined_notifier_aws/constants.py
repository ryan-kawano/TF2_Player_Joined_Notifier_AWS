"""File that contains various constants used throughout the program
"""
PRIMARY_KEY = "name" # The primary key for the DynamoDB table that holds the player names
PRIMARY_KEY_TYPE = "S" # S for String
SUCCESS_STATUS_CODE = 200
FAILURE_STATUS_CODE = 300
TIMER_FILE = "timer.txt" # The name of the file on S3 that will contain the target time that must be reached before sending a notification again.
MINUTES_TO_SECONDS_MULTIPLIER = 60 # Multiplier to convert from minutes to seconds.
EMAIL_SUBJECT_PREFIX = "[URGENT]" # Include "URGENT" in the email subject, so push notifications will get sent for it. Otherwise, it might not get flagged as important and a notification won't get sent.
