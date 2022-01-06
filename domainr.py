import whois

import json
import structlog
import concurrent.futures
from random import shuffle
from typing import Optional


logger = structlog.get_logger()


FILE = 'words.json'
OUTPUT_FILE = 'available.txt'
TLDS = ['io']
MAXLEN = 4


def plural(word: str) -> Optional[str]:
    if word[-1] != 's':
        return f'{word}s'


def is_available(url: str) -> bool:
    try:
        domain = whois.query(url)
    except whois.exceptions.WhoisCommandFailed:
        return False
    return domain is None


def main() -> int:
    filter_funcs = [lambda word: len(word) <= MAXLEN]
    transform_funcs = [lambda word: word, plural]

    with open(FILE, 'r') as f:
        words = list(json.loads(f.read()).keys())

    logger.info(f'Words total: {len(words)}')

    for func in filter_funcs:
        words = list(filter(func, words))

    shuffle(words)
    logger.info(f'After filtering: {len(words)}')

    res = []
    candidates = []

    for word in words:
        for func in transform_funcs:
            if (new_word := func(word)) is not None:
                for tld in TLDS:
                    url = f'{new_word}.{tld}'
                    candidates.append(url)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_url = {
            executor.submit(is_available, candidate): candidate
            for candidate in candidates
        }
        for future in concurrent.futures.as_completed(future_to_url):
            if future.result() is True:
                logger.info(f'{future_to_url[future]} is available!')
                res.append(future_to_url[future])

    with open(OUTPUT_FILE, 'w') as f:
        for available in res:
            f.write(f'{available}\n')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
