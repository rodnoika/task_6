"""Development-only export of static dictionaries, never a user-data generator.

Download: python -m pip download --no-deps --dest database/vendor Faker==37.12.0
Rebuild:  python database/build_lookup_data.py
The application and database require neither Python Faker nor this script.
"""

from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parent
WHEEL = ROOT / "vendor" / "faker-37.12.0-py3-none-any.whl"
sys.path.insert(0, str(WHEEL))

from faker.providers.person.en_US import Provider as US  # noqa: E402
from faker.providers.person.de_DE import Provider as DE  # noqa: E402
from faker.providers.person.de_AT import Provider as AT  # noqa: E402
from faker.providers.person.de_CH import Provider as CH  # noqa: E402


US_CITIES = """New York|NY|10001|212
Los Angeles|CA|90012|213
Chicago|IL|60601|312
Houston|TX|77002|713
Phoenix|AZ|85003|602
Philadelphia|PA|19102|215
San Antonio|TX|78205|210
San Diego|CA|92101|619
Dallas|TX|75201|214
San Jose|CA|95113|408
Austin|TX|78701|512
Jacksonville|FL|32202|904
Fort Worth|TX|76102|817
Columbus|OH|43215|614
Indianapolis|IN|46204|317
Charlotte|NC|28202|704
San Francisco|CA|94102|415
Seattle|WA|98104|206
Denver|CO|80202|303
Washington|DC|20001|202
Boston|MA|02108|617
Nashville|TN|37219|615
El Paso|TX|79901|915
Portland|OR|97204|503
Las Vegas|NV|89101|702
Detroit|MI|48226|313
Memphis|TN|38103|901
Louisville|KY|40202|502
Baltimore|MD|21202|410
Milwaukee|WI|53202|414
Albuquerque|NM|87102|505
Tucson|AZ|85701|520
Fresno|CA|93721|559
Sacramento|CA|95814|916
Kansas City|MO|64106|816
Mesa|AZ|85201|480
Atlanta|GA|30303|404
Omaha|NE|68102|402
Colorado Springs|CO|80903|719
Raleigh|NC|27601|919
Miami|FL|33130|305
Virginia Beach|VA|23451|757
Oakland|CA|94612|510
Minneapolis|MN|55401|612
Tulsa|OK|74103|918
Arlington|TX|76010|817
New Orleans|LA|70112|504
Wichita|KS|67202|316
Cleveland|OH|44114|216
Tampa|FL|33602|813
Bakersfield|CA|93301|661
Aurora|CO|80012|303
Honolulu|HI|96813|808
Anaheim|CA|92805|714
Santa Ana|CA|92701|714
Riverside|CA|92501|951
Corpus Christi|TX|78401|361
Lexington|KY|40507|859
Henderson|NV|89015|702
Stockton|CA|95202|209
Saint Paul|MN|55102|651
Cincinnati|OH|45202|513"""

DE_CITIES = """Berlin|Berlin|10115|30
Hamburg|Hamburg|20095|40
München|Bayern|80331|89
Köln|Nordrhein-Westfalen|50667|221
Frankfurt am Main|Hessen|60311|69
Stuttgart|Baden-Württemberg|70173|711
Düsseldorf|Nordrhein-Westfalen|40213|211
Leipzig|Sachsen|04109|341
Dortmund|Nordrhein-Westfalen|44135|231
Essen|Nordrhein-Westfalen|45127|201
Bremen|Bremen|28195|421
Dresden|Sachsen|01067|351
Hannover|Niedersachsen|30159|511
Nürnberg|Bayern|90402|911
Duisburg|Nordrhein-Westfalen|47051|203
Bochum|Nordrhein-Westfalen|44787|234
Wuppertal|Nordrhein-Westfalen|42103|202
Bielefeld|Nordrhein-Westfalen|33602|521
Bonn|Nordrhein-Westfalen|53111|228
Münster|Nordrhein-Westfalen|48143|251
Karlsruhe|Baden-Württemberg|76133|721
Mannheim|Baden-Württemberg|68159|621
Augsburg|Bayern|86150|821
Wiesbaden|Hessen|65183|611
Gelsenkirchen|Nordrhein-Westfalen|45879|209
Mönchengladbach|Nordrhein-Westfalen|41061|2161
Braunschweig|Niedersachsen|38100|531
Kiel|Schleswig-Holstein|24103|431
Aachen|Nordrhein-Westfalen|52062|241
Chemnitz|Sachsen|09111|371
Halle (Saale)|Sachsen-Anhalt|06108|345
Magdeburg|Sachsen-Anhalt|39104|391
Freiburg im Breisgau|Baden-Württemberg|79098|761
Krefeld|Nordrhein-Westfalen|47798|2151
Mainz|Rheinland-Pfalz|55116|6131
Lübeck|Schleswig-Holstein|23552|451
Erfurt|Thüringen|99084|361
Oberhausen|Nordrhein-Westfalen|46045|208
Rostock|Mecklenburg-Vorpommern|18055|381
Kassel|Hessen|34117|561
Hagen|Nordrhein-Westfalen|58095|2331
Saarbrücken|Saarland|66111|681
Hamm|Nordrhein-Westfalen|59065|2381
Potsdam|Brandenburg|14467|331
Ludwigshafen am Rhein|Rheinland-Pfalz|67059|621
Oldenburg|Niedersachsen|26122|441
Leverkusen|Nordrhein-Westfalen|51373|214
Osnabrück|Niedersachsen|49074|541
Solingen|Nordrhein-Westfalen|42651|212
Heidelberg|Baden-Württemberg|69117|6221
Herne|Nordrhein-Westfalen|44623|2323
Neuss|Nordrhein-Westfalen|41460|2131
Darmstadt|Hessen|64283|6151
Paderborn|Nordrhein-Westfalen|33098|5251
Regensburg|Bayern|93047|941
Ingolstadt|Bayern|85049|841
Würzburg|Bayern|97070|931
Fürth|Bayern|90762|911
Wolfsburg|Niedersachsen|38440|5361
Offenbach am Main|Hessen|63065|69
Ulm|Baden-Württemberg|89073|731
Heilbronn|Baden-Württemberg|74072|7131
Pforzheim|Baden-Württemberg|75172|7231
Göttingen|Niedersachsen|37073|551
Bottrop|Nordrhein-Westfalen|46236|2041
Trier|Rheinland-Pfalz|54290|651
Reutlingen|Baden-Württemberg|72764|7121
Koblenz|Rheinland-Pfalz|56068|261
Bremerhaven|Bremen|27568|471
Recklinghausen|Nordrhein-Westfalen|45657|2361
Bergisch Gladbach|Nordrhein-Westfalen|51465|2202
Jena|Thüringen|07743|3641"""

