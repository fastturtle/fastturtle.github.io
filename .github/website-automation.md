# Website reminders and mention monitoring

Two GitHub Actions workflows help keep the website current:

- **Quarterly website review** opens an issue at 09:17 Europe/London time on
  January, April, July, and October 1. It can also be run manually.
- **Google Alerts monitor** checks an RSS feed daily at 08:23 Europe/London
  time and opens an issue for each unseen result.

## Configure Google Alerts

1. Open [Google Alerts](https://www.google.com/alerts).
2. Create an alert for `"Gabriel Barth-Maron"`.
3. Under **Show options**, set **Deliver to** to **RSS feed**.
4. Copy the RSS link shown next to the saved alert.
5. In this repository, open **Settings → Secrets and variables → Actions**.
6. Create a repository secret named `GOOGLE_ALERTS_RSS_URL` containing the
   copied RSS URL.
7. Open **Actions → Google Alerts monitor**, select **Run workflow**, and
   confirm that the run succeeds.

The RSS URL is kept in a secret because it contains identifiers associated
with the Google Alert. If the secret is absent, the daily workflow exits
successfully without making changes.

The monitor creates at most ten issues per run and embeds a stable identifier
in each issue so the same feed result is not reported twice.
