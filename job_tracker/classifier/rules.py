from __future__ import annotations

import html
import re

from .base import ClassificationResult, EmailClassifier, EmailInput


def rx(*patterns: str) -> re.Pattern[str]:
    """Compile one case-insensitive expression from several alternatives."""
    return re.compile("|".join(f"(?:{pattern})" for pattern in patterns), re.I | re.S)


def sender_domain(sender: str) -> str:
    match = re.search(r"@([\w.-]+)", sender or "")
    return match.group(1).lower() if match else ""


def newest_message(body: str | None) -> str:
    """Return only the newest reply, excluding quoted conversation history.

    Older messages frequently contain a rejection or interview invitation. A
    classifier that sees the whole thread will eventually assign the wrong
    event to a short, otherwise harmless reply.
    """
    text = html.unescape(body or "").replace("\r\n", "\n").replace("\r", "\n")
    cuts: list[int] = []
    quote_patterns = (
        r"\nOn .{0,240}? wrote:\s*\n",
        r"\nAm .{0,240}? schrieb .{0,160}?:\s*\n",
        r"\n-{2,}\s*Original Message\s*-{2,}",
        r"\nFrom:\s*[^\n]+\nSent:\s*[^\n]+",
        r"\nVon:\s*[^\n]+\nGesendet:\s*[^\n]+",
    )
    for pattern in quote_patterns:
        match = re.search(pattern, text, re.I | re.S)
        if match:
            cuts.append(match.start())
    if cuts:
        text = text[: min(cuts)]

    text = "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith(">")
    )
    return re.sub(r"\s+", " ", text).strip()


# These are deliberately conservative. They catch the recurring newsletters,
# university notices, account messages, and career content present in the local
# mailbox without treating every message containing the word "application" as a
# job event.
NOISE_DOMAINS = {
    "leetcode.com",
    "hello.interviewquery.com",
    "news.aegeanair.com",
    "try.anaconda.com",
    "email.openai.com",
    "lists.physik.uni-muenchen.de",
    "tutoren.deutsch-uni.com",
}

NOISE_SENDER = rx(
    r"community@lrz\.uni-muenchen\.de",
    r"careerservice@verwaltung\.uni-muenchen\.de",
    r"infodienst\.lmu@verwaltung\.uni-muenchen\.de",
    r"noreply@github\.com",
)

NOISE_SUBJECT = rx(
    r"weekly digest",
    r"interview prep",
    r"acing any interview",
    r"survive the interview process",
    r"job recommendations",
    r"entry-level careers edition",
    r"think sales is just selling",
    r"could this be your story",
    r"ai challenge could land on your cv",
    r"password reset",
    r"verify your candidate account",
    r"login code",
    r"otp code",
    r"oauth application",
    r"miles\+bonus",
    r"career talk",
    r"career forum",
    r"career event",
    r"application workshop",
    r"jobsearch",
    r"german business language course",
    r"deutsch für den berufseinstieg",
    r"\bduo\b",
    r"wecare@lmu",
    r"\[infodienst\]",
    r"kältemaschine",
    r"cooling water",
    r"brütende ente",
    r"nesting duck",
    r"letter of admission",
    r"admission lmu",
    r"ticket#",
    r"isic application",
    r"t&cs",
    r"terms",
    r"how to decide if a job offer",
    r"friendly reminder: (?:your experience|how did we do)",
    r"were you hired by",
    r"keep your ey careers account active",
    r"bewerberkonto",
    r"meet & greet",
    r"innovation incubator",
    r"openclaw workshop",
    r"don.t forget about your application",
    r"coachanfrage",
    r"gehaltsgespräch\?",
    r"studentische hilfskräfte gesucht",
    r"^\[studenten\]",
    r"security vulnerability",
    r"data privacy notice",
    r"your experience at roland berger",
    r"how did we do at roland berger",
    r"looking for student assistants",
)

GENERIC_NON_EVENT = rx(
    r"your new job recommendations",
    r"latest roles by category",
    r"recommended jobs",
    r"recommended roles",
    r"see the latest roles",
    r"invitation to apply",
    r"reminder to apply",
    r"sign in",
    r"security code",
    r"verification code",
    r"bestätige kurz deine e-mail adresse",
    r"setzen sie ihre bewerbung fort",
    r"candidate account verification",
    r"thank you for creating an account",
    r"(?:application|registration|registrierung|bewerberaccount).{0,160}(?:verification|verify|verifizierung|verifizieren).{0,80}(?:email|e-mail)",
    # A recruiter-community registration is not an application, even when its
    # subject says "Your Application".
    r"(?:currently|at the moment)\s+(?:do not|don't) have a (?:job or )?project",
    r"no (?:current|suitable|matching) (?:job|role|position|project)",
    r"right opportunities for you",
)

