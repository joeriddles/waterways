from typing import Iterable
import csv
import logging
import re

import bs4
import pathlib
import requests

logger = logging.Logger(__name__)
logger.addHandler(logging.StreamHandler())

URL = "https://www.cia.gov/the-world-factbook/field/waterways/"

"""Parse 123,456km or 123km."""
KM_PATTERN = re.compile(r"(\d{1,3})?,?(\d{1,3})\W?km")

def main():
    contents: str = ""
    cached_path = pathlib.Path("./cached.html")
    if cached_path.exists():
        with open(cached_path) as fin:
            contents = fin.read()

    if contents == "":
        response = requests.get(URL)
        response.raise_for_status()
        contents = response.content.decode()
        with open(cached_path, "w") as fout:
            fout.write(contents)

    soup = bs4.BeautifulSoup(contents, "html.parser")
    
    main_content: bs4.Tag | None = soup.find(attrs={"id": "main-content"})  # type: ignore
    if main_content is None:
        raise ValueError("Could not find .main-content")
    
    countries: Iterable[bs4.Tag] = main_content.find_all(class_="pb30")
    countries_and_wateryways: list[tuple[str, int]] = []
    for country in countries:
        heading = country.find_next("h3")
        if heading is None:
            logger.warning("could not parse heading for %s", country.prettify()[:100])
            continue
        
        country_name = heading.text

        country_km = 0
        try:
            matches = KM_PATTERN.findall(country.text)
            if len(matches):
                match: list[str] = matches[0]
                country_km = int("".join(match))
        except: # TODO: more specific exception handler
            continue # TODO: log 

        countries_and_wateryways.append((country_name, country_km))

    countries_and_wateryways = sorted(countries_and_wateryways, key=lambda tup: tup[1], reverse=True)
    for country, waterway in countries_and_wateryways:
        print(f"{country}: {waterway}km")

    with open("countries.csv", "w") as fout:
        writer = csv.DictWriter(fout, ["Country", "Waterways Length (km)"])
        writer.writeheader()
        writer.writerows([
            {"Country": country, "Waterways Length (km)": km}
            for country, km
            in countries_and_wateryways
        ])
    

if __name__ == "__main__":
    main()
