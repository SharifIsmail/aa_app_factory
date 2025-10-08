Some helper scripts to scrape legal acts from CELLAR / EUR-LEX

Subfolder *notebooks* contains customer signals on relevant EU law and a notebook to get that
data into shape and aligned with EUR-LEX data.

From playground/eu-law folder run
uv run --with jupyter jupyter lab

Subfolder *eur-lex* contains Excel lists with metadata on OJ publications from 2023 to 2025.
You can use the script "scrape-eur-lex.py" to download metadata for any range of dates.
It seems that Origianl Journal (OJ) publications only started in October 2023. Hence, before
that date, no metadata for publications is retrieved.

From playground/eu-law folder run
uv run scrape-eur-lex.py 2025-05-14 2025-05-14 eur-lex