"""
Sends the digest as an email via Gmail SMTP.
Needs env vars: GMAIL_ADDRESS, GMAIL_APP_PASSWORD, DIGEST_TO_ADDRESS
(App password, not your real password — generate one at
 https://myaccount.google.com/apppasswords, takes 30 seconds)
"""
import os
import smtplib
from datetime import date
from email.mime.text import MIMEText


def _format_html(opportunities: list[dict]) -> str:
    if not opportunities:
        return "<p>No new or trending opportunities cleared the score bar today. Quiet day.</p>"

    rows = ""
    for opp in opportunities:
        rows += f"""
        <div style="margin-bottom:20px;padding:14px;border-left:4px solid #4a4a4a;background:#f7f7f7;">
          <div style="font-size:16px;font-weight:bold;">{opp['theme_key'].replace('-', ' ').title()}
            <span style="font-weight:normal;color:#888;font-size:13px;"> — {opp.get('status','')}</span>
          </div>
          <div style="margin:6px 0;">{opp['description']}</div>
          <div style="font-size:13px;color:#555;">
            Score: <b>{opp['overall_score']}/10</b>
            &nbsp;(pay signal {opp['payment_signal']}, frequency {opp['frequency_signal']}, open gap {opp['competition_gap']})
          </div>
          <div style="font-size:13px;color:#555;margin-top:4px;">"{opp.get('evidence_quote','')}"</div>
          <div style="font-size:12px;margin-top:6px;"><a href="{opp['source_url']}">source</a></div>
        </div>
        """

    return f"""
    <h2>SaaS Opportunity Radar — {date.today().isoformat()}</h2>
    <p>{len(opportunities)} opportunity(ies) worth a look today, ranked by score:</p>
    {rows}
    """


def send_digest(opportunities: list[dict]) -> None:
    html_body = _format_html(opportunities)
    msg = MIMEText(html_body, "html")
    msg["Subject"] = f"SaaS Radar: {len(opportunities)} opportunities — {date.today().isoformat()}"
    msg["From"] = os.environ["GMAIL_ADDRESS"]
    msg["To"] = os.environ.get("DIGEST_TO_ADDRESS", os.environ["GMAIL_ADDRESS"])

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(os.environ["GMAIL_ADDRESS"], os.environ["GMAIL_APP_PASSWORD"])
        server.send_message(msg)

    print(f"[notifier] sent digest with {len(opportunities)} opportunities")
