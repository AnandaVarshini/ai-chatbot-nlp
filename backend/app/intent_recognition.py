import re
from fuzzywuzzy import fuzz


class IntentRecognizer:
    def __init__(self):
        self.intent_patterns = {
            "Greeting": [
                r"^\s*(?:hi|hello|hey)[!.]?\s*$",
                r"^\s*good morning\b",
                r"^\s*good afternoon\b",
                r"^\s*good evening\b",
            ],

            "Help": [
                r"^\s*help[!.]?\s*$",
                r"^\s*what can you do\??\s*$",
                r"^\s*what are your capabilities\??\s*$",
                r"^\s*capabilities\??\s*$",
                r"^\s*how to use\b",
                r"^\s*what are your features\??\s*$",
            ],

            "Image": [
                r"\bshow\s+(?:me\s+)?images?\s+(?:of|for)\b",
                r"\bpictures?\s+of\b",
                r"\bphotos?\s+of\b",
                r"\bimages?\s+of\b",
            ],

            "Resource": [
                r"\blearn more\b",
                r"\bwhere can i\b",
                r"\bhow to learn\b",
                r"\blearning resources?\b",
                r"\bresources?\b",
                r"\bcourses?\b",
                r"\btutorials?\b",
                r"\bstudy materials?\b",
            ],

            "Example": [
                r"\bexamples?\s+of\b",
                r"\bgive\s+(?:me\s+)?an?\s+example\b",
                r"\bshow\s+(?:me\s+)?an?\s+example\b",
                r"\bexamples?\s+for\b",
                r"\breal[- ]world examples?\b",
                r"\bpractical examples?\b",
            ],

            "Definition": [
                r"^\s*what\s+is\b",
                r"^\s*what\s+are\b",
                r"^\s*what's\b",
                r"^\s*who\s+is\b",
                r"^\s*who\s+was\b",
                r"^\s*who\s+are\b",
                r"^\s*define\b",
                r"^\s*meaning\s+of\b",
                r"^\s*explain\b",
                r"^\s*tell\s+me\s+about\b",
                r"^\s*describe\b",
                r"^\s*what\s+does\b",
                r"^\s*where\s+is\b",
                r"^\s*where\s+was\b",
                r"^\s*when\s+is\b",
                r"^\s*when\s+was\b",
                r"^\s*why\s+is\b",
                r"^\s*why\s+do\b",
                r"^\s*why\s+does\b",
                r"^\s*how\s+does\b",
                r"^\s*how\s+do\b",
                r"^\s*how\s+did\b",
            ],
        }

    def recognize_intent(self, query):
        """
        Identify the user's intent.

        Returns:
            tuple: (intent_name, confidence_score)
        """

        if not isinstance(query, str) or not query.strip():
            return "Unknown", 0.0

        query_lower = re.sub(
            r"\s+",
            " ",
            query.lower().strip()
        )

        # 1. Match explicit patterns first.
        # Specific intents are checked before general definitions.
        intent_priority = [
            "Greeting",
            "Help",
            "Image",
            "Resource",
            "Example",
            "Definition",
        ]

        for intent in intent_priority:
            for pattern in self.intent_patterns[intent]:
                if re.search(pattern, query_lower):
                    return intent, 95.0

        # 2. Fuzzy matching for common short phrases.
        # Do not compare raw regex patterns with user questions.
        fuzzy_examples = {
            "Greeting": [
                "hello",
                "hi",
                "hey",
            ],
            "Help": [
                "help",
                "what can you do",
            ],
            "Example": [
                "give an example of",
                "show an example of",
                "real world example of",
            ],
            "Definition": [
                "what is",
                "what are",
                "define",
                "explain",
                "tell me about",
            ],
            "Image": [
                "show images of",
                "pictures of",
            ],
            "Resource": [
                "where can i learn",
                "learning resources",
            ],
        }

        best_intent = "Unknown"
        best_score = 0.0

        for intent, phrases in fuzzy_examples.items():
            for phrase in phrases:
                # Compare only the beginning of the query.
                # This helps avoid penalizing longer questions.
                query_prefix = query_lower[:len(phrase) + 10]

                score = fuzz.ratio(
                    phrase,
                    query_prefix
                )

                if score > best_score:
                    best_score = score
                    best_intent = intent

        # 3. Accept only high-confidence fuzzy matches.
        if best_score >= 85:
            return best_intent, round(best_score, 2)

        return "Unknown", round(best_score, 2)