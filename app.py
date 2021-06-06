from typing import List, Dict
import random
import json
import sys

from collections import defaultdict

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


def markov(text, tags_dict):
    # text_model = POSifiedText(text, state_size=2)
    text_model = markovify.Text(text, state_size=2)

    # VBZ: verb, present tense, 3rd person singular
    verbs = tags_dict["VBZ"]
    # print(verbs)

    for _ in range(0, 100):
        try:
            # print(text_model.make_sentence())
            print(
                "AWS Test",
                text_model.make_sentence_with_start(
                    beginning=start_expression(verbs), strict=False
                ),
            )
        except markovify.text.ParamError:
            continue
        break


def service_name(existing_names, tags_dict):
    name = []

    # Brand: AWS or Amazon
    brand = random.choice(["AWS", "Amazon"])

    # Nouns
    # NNP: noun, proper, singular
    # NNS: noun, common, plural
    nnp = tags_dict["NNP"]
    nns = tags_dict["NNS"]

    # Verbs
    # VB: verb, base form
    vb = tags_dict["VB"]

    name.append(brand)

    return " ".join(name)


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

    # Generate
    # markov(text, tags_dict)

    # Item names
    existing_names = [i["name"] for i in items]

    from nltk.probability import FreqDist

    all_names = " ".join(existing_names)
    all_names_tokens = word_tokenize(all_names)

    fdist = FreqDist(all_names_tokens)
    top_ten = fdist.most_common(10)
    print(top_ten)

    # print(service_name(existing_names, tags_dict))