REJECTION = rx(
    r"regret to inform",
    r"decided not to (?:proceed|move forward|continue)",
    r"decided to move forward with other candidates",
    r"decided to move forward with candidates whose profiles",
    r"(?:we.re|we are) moving forward with other candidates",
    r"move forward with another candidate",
    r"unable to move forward with your application",
    r"not able to advance (?:you|your application)",
    r"not able to take your application further",
    r"move forward with other candidates",
    r"not selected (?:at this time|for|to)",
    r"not pre-selected",
    r"cannot be considered",
    r"cannot offer you a position",
    r"unable to find a match",
    r"don['’]t have a match",
    r"not been admitted",
    r"(?:haven.t|have not) been admitted",
    r"application (?:was )?unsuccessful",
    r"will not be progressing",
    r"won['’]t be moving forward",
    r"we will not be proceeding with your application",
    r"müssen wir ihnen leider mitteilen",
    r"leider.{0,180}(?:nicht weiter berücksichtigen|nicht berücksichtigen|keine positive|keine möglichkeit|anderen kandidaten|anderen bewerber)",
    r"nicht weiter berücksichtigen",
    r"nicht in die engere auswahl",
    r"nicht in die engere wahl (?:aufnehmen|nehmen)",
    r"im weiteren bewerbungsprozess.{0,100}nicht.{0,40}berücksichtigen",
    r"bewerbung war leider nicht erfolgreich",
    r"closed the application process.{0,200}(?:didn.t|did not) work out",
    r"we.re closing it",
    r"nicht für (?:den|die) nächsten schritt",
    r"nicht weiterverfolgen",
)

OFFER = rx(
    r"pleased to offer you",
    r"we would like to offer you",
    r"offer letter.{0,120}(?:attached|enclosed|sign)",
    r"employment offer.{0,120}(?:attached|accept|sign)",
    r"vertragsangebot",
    r"arbeitsvertrag.{0,120}(?:anbei|beigefügt|unterschrift)",
)

FINAL = rx(
    r"final interview",
    r"final round",
    r"final stage interview",
    r"abschlussgespräch",
    r"finalrunde",
    r"letzte runde.{0,80}(?:gespräch|interview)",
)

TECHNICAL = rx(
    r"technical interview",
    r"coding interview",
    r"technical round",
    r"technical discussion",
    r"pair programming",
    r"fachliches interview",
    r"technisches interview",
    r"technical screen",
)

# A first/initial interview remains an HR-stage event even when the invitation
# mentions a very short coding task as part of the conversation.
FIRST_INTERVIEW = rx(
    r"(?:invite|invitation|would like to invite).{0,100}(?:first|initial)\s+(?:online\s+|video\s+|virtual\s+)?interview",
    r"(?:einladung|einladen).{0,100}erst(?:es|e|en)\s+(?:online\s+|video\s+|virtuell\s+)?(?:interview|gespräch)",
)

ASSESSMENT = rx(
    r"invitation to complete.{0,100}(?:assessment|test)",
    r"online assessment",
    r"technical assessment",
    r"coding assignment",
    r"take[- ]home",
    r"coding challenge",
    r"hacker ?rank",
    r"codility",
    r"testaufgabe",
    r"case study",
    r"working[- ]?session",
    r"assessment cent(?:er|re)",
    r"invitation to take on a few tasks",
    r"complete a few tasks",
    r"writing sample.{0,180}(?:send|submit|request)",
    r"request.{0,120}writing sample",
)

HR_INTERVIEW = rx(
    r"invitation.{0,100}(?:interview|call)",
    r"invite.{0,100}(?:interview|call)",
    r"einladung.{0,100}(?:interview|gespräch|telefonat)",
    r"teams[- ]?interview",
    r"job interview",
    r"phone screen",
    r"phone interview",
    r"telefoninterview",
    r"telefonisches interview",
    r"screening call",
    r"erstgespräch",
    r"hr[- ]?interview",
    r"vorstellungsgespräch.{0,80}einladen",
    r"gesprächstermin.{0,80}bestätigt",
    r"interview for .{0,120} job",
    r"confirmed:.{0,80}meeting",
    r"your \d+ minute meeting.{0,120}scheduled",
)

