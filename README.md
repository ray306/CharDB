# CharDB: A Comprehensive Database and Search Engine of Chinese Characters

@Jinbiao Yang

The number of Chinese characters is more than twenty thousand. Each
character has its pronunciation, written form, meaning, and other attributes.
Should we need to investigate the characters, a lot of databases are available.
But there were two major difficulties to make use of the databases. The first is
the information integrality, each database contained only partial information of
partial Chinese characters; the second is the user interface, most of the databas-
es provided only the search entry to the written characters or the pinyins, but
not to the rest of the attributes. In order to facilitate the studies of Chi-
nese characters, we provide a database, CharDB (https://chardb.cls.ru.nl/),
which contains massive information (spoken forms, written forms, frequencies,
variants, encodings, etc.) from various sources [5, 4, 1, 2] for 20,902 characters
in the first version of CJK Unifi ed Ideographs([3], U+4E00 ～ U+9FA5), and
a search engine that can filter all the attributes in the database and flexibly
combine the filtering conditions. In case researchers need to store or analyze
the filtered result, CharDB will export an offline sheet. Besides, we providea
Chinese word database which covers word frequencies[4] and is also linked with
the character database. So researchers can find the words fitted their needs,or
get the word attributes of their provided word list.

## References

[1] CRAN - package tmcn. https://cran.r-project.org/web/packages/
tmcn/index.html. Accessed: 2019-2-26.

[2] UAX #38: Unicode han database (unihan). http://www.unicode.org/
reports/tr38/tr38-21.html. Accessed: 2019-2-26.

[3] Unihan database. https://unicode.org/charts/unihangridindex.html.
Accessed: 2019-2-26.

[4] Qing Cai and Marc Brysbaert. SUBTLEX-CH: Chinese word and character
frequencies based on film subtitles. PLoS One, 5(6), 2010.

[5] Tomohiko Morioka. CHISE: Character processing based on character ontology.
In Large-Scale Knowledge Resources. Construction and Application,
pages 148–162. Springer Berlin Heidelberg, 2008.
