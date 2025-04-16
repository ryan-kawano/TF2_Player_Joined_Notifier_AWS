"""Timer related functions
"""
from botocore.client import BaseClient

import constants
from time_type import TimeType
from config import Config
from utility import convert_minutes_to_seconds, handle_error, send_email, generate_return_message


def handle_timer_file_not_found(s3_client: BaseClient, sns_client: BaseClient, current_time: TimeType) -> dict:
    """Handles the case where the timer file was not found on S3. It will create a new one with the current time plus the
    timer time and then upload it to S3
    """
    print("Timer file not found on S3. Creating a new one")
    with open(f"/tmp/{constants.Misc.TIMER_FILE}", "w") as timer_file:
        new_target_time = TimeType()
        new_target_time.set_time(current_time.current_time_seconds_float + float(convert_minutes_to_seconds(Config.THRESHOLD_TIMER_MINUTES)))
        timer_file.write(str(new_target_time.current_time_seconds_int))
    print(f"Created a new timer file with time {new_target_time.current_time_human_readable}. Uploading it")
    try:
        s3_client.upload_file(f"/tmp/{constants.Misc.TIMER_FILE}", Config.S3_BUCKET_NAME, constants.Misc.TIMER_FILE)
    except Exception as e:
        print(f"Caught exception when uploading. Exception: {e}")
        return handle_error(sns_client, f"Caught exception when uploading. Exception: {e}")

    print("Uploaded file to S3")
    message = (
        f"No timer file was found on S3. Created one with the time {new_target_time.current_time_human_readable} "
        f"and uploaded it."
    )
    send_email(
        sns_client,
        subject=f"{constants.Misc.EMAIL_SUBJECT_PREFIX}No timer file found on S3",
        message=message
    )
    return generate_return_message(constants.StatusCodes.FAILURE, message)