US_STREETS = """Oak|Maple|Pine|Cedar|Elm|Birch|Willow|Walnut|Cherry|Chestnut|Ash|Spruce|Poplar|Sycamore|Hickory|Magnolia|Cypress|Redwood|Dogwood|Juniper|Holly|Laurel|Aspen|Beech|Acacia|Alder|Mulberry|Olive|Palm|Peach|Pear|Plum|Apple|Orchard|Garden|Rose|Lily|Violet|Daisy|Iris|Tulip|Jasmine|Azalea|Camellia|Meadow|Prairie|Valley|Hill|Ridge|Summit|Mountain|Canyon|River|Creek|Brook|Lake|Pond|Ocean|Bay|Harbor|Beach|Shore|Island|Forest|Woodland|Timber|Glen|Park|Field|Farm|Pasture|Mill|Bridge|Stone|Rock|Granite|Marble|Crystal|Diamond|Silver|Golden|Copper|Sunset|Sunrise|Morning|Evening|Moonlight|Starlight|Skyline|Horizon|Rainbow|Spring|Summer|Autumn|Winter|North|South|East|West|Central|Main|Broad|High|Market|Church|School|College|University|Academy|Library|Museum|Union|Liberty|Freedom|Independence|Constitution|Washington|Jefferson|Lincoln|Madison|Franklin|Hamilton|Jackson|Adams|Monroe|Harrison|Wilson|Grant|Roosevelt|Kennedy|King|Pioneer|Frontier|Heritage|Prospect|Pleasant|Fairview|Grand|Royal|Victoria|Regent|Windsor|Oxford|Cambridge|York|Essex|Kent|Suffolk|Norfolk|Berkshire|Devon|Dover|Canterbury|Lancaster|Bristol|Salem|Concord|Lexington|Georgetown|Richmond|Belmont|Arlington|Cleveland"""
DE_STREETS = """Linden|Berg|Haupt|Schul|Bahnhof|Garten|Blumen|Rosen|Wald|Feld|Kirch|Dorf|Bach|Mühlen|Brücken|Markt|Burg|Schloss|Park|See|Ufer|Wiesen|Tal|Höhen|Ring|Kastanien|Eichen|Buchen|Birken|Ahorn|Eschen|Erlen|Weiden|Pappel|Tannen|Fichten|Kiefern|Akazien|Robinien|Ulmen|Walnuss|Apfel|Kirsch|Birnen|Pflaumen|Obst|Sonnen|Mond|Stern|Himmel|Morgen|Abend|Frühlings|Sommer|Herbst|Winter|Nord|Süd|Ost|West|Freiheits|Friedens|Einheits|Heimat|Kaiser|Königs|Prinzen|Herzog|Grafen|Ritter|Jäger|Forst|Fischer|Bäcker|Schmiede|Handwerker|Weber|Töpfer|Hafen|Kanal|Deich|Damm|Wasser|Quellen|Brunnen|Stein|Felsen|Sand|Kies|Lehm|Ton|Gold|Silber|Kupfer|Eisen|Salz|Kreuz|Kloster|Kapellen|Pfarr|Dom|Spital|Krankenhaus|Rathaus|Gerichts|Amts|Post|Zoll|Grenz|Heer|Alpen|Taunus|Harz|Spree|Elb|Rhein|Donau|Mosel|Neckar|Isar|Main|Lech|Weser|Ems|Havel|Oder|Saale|Fulda|Werra|Lahn|Ruhr|Goethe|Schiller|Lessing|Heine|Brecht|Humboldt|Leibniz|Kant|Hegel|Beethoven|Mozart|Bach|Wagner|Brahms|Händel|Dürer|Cranach|Bauern|Winkel|Teich|Anger|Auen|Heide|Farn|Moos|Lerchen|Amsel|Drossel|Finken|Meisen|Adler|Falken|Habicht|Eulen|Fuchs|Dachs|Hasen|Reh|Hirsch|Biber|Otter|Igel"""


