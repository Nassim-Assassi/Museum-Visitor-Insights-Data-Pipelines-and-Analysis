from wednesday import morse_translator, slash_morse_translator, message_to_morse


def test_morse_translator():
    assert morse_translator("-... . .") == "BEE"


def test_morse_translator_invalid_char():
    assert morse_translator(".-- --- .-.. .-.-.-- . ...") == "WOL?ES"


def test_slash_morse_translator():
    assert slash_morse_translator(
        ".. / .- -- / -. --- - / .- ..-. .-. .- .. -.. / --- ..-. / .-- --- .-.. ...- . ...") == "I AM NOT AFRAID OF WOLVES"


def test_word_to_morse():
    assert message_to_morse("ABC") == ".- -... -.-."


def test_message_to_morse():
    assert message_to_morse("AB C") == ".- -... / -.-."


def test_message_to_morse_lower():
    assert message_to_morse("ab c") == ".- -... / -.-."


def test_message_to_morse_non_alpanumeric():
    assert message_to_morse("ab% c?") == ".- -... / -.-."
