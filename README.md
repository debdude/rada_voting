# Rada voting scraping, parsing, and analysis

Verkhovna Rada (Parliament of Ukraine) publishes detailed voting records. Unfortunately, these records are published as individual html documents and no API is provided. 

This repo contains these records, both as original HTML, and parsed into CSVs; and also provides the script used to dl and parse them

## Records

As of Oct 5, 2020, **5424** vote records were captured in `source_docs` folder, which were parsed into `votes.csv` file and **2,292,228** individual votes in `votes.csv.gz`


## Requirements

* Python >= 3.8

## Installation

`pip install -r requirements.txt`

## Usage

`rada.py [-h] [--start START] [--end END] {parse,scrape,reparse}`

Following commands are supported:

#### `parse`
Downloads a range of documents from Rada's site, saves them into `source_docs`, and parses them into CSVs

#### `scrape`

Downloads a range of docs and simply saves them.

#### `reparse`

Re-parses all documents in `source_docs` into CSVs


`--start` and `--end` optional params: limit range of docs to download for `parse` and `scrape` commands. For current Rada, about 5000 vote documents are available, starting with `25` and ending around `7800` (as of October 5th, 2020). Default is get all.

## Output

Downloaded htmls are saved into `source_docs` as vote_NNNN.html

Parsed votes are saved into two CSVs:
* vote_headers.csv
* votes.csv.gz (compressed)


