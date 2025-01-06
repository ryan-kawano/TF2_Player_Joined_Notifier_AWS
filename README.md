# TF2 Player Joined Notifier AWS
An application for AWS Lambda that will send email notifications when players join a server. There are different modes that the application can run in. See the sections below for explanation of the modes. The user will provide certain values that are common to both modes, like the target server IP. These values are provided via the Lambda's environment variables. After everything is setup, it will send notifications automatically.

## Modes
### ALL Mode
This mode will send email notifications for every player that joins the server. It is set to check repeatedly on a timer and will query the server for the player list in order to determine whether to send a notification. It temporarily stores player names that it has already sent notifications for, in a database, so repeat notifications do not get sent. 
### Threshold Mode
This mode will send email notifications when the player count reaches a certain user-provided threshold. For example, if the threshold is set to 16, then it'll send a notification when it detects that the player count is 16 or higher.  It is set to check repeatedly on a timer and will query the server for the player list in order to determine whether to send a notification. The user also provides a `timer` value, which is a time duration for the program to wait, after sending a notification. This is to prevent users from getting unnecessarily notified, repeatedly. For example, if the timer was set to 1 hour, then after the threshold is reached and a notification is sent, it will wait 1 hour before sending another notification when the player count reaches the threshold.

## Usage
TO-DO