def quote(value):
    return "'" + str(value).replace("'", "''") + "'"


def unique(values):
    return list(dict.fromkeys(values))


def main():
    statements = [
        "-- Generated static lookup data. Source/version/license: database/NOTICE.md.",
        "-- Generated only at development time; no Python generator runs in this application.",
        "INSERT INTO faker.locales (code,label,country,country_code,address_template,street_template,phone_template,house_number_max) VALUES",
        "('en_US','English (United States)','United States','1','{number} {street}, {city}, {region} {postal}, United States','{stem} {suffix}','+1 ({area}) 555-{subscriber4}',9999),",
        "('de_DE','Deutsch (Deutschland)','Germany','49','{street} {number}, {postal} {city}, Deutschland','{stem}{suffix}','+49 {area} {subscriber7}',199)",
        "ON CONFLICT (code) DO NOTHING;",
    ]
    all_sets = {
        "en_US": {
            "first_name": list(US.first_names), "last_name": list(US.last_names),
            "street_stem": US_STREETS.split("|"),
            "street_suffix": ["Street", "Avenue", "Road", "Lane", "Drive", "Court", "Place", "Way", "Boulevard", "Terrace"],
            "title": ["Dr.", "Prof.", "Dr. med.", "Prof. Dr."],
            "eye_color": ["Brown", "Blue", "Green", "Hazel", "Gray", "Amber"],
            "address_format": [
                "{number} {street}, {city}, {region} {postal}, United States",
                "{number} {street}, Apt. {unit}, {city}, {region} {postal}, United States",
                "{number} {street}, Unit {unit}, {city}, {region} {postal}, United States",
            ],
            "phone_format": ["+1 ({area}) 555-{subscriber4}", "+1 {area}-555-{subscriber4}", "+1 {area} 555 {subscriber4}"],
        },
        "de_DE": {
            "first_name": list(DE.first_names),
            "last_name": list(DE.last_names) + list(AT.last_names) + list(CH.last_names),
            "street_stem": DE_STREETS.split("|"),
            "street_suffix": ["straße", "weg", "gasse", "allee"],
            "title": ["Dr.", "Prof.", "Dr. med.", "Prof. Dr."],
            "eye_color": ["Braun", "Blau", "Grün", "Haselnussbraun", "Grau", "Bernstein"],
            "address_format": [
                "{street} {number}, {postal} {city}, Deutschland",
                "{street} {number}, Whg. {unit}, {postal} {city}, Deutschland",
                "{street} {number}a, {postal} {city}, Deutschland",
            ],
            "phone_format": ["+49 {area} {subscriber7}", "+49 {area}/{subscriber7}", "+49 ({area}) {subscriber7}"],
        },
    }
    # Local, gender-neutral academic titles avoid pairing random honorifics with names.
    all_sets["en_US"]["title"] = ["Dr.", "Prof.", "Rev.", "Mx."]
    for locale, sets in all_sets.items():
        for kind, values in sets.items():
            vals = unique(values)
            statements.append("INSERT INTO faker.lookup_sets (locale,kind,entries) VALUES (" + quote(locale) + "," + quote(kind) + ",ARRAY[" + ",".join(map(quote, vals)) + "]::text[]) ON CONFLICT (locale,kind) DO NOTHING;")
            print(locale, kind, len(vals))
    for locale, raw in [("en_US", US_CITIES), ("de_DE", DE_CITIES)]:
        rows = []
        for i, line in enumerate(raw.splitlines(), 1):
            rows.append("(" + ",".join([quote(locale), str(i)] + list(map(quote, line.split("|")))) + ")")
        statements.append("INSERT INTO faker.cities (locale,ordinal,name,region,postal_code,calling_code) VALUES\n" + ",\n".join(rows) + "\nON CONFLICT (locale,ordinal) DO NOTHING;")
        print(locale, "cities", len(rows))
    (ROOT / "002_lookup_data.sql").write_text("\n".join(statements) + "\n", encoding="utf-8")
    with zipfile.ZipFile(WHEEL) as wheel:
        (ROOT / "vendor" / "Faker-LICENSE.txt").write_bytes(wheel.read("faker-37.12.0.dist-info/licenses/LICENSE.txt"))


if __name__ == "__main__":
    main()
