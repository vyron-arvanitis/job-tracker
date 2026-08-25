# Job Tracker

A local, read-only Gmail application that turns recruiting email into one SQLite row per company and position.

## Setup

Use Python 3.12+, create a virtual environment, and install the project:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
```

In Google Cloud, create a project, enable the Gmail API, configure the OAuth consent screen, and create an OAuth client of type **Desktop app**. Download its JSON as `credentials.json` in the project directory. The app requests only `gmail.readonly`, never asks for a Gmail password, and never modifies messages. The local `token.json` is created after the browser-based consent flow.

Copy `.env.example` to `.env` and adjust `DATABASE_URL`, `NO_RESPONSE_DAYS`, or `GMAIL_MAX_RESULTS` if needed.

## Commands

Run commands from the project root with the virtual environment activated.

```bash
# Open the browser-based Google OAuth flow. Creates token.json, or the path
# configured by TOKEN_FILE, after consent.
python -m job_tracker auth

# Search Gmail, fetch candidate messages, classify them, and update SQLite.
# The sync displays progress while searching and fetching messages.
python -m job_tracker sync

# Re-run the current classifier against email bodies already stored in SQLite.
# This does not contact or modify Gmail.
python -m job_tracker reclassify

# Print one row per company and position.
python -m job_tracker list

# Print only applications with a specific status.
python -m job_tracker list --status rejected

# List follow-up candidates, including the recruiter contact email when known.
python -m job_tracker list --status no_response

# Show cumulative applications and counts grouped by current status.
python -m job_tracker stats

# Export the current application tracker as CSV.
python -m job_tracker export applications.csv

# Generate a visual PNG donut chart of the application pipeline.
python -m job_tracker chart

# Choose a different chart output path.
python -m job_tracker chart --output reports/application_status.png
```

`auth` is normally needed only once. It uses the read-only Gmail scope and never sends, edits, archives, or deletes email.

`sync` searches likely recruiting terms in Gmail, including Sent mail, fetches only matching messages, stores Gmail message IDs for idempotency, and associates messages using thread ID and normalized company/position. The first sync checks Gmail history; later syncs use the newest stored email timestamp and search only newer mail with a one-day overlap. Existing Gmail IDs are skipped, so the overlap is safe. Existing applications are updated when new messages arrive. The tracker also stores the latest recruiter-side contact email when available. Rule classification supports common English and German terms. `no_response` is derived after `NO_RESPONSE_DAYS` only when no later process event exists.

`reclassify` applies the current local rules to every email body already stored in SQLite and recomputes application statuses. It does not access Gmail. Messages identified as newsletters, university/course notices, account/security mail, or other non-job mail are detached from applications; applications with no genuine job emails left are removed. The raw email rows remain local so the rules can be improved and rerun later.

Supported statuses include `applied`, `no_response`, `hr_interview`, `technical_interview`, `assessment`, `final_interview`, `rejected`, `offer`, `withdrawn`, and `unknown`. Generic words such as `Stellenangebot` or `Jobangebote` are not treated as an employment offer.

The `chart` command creates a local `applications_status.png` donut chart with the cumulative applied count, ongoing applications, closed applications, and a current-status breakdown. `No response` and later stages are included in the cumulative applied count; the status breakdown remains mutually exclusive. It does not send any data externally.

To use a different database, token location, or no-response threshold, edit `.env`:

```env
DATABASE_URL=sqlite:///job_tracker.db
CREDENTIALS_FILE=secrets/credentials.json
TOKEN_FILE=secrets/token.json
NO_RESPONSE_DAYS=14
GMAIL_MAX_RESULTS=500
```

## Optional OpenAI classification

Install `pip install -e '.[openai]'`, set `OPENAI_API_KEY`, and use `OpenAIClassifier` for low-confidence/ambiguous messages. The implementation sends the sender, subject, and a truncated body (up to 6,000 characters) to OpenAI and requests structured JSON. This is disabled by default; email contents remain local when using the rule classifier. Review your organization’s privacy and retention requirements before enabling it.

## Privacy

Credentials, OAuth tokens, environment files, and SQLite databases are ignored by Git. Bodies are stored locally to support reclassification, but are never logged by default. Gmail access is read-only. Treat the database as sensitive personal data and protect the machine and backups where it is stored.

## Development

```bash
pytest
```
