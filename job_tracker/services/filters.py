def is_excluded_message(message, excluded_terms: tuple[str, ...]) -> bool:
    haystack = " ".join((message.sender, message.recipients or "", message.subject, message.body_text)).casefold()
    return any(term.casefold() in haystack for term in excluded_terms)

