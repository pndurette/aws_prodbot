import json
import logging
import logging.config
import random
import re
import sys
from collections import defaultdict
from typing import Dict, List, Tuple

import markovify
import nltk
from nltk import word_tokenize
from nltk.probability import FreqDist

# Logger settings
LOGGER_SETTINGS = {
    "version": 1,
    "formatters": {
        "default": {
            "format": "%(asctime)s %(funcName)s:%(lineno)s - %(levelname)s - %(message)s"
        }
    },
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "default"}},
    "loggers": {"app.py": {"handlers": ["console"], "level": "DEBUG"}},
}

# Logger
logging.config.dictConfig(LOGGER_SETTINGS)
log = logging.getLogger("app.py")

# NLTK tags reference:
# https://stackoverflow.com/a/38264311
# https://www.ling.upenn.edu/courses/Fall_2003/ling001/penn_treebank_pos.html

# Setup:
# >>> import nltk
# >>> nltk.download('punkt')
# >>> nltk.download('averaged_perceptron_tagger')


def load_items(filename: str) -> List[Dict]:
    with open(filename, "r") as f:
        return json.load(f)


def nltk_tags(text: str) -> List[Tuple[str, str]]:
    # Calculate the nltk tags
    # e.g. [(<word>, <tag>), ...]
    tokens = word_tokenize(text)
    return nltk.pos_tag(tokens)


def nltk_tags_by_tag(nltk_tags: List[Tuple[str, str]]) -> Dict:
    # Tranform an nltk tags output into a dictionnary
    # of word lists per tag
    # e.g. [(<word>, <tag>), (<word>, <tag>), ...]
    #  to: { <tag>: [<word>, <word>]}

    words_dict = defaultdict(list)

    for t in nltk_tags:
        word, type = t

        if word in ["amazon", "aws"]:
            continue
        if word in words_dict[type]:
            continue

        words_dict[type].append(word.strip())

    return words_dict


def start_expression(verbs: List) -> str:
    # Generate the start of service description (after the namer),
    # to ease Markov Chains completion
    # i.e. is a|is an|<a verb>
    exps = ["is a", "is an", random.choice(verbs)]
    exps_weights = [40, 20, 40]
    return random.choices(population=exps, weights=exps_weights)[0]


class POSifiedText(markovify.Text):
    # Class to use nltk's tagging and word split
    def word_split(self, sentence):
        words = re.split(self.word_split_pattern, sentence)
        words = ["::".join(tag) for tag in nltk.pos_tag(words)]
        return words

    def word_join(self, words):
        sentence = " ".join(word.split("::")[0] for word in words)
        return sentence


def service_desc(corpus: str, tags_dict: Dict, max_len: int):
    # Generate a service mane using Markov Chains
    # Uses the whole corpus text, tags dict and specifies a max lenght

    # text_model = POSifiedText(text, state_size=2)
    text_model = markovify.Text(corpus, state_size=2)

    # VBZ: verb, present tense, 3rd person singular
    verbs = tags_dict["VBZ"]

    # Retry many times to make sure a sentence with start is generated
    # Also implement the logic of 'make_short_sentence()'
    for i in range(0, 100):
        try:
            # sentence = text_model.make_sentence()
            sentence = text_model.make_sentence_with_start(
                beginning=start_expression(verbs), strict=False
            )
            
            log.debug(f"Run #{i}, {max_len=} {len(sentence)=}")
            
            if len(sentence) <= max_len:
                return sentence
            else:
                continue

        except markovify.text.ParamError:
            continue
        break


