# TF2 Player Joined Notifier AWS
An application for AWS Lambda that will send email notifications when players join a server for the online video game `Team-Fortress 2`. There are different modes that the application can run in. See the sections below for explanation of the modes. The user will provide certain values that are common to both modes, like the target server IP. These values are provided via the Lambda's environment variables. After everything is setup, it will send notifications automatically.

## Example Notification (email)
```
Subject: [URGENT]Player count has reached the threshold
From: TF2 Player Joined Notifier

The player count has reached the threshold: 6

Server name: "<Your Server Name>"
IP: "<Your Server IP>"
Player count: 6

The next check will happen after Fri Apr, 4 05:42:05 2025 (UTC)


--
If you wish to stop receiving notifications from this topic, please click or visit the link below to unsubscribe:
<Unsubscribe link>

Please do not reply directly to this email. If you have any questions or comments regarding this email, please contact us at <Support link>
```

## Usage
This application can be set up by either:
1. Using the included AWS SAM Template file and deploying to your own AWS account that way. If you are not familiar with using a template file, I recommend looking at [this tutorial](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-getting-started-hello-world.html) by AWS. You essentially only need to do `Step 2: Build your application` and `Step 3: Deploy your application to the AWS Cloud` with this project. Before deploying, read this README and fill in the places that are marked `FILL IN` in the `template.yaml` file at the root of this repo.
2. Reading the `Technical Explanation` section below and set up the required resources on AWS manually.

## Modes
### ALL Mode
This mode will send email notifications for every player that joins the server. It is set to check repeatedly on a timer and will query the server for the player list in order to determine whether to send a notification. It temporarily stores player names that it has already sent notifications for, in a database, so repeat notifications do not get sent. 
### Threshold Mode
This mode will send email notifications when the player count reaches a certain user-provided threshold. For example, if the threshold is set to 16, then it'll send a notification when it detects that the player count is 16 or higher.  It is set to check repeatedly on a timer and will query the server for the player list in order to determine whether to send a notification. The user also provides a `timer` value, which is a time duration for the program to wait, after sending a notification. This is to prevent users from getting unnecessarily notified repeatedly. For example, if the timer was set to 1 hour, then after the threshold is reached and a notification is sent, it will wait 1 hour before sending another notification when the player count reaches the threshold.

## Technical Explanation
The AWS components below are required to run the program:
* Lambda
* EventBridge
* S3
* Simple Notification Service
* DynamoDB
* CloudWatch
* IAM Roles with sufficient permissions.

The main code runs on `Lambda` which is triggered by a timer on `EventBridge`. `DynamoDB` is used to store player names so duplicate notifications are not sent. `S3` is used to store the timer value. `Simple Notification Service` sends the actual notification. `CloudWatch` is for logs.
