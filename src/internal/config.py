"""Configuration class.
"""
import os

from . import constants


class Config:
    """Holds various configuration values used by the application.
    """
    MODE: str = None # Possible values: "threshold" or "all". See README.md for explanation of modes.
    SERVER_IP: str = None # The IP of the server to query.
    DYNAMO_DB_TABLE: str = None # The name of the DynamoDB table that will hold the player names.
    SNS_TOPIC_ARN: str = None # The ARN of the SNS Topic to send notifications from.
    PLAYER_COUNT_THRESHOLD: int = None  # Minimum amount of players required to send a notification. Only for threshold mode.
    THRESHOLD_TIMER_MINUTES: int = None  # The amount of time to send before sending another notification. Only for threshold mode.
    S3_BUCKET_NAME: str = None  # Name of the bucket that will hold the timer's target time.

    class RequiredValue:
        def __init__(self, name: str, data_type: type, min_value: int = None, max_value: int = None):
            self.name: str = name
            self.data_type: type = data_type
            self.min_value: int = min_value
            self.max_value: int = max_value

    required_values_for_mode: dict[str, tuple[RequiredValue]] = {
        constants.Modes.ALL: (RequiredValue(constants.Environment.SERVER_IP, str),
                              RequiredValue(constants.Environment.DYNAMO_DB_TABLE, str),
                              RequiredValue(constants.Environment.SNS_TOPIC_ARN, str)
                              ),
        constants.Modes.THRESHOLD: (RequiredValue(constants.Environment.SERVER_IP, str),
                                    RequiredValue(constants.Environment.SNS_TOPIC_ARN, str),
                                    RequiredValue(
                                        constants.Environment.PLAYER_COUNT_THRESHOLD,
                                        int,
                                        constants.Environment.MIN_THRESHOLD,
                                        constants.Environment.MAX_THRESHOLD
                                    ),
                                    RequiredValue(
                                        constants.Environment.THRESHOLD_TIMER_MINUTES,
                                        int,
                                        constants.Environment.MIN_TIMER_MINUTES,
                                        constants.Environment.MAX_TIMER_MINUTES
                                    ),
                                    RequiredValue(constants.Environment.S3_BUCKET_NAME, str)
                                    )
    }

    @classmethod
    def get_env_variables(cls) -> int:
        """Retrieves the environment variables.

        :return: 0 if successful. -1 if failed.
        :rtype: int
        """
        cls.MODE = os.environ["MODE"]

        if cls.MODE == constants.Modes.ALL:
            print(f"Retrieving environment variables for \"{cls.MODE}\" mode")
            for req_value in cls.required_values_for_mode[cls.MODE]:
                name = req_value.name
                data_type = req_value.data_type
                value = os.environ[req_value.name]
                setattr(cls, name, data_type(value))
            return 0
        elif cls.MODE == constants.Modes.THRESHOLD:
            print(f"Retrieving environment variables for \"{cls.MODE}\" mode")
            for req_value in cls.required_values_for_mode[cls.MODE]:
                name = req_value.name
                data_type = req_value.data_type
                value = os.environ[req_value.name]
                setattr(cls, name, data_type(value))
            return 0
        else:
            error_message = (
                f"Error, the mode \"{cls.MODE}\" was invalid. Please provide one in the variable \"MODE\" in "
                f"AWS Lambda's environment variables. The possible values are: "
                f"{constants.Modes.possible_modes()}"
            )
            print(error_message)
            raise Exception(error_message)

    @classmethod
    def verify_env_variables(cls) -> dict | None:
        """Verifies environment variables by checking that they are present. For certain variables, it will also check
        whether they are within a valid range.

        :return: `None` if environment variables were valid, otherwise returns an error message.
        :rtype: None, dict
        """
        if cls.MODE not in vars(constants.Modes).values():
            error_message = f"Invalid mode provided"
            print(error_message)
            raise Exception(error_message)

        for req_value in cls.required_values_for_mode[cls.MODE]:
            attr = getattr(cls, req_value.name)
            if attr is None:
                error_message = (
                    f"Error, {req_value.name} was not provided. Please provide one in the Lambda environment"
                    f" variable: \"{req_value.name}\""
                )
                print(error_message)
                raise Exception(error_message)
            min_value = req_value.min_value
            if min_value is not None:
                if attr < min_value:
                    error_message = f"Error, \"{req_value.name}\"'s value \"{attr}\" was less than the min value \"{min_value}\""
                    print(error_message)
                    raise Exception(error_message)
            max_value = req_value.max_value
            if max_value is not None:
                if attr > max_value:
                    error_message = f"Error, \"{req_value.name}\"'s value \"{attr}\" was greater than the max value \"{max_value}\""
                    print(error_message)
                    raise Exception(error_message)
        return None
