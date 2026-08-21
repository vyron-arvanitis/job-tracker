from job_tracker.classifier.base import EmailInput
from job_tracker.classifier.rules import RuleBasedClassifier

def classify(text):
    return RuleBasedClassifier().classify(EmailInput("recruiter@unit8.com", "", text))

def test_application_received(): assert classify("Thank you for applying for the Software Engineer position.").event_type == "application_received"
def test_technical_interview(): assert classify("We were impressed with your profile and would like to invite you to a technical interview.").event_type == "technical_interview"
def test_german_rejection(): assert classify("Leider können wir Ihre Bewerbung im weiteren Auswahlverfahren nicht berücksichtigen.").event_type == "rejection"

