import os
import sys
import pathlib
from app import constants
from app.utils import xunit_utils
from app.utils import slack_utils


def _write_github_output(response):
    """Expose the posted message ts + channel as GitHub Action outputs so a
    caller can thread follow-up uploads under the report."""
    github_output = os.getenv("GITHUB_OUTPUT")
    if not github_output or response is None:
        return

    ts = response.get("ts") if hasattr(response, "get") else None
    channel = response.get("channel") if hasattr(response, "get") else None

    with open(github_output, "a", encoding="utf-8") as file:
        if ts:
            file.write(f"ts={ts}\n")
        if channel:
            file.write(f"channel={channel}\n")


def main():
    # Check input values.
    if constants.XUNIT_PATH_ENV_VAR not in os.environ and constants.XUNIT_PATH_GLOB_ENV_VAR not in os.environ:
        raise Exception(f"xunit file(s) not found!  Please make sure to set the {constants.XUNIT_PATH_ENV_VAR} or {constants.XUNIT_PATH_GLOB_ENV_VAR} env variable!")

    if constants.SLACK_CHANNEL_ENV_VAR not in os.environ:
        raise Exception(f"Slack channel!  Please make sure to set the {constants.SLACK_CHANNEL_ENV_VAR} env variable!")

    if constants.SLACK_TOKEN_ENV_VAR not in os.environ:
        raise Exception(f"Slack channel!  Please make sure to set the {constants.SLACK_TOKEN_ENV_VAR} env variable!")

    # Load configs
    only_notify_on_issues = os.getenv(constants.ONLY_NOTIFY_ON_ISSUES_ENV_VAR, "false").lower() == 'true'
    exit_on_failure = os.getenv(constants.EXIT_ON_FAILURE_ENV_VAR, "false").lower() == 'true'

    # Load XUnit report(s)
    xunit_path = os.getenv(constants.XUNIT_PATH_ENV_VAR, "")
    xunit_glob = os.getenv(constants.XUNIT_PATH_GLOB_ENV_VAR, "")

    if xunit_glob:
        working_dir = pathlib.Path(os.getenv('GITHUB_WORKSPACE'))
        files = working_dir.glob(xunit_glob)
    elif xunit_path:
        files = [pathlib.Path(xunit_path)]

    # Report on files
    failed_tests = False

    for file in files:
        xunit_report = xunit_utils.read_xunit(file)
        file_contains_failures = bool(xunit_report.errors or xunit_report.failures)

        # Slack results
        slack_attachment = {
            "color": constants.PASS_COLOR,
            "author_name": "XUnit Slack Reporter",
            "author_link": f"https://github.com/{os.getenv('GITHUB_REPOSITORY')}/actions/runs/{os.getenv('GITHUB_RUN_ID')}",
            "title": f"XUnit test results for {os.getenv('GITHUB_WORKFLOW')} on {os.getenv('GITHUB_REF')}",
            "fields": []
        }

        if file_contains_failures:
            slack_attachment['color'] = constants.FAIL_COLOR

        slack_attachment['fields'].append({
            "title": "Total # of tests",
            "value": f"{xunit_report.tests}",
            "short": True
        })

        slack_attachment['fields'].append({
            "title": "Tests passed",
            "value": f"{xunit_report.tests - xunit_report.errors - xunit_report.failures}",
            "short": True
        })

        slack_attachment['fields'].append({
            "title": "Tests errored",
            "value": f"{xunit_report.errors}",
            "short": True
        })

        slack_attachment['fields'].append({
            "title": "Tests failed",
            "value": f"{xunit_report.failures}",
            "short": True
        })

        slack_attachment['fields'].append({
            "title": "Time elapsed",
            "value": f"{xunit_report.time} seconds",
            "short": True
        })

        slack_attachment['fields'].append({
            "title": "File",
            "value": str(file)
        })

        # If success, only send if configured.
        if not file_contains_failures:
            if not only_notify_on_issues:
                response = slack_utils.send_slack_msg(
                    os.getenv(constants.SLACK_CHANNEL_ENV_VAR),
                    attachments=[slack_attachment]
                )
                _write_github_output(response)
        # If error or failure.
        else:
            response = slack_utils.send_slack_msg(
                    os.getenv(constants.SLACK_CHANNEL_ENV_VAR),
                    attachments=[slack_attachment]
            )
            _write_github_output(response)
            failed_tests = True

    # Return appropriate status code.
    if exit_on_failure:
        if failed_tests:
            sys.exit(1)

if __name__ == "__main__":
    main()
