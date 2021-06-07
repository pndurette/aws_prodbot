from typing import List, Dict
import random
import json
import sys

from collections import defaultdict

from nltk.probability import FreqDist
from nltk import word_tokenize
import nltk

import markovify

import re

# NLTK tags reference:
# https://stackoverflow.com/a/38264311
# https://www.ling.upenn.edu/courses/Fall_2003/ling001/penn_treebank_pos.html


def load_items(filename) -> List[Dict]:
    with open(filename, "r") as f:
        return json.load(f)


def nltk_tags_by_tag(nltk_tags):
    words_dict = defaultdict(list)

    for t in nltk_tags:
        word, type = t

        if word in ["amazon", "aws"]:
            continue
        if word in words_dict[type]:
            continue

        words_dict[type].append(word.strip())

    return words_dict


def nltk_tags(text):
    tokens = word_tokenize(text)
    return nltk.pos_tag(tokens)


def start_expression(verbs):
    exps = ["is a", "is an", random.choice(verbs)]
    exps_weights = [40, 20, 40]
    return random.choices(population=exps, weights=exps_weights)[0]


class POSifiedText(markovify.Text):
    def word_split(self, sentence):
        words = re.split(self.word_split_pattern, sentence)
        words = ["::".join(tag) for tag in nltk.pos_tag(words)]
        return words

    def word_join(self, words):
        sentence = " ".join(word.split("::")[0] for word in words)
        return sentence


def service_desc(text, tags_dict, service_name):
    # text_model = POSifiedText(text, state_size=2)
    text_model = markovify.Text(text, state_size=2)

    # VBZ: verb, present tense, 3rd person singular
    verbs = tags_dict["VBZ"]
    # print(verbs)

    for _ in range(0, 100):
        try:
            # return text_model.make_sentence()
            # return "AWS Test " \
            #     + text_model.make_sentence_with_start(
            #         beginning=start_expression(verbs), strict=False
            #     )
            return text_model.make_sentence_with_start(
                    beginning=start_expression(verbs), strict=False
                )
        except markovify.text.ParamError:
            continue
        break


def service_name(names_list, tags_dict):

    # Nouns
    # NN: noun, singular or mass
    # NNP: noun, proper, singular
    # NNS: noun, common, plural
    nn = tags_dict["NN"]
    nnp = tags_dict["NNP"]
    nns = tags_dict["NNS"]

    # Keep names longer than 2 chars
    nn = [i for i in nn if len(i) > 2]
    nnp = [i for i in nnp if len(i) > 2]

    # Verbs
    # VB: verb, base form
    vb = tags_dict["VB"]

    # Keep verbs longer than 2 chars
    vb = [i for i in vb if len(i) > 2]

    # Extra words
    extra_words = ["plant", "coffee"]

    # Extract info from existing names

    # Remove AWS & Amazon
    # (except at the end)
    names_list = [re.sub(r"(AWS.)|(Amazon.)", "", n) for n in names_list]

    # Remove things in parentheses
    # e.g. '(SNS)', '(Preview)'
    names_list = [re.sub(r" ?\([^)]+\)", "", n) for n in names_list]

    # Add space before capital
    # e.g. "CloudWatch" to "Cloud Watch"
    # Only when the next letter isn't a capital or space,
    # so it doesn't split accronyums (e.g. 'EKS')
    names_list = [re.sub(r"([A-Z][^A-Z\s\d])", " \\1", n) for n in names_list]

    # Clean up
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
    Types of names
    <Brand> <Prefix><Name> <Suffix>
    <Brand> <Prefix><name> <Suffix>
    <Brand> <Prefix> <Name>
    <Brand> <Name> for <Name>
    <Brand> <Prefix> <Prefix> <Name>
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
        50,
        50,
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

    # print(name)
    return " ".join(name)


def _capitalize(str):
    # Like str.capitlize() but only changes the first letter"
    if len(str) == 0:
        return ""
    elif len(str) == 1:
        return str[0].upper()
    else:
        return str[0].upper() + str[1:]


if __name__ == "__main__":
    # Load items (json)
    # Usage: app.py <file.json>
    filename = sys.argv[1]
    items = load_items(filename)

    # Create continous text from item descriptions
    text = " ".join([i["desc"] for i in items])

    # Create nltk tags from text
    tags = nltk_tags(text)
    tags_dict = nltk_tags_by_tag(tags)

    # Item names
    existing_names = [i["name"] for i in items]

    for _ in range(1):
        service_name = service_name(existing_names, tags_dict)
        service_desc = service_desc(text, tags_dict, service_name)

        body = f"{service_name}\n\n{service_desc}"

        print(body)
        print()

    import pprint
    # pprint.pprint(tags_dict)
    # pprint.pprint(existing_names)


"""
# TODO
* Remove names that aren't just letters or numbers
* Set some words that can't be seperated (DevOps, SageMaker)
"""