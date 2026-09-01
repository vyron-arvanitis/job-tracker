from job_tracker.classifier.base import EmailInput
from job_tracker.classifier.rules import RuleBasedClassifier


def classify(text, sender="recruiter@unit8.com", subject=""):
    return RuleBasedClassifier().classify(EmailInput(sender, subject, text))

def test_application_received(): assert classify("Thank you for applying for the Software Engineer position.").event_type == "application_received"
def test_technical_interview(): assert classify("We were impressed with your profile and would like to invite you to a technical interview.").event_type == "technical_interview"
def test_german_rejection(): assert classify("Leider können wir Ihre Bewerbung im weiteren Auswahlverfahren nicht berücksichtigen.").event_type == "rejection"
def test_german_rejection_when_continuing_with_other_candidates():
    result = classify(
        "Wir haben deine Unterlagen mit grossem Interesse studiert. Nach "
        "sorgfältiger Überlegung haben wir uns entschieden, für diese Position "
        "mit anderen Kandidatinnen und Kandidaten weiterzufahren, deren "
        "Erfahrungen und Kompetenzen unserem Wunschprofil noch näher kommen.",
        sender="Kerstin Wessel <recruiting@css.ch>",
        subject="Deine Bewerbung bei der CSS",
    )
    assert result.event_type == "rejection"


def test_german_rejection_with_other_applicants_variant():
    assert classify("Wir fahren mit anderen Bewerberinnen und Bewerbern weiter.").event_type == "rejection"


def test_position_is_extracted_from_application_subject():
    result = classify(
        "The application was unsuccessful.",
        subject="Update on your application for Shopware Backend Entwickler*in (m/w/d)",
    )
    assert result.position == "Shopware Backend Entwickler*in (m/w/d)"


def test_french_rejection(): assert classify("D'autres candidats plus proches du profil recherché par notre client ont été retenus.", sender="Olivier <noreply@academicwork.com>", subject="Merci pour votre candidature!").event_type == "rejection"
def test_german_phone_interview_is_hr_interview(): assert classify("Um uns besser kennenzulernen, möchte ich gerne ein kurzes Telefoninterview mit dir führen. Mein Terminvorschlag wäre Mittwoch.").event_type == "hr_interview"


def test_role_before_role_at_company_is_extracted_without_company_suffix():
    associate = classify(
        "Dear Vyron, Thank you for your interest in the Associate role at McKinsey."
    )
    junior = classify(
        "Dear Vyron, Thank you for your interest in the Junior Associate role at McKinsey."
    )
    assert associate.position == "Associate"
    assert junior.position == "Junior Associate"


def test_rejection_with_another_candidate_is_detected():
    assert (
        classify(
            "We decided to move forward with another candidate who closely "
            "matches our current needs."
        ).event_type
        == "rejection"
    )


def test_newsletter_with_interview_language_is_unknown():
    result = classify(
        "Our guide explains how to prepare for interviews.",
        sender="LeetCode <no-reply@leetcode.com>",
        subject="LeetCode Weekly Digest",
    )
    assert (result.is_job_related, result.event_type) == (False, "unknown")


def test_quoted_rejection_does_not_override_a_short_new_reply():
    result = classify(
        "14:30 works for me.\n\nOn Tuesday, June 2, 2026, Alex wrote:\n"
        "Unfortunately, we will not be moving forward with your application."
    )
    assert result.event_type == "recruiter_contact"


def test_first_interview_with_short_coding_task_is_hr_interview():
    result = classify(
        "We would like to invite you to a first online interview. "
        "The last five minutes include a short coding assignment."
    )
    assert result.event_type == "hr_interview"


def test_application_confirmation_is_detected_from_success_message():
    result = classify(
        "You've successfully applied. The company is reviewing your application."
    )
    assert result.event_type == "application_received"


def test_recruiter_registration_without_a_matching_role_is_unknown():
    result = classify(
        "Thank you for signing up. We currently don't have a job or project "
        "that matches your search criteria.",
        sender="Rockstar Recruiting <applications@rockstar.jobs>",
        subject="Your Application from 25.05.2026",
    )
    assert (result.is_job_related, result.event_type) == (False, "unknown")


def test_account_email_verification_is_not_an_application_event():
    result = classify(
        "Please close your application and registration for your candidate "
        "account by verifying your email address.",
        sender="Tabea Ade <t.ade@ratbacher.com>",
        subject="Ihre Bewerbung bei der Ratbacher GmbH",
    )
    assert (result.is_job_related, result.event_type) == (False, "unknown")


def test_missing_documents_are_recruiter_follow_up():
    result = classify(
        "Herzlichen Dank für Deine Bewerbung. Deine Unterlagen sind noch nicht "
        "vollständig. Bitte ergänze Dein Bachelorzeugnis.",
        sender="KPMG <recruiting@kpmg.com>",
        subject="KPMG | Deine Bewerbung",
    )
    assert result.event_type == "recruiter_contact"


def test_multi_application_agency_update_is_not_a_rejection():
    result = classify(
        "Bezüglich deiner Bewerbungen habe ich schon zwei Rückmeldungen "
        "erhalten. Bei Comerge und Stampfli leider eine Absage. Andere "
        "Bewerbungen sind noch in Bearbeitung.",
        sender="Alexander Föll <a.foell@bruederlinpartner.ch>",
        subject="AW: Terminvorschlag",
    )
    assert result.event_type == "recruiter_contact"


def test_known_recruiter_domain_keeps_terse_reply_in_pipeline():
    result = classify("14:30 works for me.", sender="Recruiter <reply@unit8.com>")
    assert result.event_type == "recruiter_contact"
