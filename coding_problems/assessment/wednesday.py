"""
".-": 'A', "-...": 'B', "-.-.": 'C', "-..": 'D', ".": 'E', "..-.": 'F',
"--.": 'G', "....": 'H', "..": 'I', ".---": 'J', "-.-": 'K', ".-..": 'L',
"--": 'M', "-.": 'N', "---": 'O', ".--.": 'P', "--.-": 'Q', ".-.": 'R',
"...": 'S', "-": 'T', "..-": 'U', "...-": 'V', ".--": 'W', "-..-": 'X',
"-.--": 'Y', "--..": 'Z', ".----": '1', "..---": '2', "...--": '3',
"....-": '4', ".....": '5', "-....": '6', "--...": '7', "---..": '8',
"----.": '9', "-----": '0'

"""

morse_code_dictionary = {".-": 'A', "-...": 'B', "-.-.": 'C', "-..": 'D', ".": 'E', "..-.": 'F',
                         "--.": 'G', "....": 'H', "..": 'I', ".---": 'J', "-.-": 'K', ".-..": 'L',
                         "--": 'M', "-.": 'N', "---": 'O', ".--.": 'P', "--.-": 'Q', ".-.": 'R',
                         "...": 'S', "-": 'T', "..-": 'U', "...-": 'V', ".--": 'W', "-..-": 'X',
                         "-.--": 'Y', "--..": 'Z', ".----": '1', "..---": '2', "...--": '3',
                         "....-": '4', ".....": '5', "-....": '6', "--...": '7', "---..": '8',
                         "----.": '9', "-----": '0'}

reverse_morse_code_dictionary = {'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
                                 'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..', 'M': '--',
                                 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
                                 'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-', 'Y': '-.--',
                                 'Z': '--..', '1': '.----', '2': '..---', '3': '...--', '4': '....-', '5': '.....', '6':
                                 '-....', '7': '--...', '8': '---..', '9': '----.', '0': '-----'}


def morse_translator(morse: str) -> str:
    morse_characters = morse.split(" ")
    real_characters = [morse_code_dictionary.get(character, "?")
                       for character in morse_characters]

    out_string = "".join(real_characters)
    return out_string


def slash_morse_translator(morse: str) -> str:
    morse_words = morse.split(" / ")
    real_words = []
    for word in morse_words:
        real_words.append(morse_translator(word))
    sentence = " ".join(real_words)
    return sentence


def reverse_dict(map: dict):
    reversed_dict = {}
    for key, value in map.items():
        reversed_dict.update({value: key})
    return reversed_dict


def message_to_morse(message: str) -> str:
    """
    Removes non alphanumeric characters
    split at whitespace
    for each word, split into characters
    for each character, get the morse code from the reverse dictionary
    join the morse code for each character into a word
    join the morse code for each word into a sentence
    """
    cleaned_characters = []
    for character in message.upper():
        if character.isalnum() or character.isspace():
            cleaned_characters.append(character)

    cleaned_message = "".join(cleaned_characters)
    words = cleaned_message.split()

    morse_words = []
    for word in words:
        morse_letters = []
        for character in word:
            morse_letters.append(reverse_morse_code_dictionary[character])
        morse_words.append(" ".join(morse_letters))

    return " / ".join(morse_words)


if __name__ == "__main__":
    print(reverse_dict(morse_code_dictionary))