def service_name(names_list, tags_dict):
    # Generate a service mane already existing nounds and words
    # Uses statistics and frequence of usage of some existing words
    # and some AWS service name formats

    # Nouns
    # NN: noun, singular or mass
    # NNP: noun, proper, singular
    # NNS: noun, common, plural
    nn = tags_dict["NN"]
    nnp = tags_dict["NNP"]
    nns = tags_dict["NNS"]

    # Keep nouns longer than 2 chars
    nn = [i for i in nn if len(i) > 2]
    nnp = [i for i in nnp if len(i) > 2]

    # Remove common 'nouns' that have other than letters, numbers or dashes
    nn = [i for i in nn if re.search(r"^[a-zA-Z0-9-]+$", i)]

    # Verbs
    # VB: verb, base form
    vb = tags_dict["VB"]

    # Keep verbs longer than 2 chars
    vb = [i for i in vb if len(i) > 2]

    # Extract info from existing names

    # Remove AWS & Amazon
    # Except at the end e.g. "<stuff> for AWS"
    names_list = [re.sub(r"(AWS.)|(Amazon.)", "", n) for n in names_list]

    # Remove things in parentheses
    # e.g. '(SNS)', '(Preview)'
    names_list = [re.sub(r" ?\([^)]+\)", "", n) for n in names_list]

    # Add space before capital
    # e.g. "CloudWatch" to "Cloud Watch"
    # Only when the next letter isn't a capital or space,
    # so it doesn't split accronyums (e.g. 'EKS')
    names_list = [re.sub(r"([A-Z][^A-Z\s\d])", " \\1", n) for n in names_list]

    # Clean up (remove extra staces (join(split)) and remove trail/lead spaces)
    names_list = [" ".join(n.split()).strip() for n in names_list]

    # Extract prefix and suffix terms
    prefix_list = []
    suffix_list = []
    for n in names_list:
        if re.search(r"\s", n):
            tokens = n.split()
            prefix_list.append(tokens[0])
            suffix_list.append(tokens[-1])

    # print(names_list)

    # Calculate frequency of prefix and suffix
    prefix_fdist = FreqDist(prefix_list)
    suffix_fdist = FreqDist(suffix_list)

    # FreqDist.most_common gives returns
    # [(<word>, <count>), (<word>, <count>), ...]
    # in order of frequency, keep the most common words
    top_prefixes, _ = zip(*prefix_fdist.most_common(12))
    top_suffixes, _ = zip(*suffix_fdist.most_common(12))

    top_prefixes = list(top_prefixes)
    top_suffixes = list(top_suffixes)

    """
    Service names examples:
        <Brand> <Prefix><Name> <Suffix>
        <Brand> <Prefix><name> <Suffix>
        <Brand> <Prefix> <Name>
        <Brand> <Name> for <Name>
        <Brand> <Prefix> <Prefix> <Name>
        etc..
    """

    # Name components

    # Brand: AWS or Amazon
    brand = random.choice(["AWS", "Amazon"])

    # Prefix
    prefix_exps = [
        "",  # No prefix
        random.choice(top_prefixes),  # Top prefixes from existing products
    ]
    prefix_weights = [
        10,
        50,
    ]
    prefix = random.choices(prefix_exps, prefix_weights)[0]

    # 'Middle name'
    # e.g. "ThisThat", "Thisthat", "This That", "This", "That"
    middle_name_exps_a = [
        "",  # Nothing
        random.choice(nn),  # Alredy used nouns
        random.choice(vb),  # Alread used infinitive verbs
    ]
    middle_name_exps_b = [
        "",  # Nothing
        random.choice(nn),  # Alredy used nouns
        random.choice(vb),  # Alread used infinitive verbs
    ]

    middle_name_weight_a = [10, 70, 20]
    middle_name_weight_b = [10, 20, 70]

    middle_name_a = random.choices(middle_name_exps_a, middle_name_weight_a)[0]
    middle_name_b = random.choices(middle_name_exps_b, middle_name_weight_b)[0]

    middle_name = random.choice(
        [
            _capitalize(f"{middle_name_a}{middle_name_b}"),
            f"{_capitalize(middle_name_a)}{_capitalize(middle_name_b)}",
            f"{_capitalize(middle_name_a)} {_capitalize(middle_name_b)}",
        ]
    )

    # Suffix
    suffix_exps = [
        "",  # No prefix
        random.choice(top_suffixes),  # Top suffixes from existing products
    ]
    suffix_weights = [
        60,
        40,
    ]
    suffix = random.choices(suffix_exps, suffix_weights)[0]

    # Purpose
    # e.g. "for <something>"
    purpose_exps = [
        "",  # No prefix
        f"for {random.choice(nnp)}",  # Top prefixes from existing products
    ]
    purpose_weights = [
        90,
        10,
    ]
    purpose = random.choices(purpose_exps, purpose_weights)[0]

    # Build the name
    name = []
    name.append(brand)
    name.append(prefix)
    name.append(middle_name)
    name.append(suffix)
    name.append(purpose)

    # Clean (strip and remove empty tokens)
    name = [n.strip() for n in name if len(n) > 0]
    
    # Join into a single string
    name_str = " ".join(name)

    log.debug(f"{name=}")
    log.debug(f"{len(name_str)=}, {name_str=}")

    return name_str


def _capitalize(str):
    # Like str.capitlize() but only changes the first letter
    if len(str) == 0:
        return ""
    elif len(str) == 1:
        return str[0].upper()
    else:
        return str[0].upper() + str[1:]


def format_tweet(service_name: str, service_desc: str) -> str:
    tweet = f"{service_name}\n\n{service_name} {service_desc}"
    log.debug(f"{len(tweet)=}, {tweet=}")
    return tweet


if __name__ == "__main__":
    # Load items (json)
    # Usage: app.py <file.json>
    filename = sys.argv[1]
    items = load_items(filename)

    # Create corpus from item blurbs and descriptions
    blurbs = [i["blurb"] for i in items]
    descs = [i["desc"] for i in items]
    corpus = " ".join(blurbs + descs)

    # Create nltk tags from corpus
    tags = nltk_tags(corpus)
    tags_dict = nltk_tags_by_tag(tags)

    # Item names
    existing_names = [i["name"] for i in items]

    for _ in range(5):
        # Service name
        name = service_name(existing_names, tags_dict)

        # Space left for service description
        # (from maximum Tweet lenght of 280 chars)
        desc_max_len = 280 - len(name)

        # Service description
        desc = service_desc(corpus, tags_dict, desc_max_len)

        # Tweet
        tweet = format_tweet(name, desc)

        print(tweet)
        print("-")

    # import pprint
    # pprint.pprint(tags_dict)
    # pprint.pprint(existing_names)
