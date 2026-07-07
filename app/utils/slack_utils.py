import os
from slack import WebClient
from app import constants


def send_slack_msg(slack_channel: str,
                   message: str = '',
                   attachments: list = None):
    """
    General purpose function to send one-off Slack messages.

    :param slack_channel: Slack channel for message
    :param message: Message to send to Slack
    :param attachments: Attachments (if desired)
    :return: the Slack API response (includes ``ts`` and ``channel``)
    """
    client = WebClient(os.getenv(constants.SLACK_TOKEN_ENV_VAR, ""))

    # Return the response so callers can read the posted message's ts / channel
    # (e.g. to thread follow-up uploads under the report).
    return client.chat_postMessage(
        channel=slack_channel,
        text=message,
        attachments=attachments,
        as_user=True
    )
