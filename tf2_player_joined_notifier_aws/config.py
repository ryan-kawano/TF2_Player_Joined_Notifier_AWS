"""File for the Config class.
"""

class Config:
    """This class is meant to hold various configuration values used by the application.
    """
    MODE: str = None # Possible values: "threshold" or "all". This value is always required, which is why we always retrieve it here. See README.md for explanation of modes.
    SERVER_IP: str = None # The IP of the server to query.
    DYNAMO_DB_TABLE: str = None # The name of the DynamoDB table that will hold the player names.
    SNS_TOPIC_ARN: str = None # The ARN of the SNS Topic to send notifications from.
    PLAYER_COUNT_THRESHOLD: int = None  # Minimum amount of players required to send a notification. Only for threshold mode.
    THRESHOLD_TIMER_MINUTES: int = None  # The amount of time to send before sending another notification. Only for threshold mode.
    S3_BUCKET_NAME: str = None  # Name of the bucket that will hold the timer's target time.