APPLICATION_RECEIVED = rx(
    r"application (?:has been )?received",
    r"we received your (?:job )?application",
    r"successfully received your application",
    r"application (?:was )?submitted successfully",
    r"thanks? for (?:your )?(?:job )?application",
    r"thank you for (?:your )?(?:job )?application",
    r"thank you (?:very much )?for (?:your )?(?:job )?application",
    r"thank you for taking the time to apply",
    r"currently reviewing your profile",
    r"bewerbung ist bei uns angekommen",
    r"herzlichen dank für (?:deine|ihre) bewerbung",
    r"thank you for applying",
    r"thank you (?:very much )?.{0,80}for applying",
    r"thanks for applying",
    r"confirming your .*application",
    r"eingangsbestätigung.{0,100}bewerbung",
    r"eingang ihrer .*bewerbung",
    r"hiermit bestätigen wir den eingang ihrer bewerbung",
    r"bewerbung.{0,120}(?:eingegangen|erhalten)",
    r"vielen dank für (?:deine|ihre) bewerbung.{0,220}(?:prüf|bearbeit|geduld|rückmeldung)",
    r"application received",
    r"we['’]ve got it!.{0,100}application",
    r"application.{0,80}has been sent",
    r"successfully submitted your .*application",
    r"you.ve successfully applied",
    r"bewerbung wurde weitergeleitet",
    r"thanks for submitting your documents",
    r"we are reviewing your application",
    r"we will give careful consideration to your application",
    r"bewerbung sorgfältig prüfen",
    r"we will review your application",
    r"application.{0,100}received",
    r"application.{0,140}(?:reviewing|reviewed|under review)",
    r"application.{0,140}(?:in process|being processed|pending)",
    r"acknowledgement of application",
    r"application will now be reviewed",
)

MISSING_DOCUMENTS = rx(
    r"(?:missing|outstanding|required|additional).{0,100}(?:document|documents|unterlagen|zeugnis)",
    r"(?:document|documents|unterlagen|zeugnis).{0,100}(?:missing|fehlen|nachreichen)",
    r"(?:please|bitte).{0,100}(?:send|provide|submit|senden|einreichen).{0,100}(?:missing|required|additional).{0,80}(?:document|documents|unterlagen)",
    r"unterlagen sind noch nicht vollständig",
    r"nachgeforderten unterlagen",
    r"fehlende unterlagen",
)

MULTI_APPLICATION_UPDATE = rx(
    r"\b(?:two|multiple|several)\s+(?:job\s+)?applications?\b",
    r"\b(?:zwei|mehrere)\s+(?:bewerbungen|rückmeldungen)\b",
    r"\b(?:two|zwei)\s+(?:pieces of )?(?:feedback|rückmeldungen)\b",
    r"(?:applications?|bewerbungen).{0,120}(?:in progress|in bearbeitung|awaiting|warte(?:n|t) auf)",
    r"(?:rejections?|absagen).{0,120}(?:other|weitere|multiple|mehrere|applications?|bewerbungen)",
)

JOB_RELATED = rx(
    r"\bapplication\b",
    r"\bapplying\b",
    r"\bapplied\b",
    r"\bcandidate\b",
    r"\brecruit",
    r"\binterview\b",
    r"\bposition\b",
    r"\brole\b",
    r"\bjob\b",
    r"\bbewerbung\b",
    r"\bbewerber",
    r"\bstelle\b",
    r"\bhiring\b",
    r"\btrainee\b",
    r"arbeitszeugnis",
    r"bewerbungsprozess",
)

# Terse replies from these domains are still part of a recruiting thread. All
# noise checks run first, so interview newsletters from an otherwise relevant
# company remain ignored.
RECRUITING_DOMAINS = {
    "unit8.com",
    "unit8.co",
    "kpmg.com",
    "reply.de",
    "reply.com",
    "vogel-beratung.com",
    "bruederlinpartner.ch",
    "siemens.com",
    "siemens-healthineers.com",
    "janestreet.com",
    "deshaw.com",
    "wsl.ch",
    "mvz-labor-berlin.de",
    "ratbacher.com",
    "aconium.eu",
    "senacor.com",
    "d-fine.com",
    "jobs.d-fine.com",
    "ferchau.com",
}

SELF_EMAIL = "vyronas.arvanitis@gmail.com"


