import json
from tqdm import tqdm
import os
from datetime import date, timedelta
import csv
import jsonlines
import re 


def convert_for_covid(row):

    covid_terms = ["2019 novel coronavirus disease", "COVID19", "COVID-19 pandemic", "SARS-CoV-2 infection",
                   "COVID-19 virus disease", "2019 novel coronavirus infection", "2019-nCoV infection",
                   "coronavirus disease 2019", "coronavirus disease-19", "2019-nCoV disease",
                   "COVID-19 virus infection", "COVID-19"]
    covid_terms = [term.lower() for term in covid_terms]

    non_covid_terms = ["infection", "infections", "SARS-CoV-2", "SARS-CoV-2 virions",
                       "SARS-CoV-2 virion", "SARS"]
    non_covid_terms = [term.lower() for term in non_covid_terms]

    cleaned_ents = []
    cleaned_ents_title = []
    abstract = row["abstract"]
    ents = row["ents"]
    title_ents = row["title_ann"]["ents"]
    title = row["title_ann"]["text"]

    # we need to iterate over already annotated entities first:
    # iterate over title entities
    for ent in title_ents:
        not_found = True
        begin = ent["start"]
        end = ent["end"]
        word = title[begin:end]
        label = ent["label"]
        concept = ent["concept"]
        for cov in covid_terms:
            if word.lower() in cov and cov in title.lower():
                not_found = False
                begin_cleaned = title.lower().index(cov)
                end_cleaned = begin_cleaned+len(cov)
                entry = {"start": begin_cleaned, "end": end_cleaned,
                         "label": "MESHD", "concept": "http://id.nlm.nih.gov/mesh/D000086382",
                         "covered_text": cov}
                cleaned_ents_title.append(entry)
        if not_found:
            if word.lower() not in non_covid_terms:
                cleaned_ents_title.append(ent)

    # then we need to go over free text and add missing annotations:
    for cov in covid_terms:
        if cov in title.lower():
            starts = [m.start() for m in re.finditer(cov, title.lower())]
            for begin in starts:
                end = begin+len(cov)
                concept = "http://id.nlm.nih.gov/mesh/D000086382"
                entry = {"start": begin, "end": end,
                         "label": "MESHD", "concept": concept,
                         "covered_text": cov}
                if begin not in [x["start"] for x in cleaned_ents_title]:
                    cleaned_ents_title.append(entry)

    # remove duplicates:
    cleaned_ents_title = [dict(t) for t in {tuple(d.items()) for d in cleaned_ents_title}]
    # sort by starting index
    cleaned_ents_title.sort(key=lambda x: x["start"])
    row["title_ann"]["ents"] = cleaned_ents_title

    # iterate over abstract annotations
    for ent in ents:
        not_found = True
        begin = ent["start"]
        end = ent["end"]
        word = abstract[begin:end]
        label = ent["label"]
        concept = ent["concept"]
        for cov in covid_terms:
            if word.lower() in cov and cov in abstract.lower():
                not_found = False
                begin_cleaned = abstract.lower().index(cov)
                end_cleaned = begin_cleaned+len(cov)
                entry = {"start": begin_cleaned, "end": end_cleaned,
                         "label": "MESHD", "concept": "http://id.nlm.nih.gov/mesh/D000086382",
                        "covered_text": cov}
                cleaned_ents.append(entry)

        if not_found:
            if word.lower() not in non_covid_terms:
                cleaned_ents.append(ent)

    # go over free text and add missing annotations:
    for cov in covid_terms:
        if cov in abstract.lower():
            starts = [m.start() for m in re.finditer(cov, abstract.lower())]
            for begin in starts:
                #begin = abstract.lower().index(cov)
                end = begin+len(cov)
                concept = "http://id.nlm.nih.gov/mesh/D000086382"
                entry = {"start": begin, "end": end, "label": "MESHD", "concept": concept,"covered_text": cov}
                if begin not in [x["start"] for x in cleaned_ents]:
                    cleaned_ents.append(entry)

    # remove duplicates:
    cleaned_ents = [dict(t) for t in {tuple(d.items()) for d in cleaned_ents}]
    # sort
    cleaned_ents.sort(key=lambda x: x["start"])
    row["ents"] = cleaned_ents

    return row


if __name__ == '__main__':
    with jsonlines.open("preprints.jsonl", "r") as reader:
        for js in reader:
            js = convert_for_covid(js)
            with jsonlines.open("final.jsonl", "a") as writer:
                writer.write(js)