def extract_company(sender: str, text: str) -> str | None:
    match = re.search(r"@([\w.-]+)", sender or "")
    if match:
        domain = match.group(1).split(".")[0]
        if domain not in {"gmail", "outlook", "yahoo", "hotmail"}:
            return domain.replace("-", " ").title()
    match = re.search(
        r"(?:at|bei|from|von)\s+([A-Z][\w&.-]+(?:\s+[A-Z][\w&.-]+)?)", text
    )
    return match.group(1).strip() if match else None


def extract_position(text: str) -> str | None:
    patterns = (
        r"(?:interest in|applied for|application for|apply for|for)\s+(?:the|a|an)\s+([^\n.!?]{2,100}?)\s+(?:role|position|job)\b",
        r"(?:the|a|an)\s+([^\n.!?]{2,100}?)\s+(?:role|position|job)\b",
        r"(?:role|position|job)\s+(?:of|as)\s+([^\n.!?]{2,100})",
        r"(?:position|role|job|stelle)[:\s]+([^\n.!?]{3,100})",
        r"for the\s+([^\n.!?]{3,100})\s+position",
        r"für die Stelle als\s+([^\n.!?]{3,100})",
    )
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            position = match.group(1).strip(" -–—")
            if position.lower() not in {
                "your application",
                "an update on your application",
                "your candidacy",
            }:
                return position
    return None


def _event_type(sender: str, subject: str, body: str) -> str:
    """Apply the supplied reclassification rules to one newest message."""
    text = f"{subject}\n{body}"[:20000]
    domain = sender_domain(sender)

    if SELF_EMAIL in sender.lower():
        return "unknown"
    if (
        domain in NOISE_DOMAINS
        or "starred.com" in domain
        or NOISE_SENDER.search(sender)
        or NOISE_SUBJECT.search(subject)
    ):
        return "unknown"
    if GENERIC_NON_EVENT.search(text):
        return "unknown"

    # Agency summaries can mention an interview or a rejection belonging to a
    # different client application. Keep the message as recruiter follow-up
    # rather than attributing that event to the tracked row.
    if domain == "bruederlinpartner.ch" and MULTI_APPLICATION_UPDATE.search(text):
        return "recruiter_contact"

    # Explicit stage rules have priority over generic application language.
    if OFFER.search(text):
        return "offer"
    if REJECTION.search(text):
        # Agency summaries describe several client applications at once. They
        # should not close one particular tracked application.
        if MULTI_APPLICATION_UPDATE.search(text):
            return "recruiter_contact"
        return "rejection"
    if FINAL.search(text):
        return "final_interview"
    if TECHNICAL.search(text):
        return "technical_interview"
    if FIRST_INTERVIEW.search(text):
        return "hr_interview"
    if ASSESSMENT.search(text):
        return "assessment"

    if HR_INTERVIEW.search(text):
        return "hr_interview"
    if re.search(r"\bgespräch\b", subject, re.I) and re.search(
        r"(teams meeting|microsoft teams|google meet|termin|meeting)", text, re.I
    ):
        return "hr_interview"

    # A request for missing documents is follow-up, not proof that a new
    # application was just submitted. It can still contain an automated
    # "thank you for your application" acknowledgement.
    if MISSING_DOCUMENTS.search(text):
        return "recruiter_contact"
    if APPLICATION_RECEIVED.search(text):
        return "application_received"

    if JOB_RELATED.search(text) or domain in RECRUITING_DOMAINS:
        return "recruiter_contact"
    return "unknown"


class RuleBasedClassifier(EmailClassifier):
    """Classify recruiting events with local, deterministic rules."""

    def classify(self, email: EmailInput) -> ClassificationResult:
        body = newest_message(email.body_text)
        event = _event_type(email.sender, email.subject, body)
        if event == "unknown":
            return ClassificationResult(False, None, None, event, 0.97)

        text = f"{email.subject}\n{body}".strip()
        confidence = {
            "offer": 0.99,
            "rejection": 0.99,
            "final_interview": 0.97,
            "technical_interview": 0.98,
            "assessment": 0.96,
            "hr_interview": 0.95,
            "application_received": 0.97,
            "recruiter_contact": 0.78,
        }[event]
        actions = {
            "application_received": "Wait for a response",
            "hr_interview": "Prepare for HR interview",
            "technical_interview": "Prepare for technical interview",
            "assessment": "Complete the assessment",
            "final_interview": "Prepare for final interview",
            "offer": "Review offer",
            "recruiter_contact": "Reply to recruiter",
        }
        return ClassificationResult(
            True,
            extract_company(email.sender, text),
            extract_position(text),
            event,
            confidence,
            actions.get(event),
        )
