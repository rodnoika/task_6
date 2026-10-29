-- Original, versioned training text and all Markov algorithms live in PostgreSQL.
CREATE TABLE IF NOT EXISTS faker.text_corpora (
    locale text NOT NULL REFERENCES faker.locales(code),
    model_version text NOT NULL,
    corpus text NOT NULL CHECK (length(btrim(corpus)) > 0),
    attribution text NOT NULL,
    PRIMARY KEY (locale, model_version)
);

CREATE TABLE IF NOT EXISTS faker.markov_transitions (
    locale text NOT NULL,
    model_version text NOT NULL,
    previous_first text NOT NULL,
    previous_second text NOT NULL,
    next_token text NOT NULL,
    weight integer NOT NULL CHECK (weight > 0),
    PRIMARY KEY (locale, model_version, previous_first, previous_second, next_token),
    FOREIGN KEY (locale, model_version) REFERENCES faker.text_corpora(locale, model_version)
);

-- Each line is a sentence. Shared contexts allow genuinely new word sequences.
INSERT INTO faker.text_corpora VALUES ('en_US', 'sql-markov-v1', $english$
The morning train follows the river through the green hills.
The morning light fills the small cafe by the river.
The morning breeze carries the scent of bread through the quiet street.
The evening train carries a new story to the old station.
The evening light touches the old bridge and the quiet garden.
The evening breeze moves through the garden after the rain.
The quiet garden welcomes the city with a little shade.
The quiet street leads to the market beside the river.
The quiet library holds a new story for every visitor.
In the city a new story begins at the station.
In the garden a small bird sings after the rain.
In the library a new journey begins with a book.
In the market the scent of bread meets the morning breeze.
In the forest the green path leads to the river.
We follow the green path through the old forest.
We follow a small boat under the old bridge.
We follow the river to the quiet garden beside the market.
The river carries a small boat through the city.
The river reflects the evening light under the stars.
The river leads the traveler to the old station.
By the river the city welcomes a new season.
By the window the traveler opens a book about the forest.
By the bridge a small cafe welcomes every visitor.
After the rain the garden fills with a little light.
After the concert the quiet street leads us to the station.
After the market the traveler follows the path by the river.
On the way to the station we share a new story.
On the bridge the morning breeze carries a little rain.
On the table a book waits beside a cup of tea.
At the station the city welcomes a new visitor.
At the market the warm bread waits in the small cafe.
At the window the evening light falls across a book.
At the door the traveler listens to the quiet street.
A new story begins in the small cafe after the rain.
A new journey follows the river through the green hills.
A new season brings warm light to the city.
The city welcomes the traveler with a little music.
The city wakes with the morning train and the scent of bread.
The city rests under the stars beside the quiet river.
The city changes with every new story in the market.
Under the trees the green path leads to the old library.
Under the bridge a small boat follows the quiet river.
Under the stars the evening breeze carries a new song.
The old bridge connects the market with the quiet garden.
The old station holds a little history for every visitor.
The old library opens its doors to the morning light.
The small cafe offers warm bread and a cup of tea.
The small boat carries a new visitor through the city.
The small garden reflects the quiet light after the rain.
The green hills welcome the morning train with a little mist.
The green garden grows beside the old library.
The green path leads through the forest to the small cafe.
The warm bread brings the traveler to the market.
The warm light fills the library after the morning rain.
The warm breeze carries the music through the city.
Every visitor finds a new story in the old library.
Every traveler follows a new path through the quiet city.
Every morning brings a little music to the garden.
We share a cup of tea by the window after the concert.
We share a new story in the garden under the stars.
$english$, 'Original English corpus authored for this project; one sentence per line.')
ON CONFLICT (locale, model_version) DO NOTHING;

INSERT INTO faker.text_corpora VALUES ('de_DE', 'sql-markov-v1', $german$
Am frühen Morgen fährt der Zug durch den grünen Wald.
Am frühen Abend fällt das Licht auf den alten Bahnhof.
Am Abend leuchten die Fenster in der kleinen Stadt.
Am Abend zieht der warme Wind durch den Park.
Am Abend beginnt eine neue Geschichte am alten Markt.
Die kleine Bäckerei öffnet ihre Türen am frühen Morgen.
Die kleine Bibliothek sammelt Geschichten aus der ganzen Stadt.
Die kleine Stadt begrüßt den Frühling mit einem Lächeln.
Die alte Brücke führt über den Fluss zum ruhigen Garten.
Die alte Bibliothek öffnet ihre Fenster für den warmen Wind.
Die alte Straße führt durch den Park zum kleinen Café.
Der kleine Garten duftet nach Regen und frischem Brot.
Der kleine Fluss trägt die Boote unter der alten Brücke.
Der kleine Bahnhof begrüßt die Reisenden mit einem Lächeln.
In der Stadt beginnt eine neue Geschichte mit einem Buch.
In der Bibliothek finden wir einen neuen Gedanken.
In der Bäckerei duftet das frische Brot nach einem guten Morgen.
In der Ferne leuchten die Fenster am alten Bahnhof.
Wir gehen durch den Park und hören die Vögel.
Wir gehen durch den Wald und entdecken einen neuen Weg.
Wir gehen durch den Regen zum kleinen Café.
Wir schauen über die Brücke auf den ruhigen Fluss.
Wir schauen über die Straße zum alten Markt.
Wir schauen über die Wiesen in die grüne Ferne.
Auf dem Markt beginnt der Morgen mit frischem Brot.
Auf dem Tisch wartet ein Buch neben einer Tasse Tee.
Auf dem Weg zum Bahnhof erzählen wir eine neue Geschichte.
Vor dem Fenster wächst der kleine Garten nach dem Regen.
Vor dem Theater treffen wir die Reisenden aus der Stadt.
Vor dem Bahnhof beginnt ein neuer Weg durch den Park.
Mit einem Buch beginnt eine Reise in die Ferne.
Mit einem Lächeln begrüßt die Bäckerin den frühen Morgen.
Mit einem Lied zieht der warme Wind durch die Stadt.
Wir finden einen neuen Weg unter den grünen Bäumen.
Wir finden einen neuen Gedanken in der kleinen Bibliothek.
Wir finden einen neuen Anfang am alten Bahnhof.
Die kleinen Boote folgen dem Fluss durch die Stadt.
Die kleinen Gärten leuchten im weichen Licht nach dem Regen.
Die kleinen Fenster spiegeln das Licht am frühen Abend.
Unter den Bäumen wartet eine Bank neben dem grünen Weg.
Unter den Sternen erzählt der Fluss eine leise Geschichte.
Unter den Wolken zieht der Zug durch den grünen Wald.
Die ruhige Straße führt zum kleinen Garten an der Brücke.
Die ruhige Musik begleitet die Reisenden durch den Abend.
Die ruhige Bibliothek schenkt jedem Besucher einen neuen Gedanken.
Der warme Wind trägt den Duft von Brot durch die Straße.
Der warme Duft führt uns zur kleinen Bäckerei am Markt.
Der warme Tee wartet neben einem Buch auf dem Tisch.
Das weiche Licht fällt durch die Fenster in den Garten.
Das weiche Gras wächst unter den Bäumen nach dem Regen.
Das weiche Brot liegt am frühen Morgen auf dem Tisch.
Im kleinen Garten erzählt die Bäckerin eine neue Geschichte.
Im kleinen Café teilen wir eine Tasse Tee nach dem Konzert.
Im kleinen Bahnhof wartet der Zug auf die Reisenden.
Am alten Bahnhof finden wir einen neuen Weg in die Stadt.
Am alten Markt duftet die Luft nach frischem Brot.
Am alten Fluss führt der grüne Weg unter die Brücke.
Der grüne Weg verbindet die kleine Bibliothek mit dem Markt.
Der grüne Wald begrüßt die Reisenden mit einem leisen Lied.
Der grüne Garten schenkt der Stadt einen ruhigen Ort.
$german$, 'Original German corpus authored for this project; one sentence per line.')
ON CONFLICT (locale, model_version) DO NOTHING;

CREATE OR REPLACE PROCEDURE faker.train_markov(
    p_locale text, p_model_version text DEFAULT 'sql-markov-v1'
)
LANGUAGE plpgsql AS $$
DECLARE
    source_text text;
BEGIN
    SELECT corpus INTO source_text FROM faker.text_corpora
    WHERE locale=p_locale AND model_version=p_model_version;
    IF source_text IS NULL THEN
        RAISE EXCEPTION 'Missing Markov training corpus' USING ERRCODE='22023';
    END IF;
    DELETE FROM faker.markov_transitions WHERE locale=p_locale AND model_version=p_model_version;
    INSERT INTO faker.markov_transitions
        (locale,model_version,previous_first,previous_second,next_token,weight)
    SELECT p_locale,p_model_version,
        CASE WHEN i>2 THEN words[i-2] ELSE '<s>' END,
        CASE WHEN i>1 THEN words[i-1] ELSE '<s>' END,
        words[i],count(*)::integer
    FROM (
        SELECT regexp_split_to_array(btrim(line), E'\\s+') AS words
        FROM regexp_split_to_table(source_text, E'\n') AS line
        WHERE btrim(line)<>''
    ) AS sentences
    CROSS JOIN LATERAL generate_subscripts(words,1) AS i
    GROUP BY 3,4,5;
END;
$$;

CREATE OR REPLACE PROCEDURE faker.markov_next(
    p_locale text, p_seed text, p_position bigint, p_step integer,
    p_previous_first text, p_previous_second text, p_model_version text,
    INOUT p_result text DEFAULT NULL
)
LANGUAGE plpgsql AS $$
DECLARE
    total_weight bigint;
    draw bigint;
    u double precision;
BEGIN
    IF p_step IS NULL OR p_step<1 THEN
        RAISE EXCEPTION 'Markov step must be positive' USING ERRCODE='22023';
    END IF;
    SELECT sum(weight) INTO total_weight FROM faker.markov_transitions
    WHERE locale=p_locale AND model_version=p_model_version
        AND previous_first=p_previous_first AND previous_second=p_previous_second;
    IF total_weight IS NULL THEN
        RAISE EXCEPTION 'Missing Markov state; train the locale first' USING ERRCODE='22023';
    END IF;
    CALL faker.uniform(p_locale,p_seed,p_position,
        'text.'||p_model_version||'.word.'||p_step::text,u);
    draw := floor(u*total_weight)::bigint+1;
    SELECT next_token INTO p_result FROM (
        SELECT next_token,sum(weight) OVER (ORDER BY next_token COLLATE "C") AS cumulative
        FROM faker.markov_transitions
        WHERE locale=p_locale AND model_version=p_model_version
            AND previous_first=p_previous_first AND previous_second=p_previous_second
    ) AS choices WHERE cumulative>=draw ORDER BY next_token COLLATE "C" LIMIT 1;
END;
$$;

CREATE OR REPLACE PROCEDURE faker.generate_text(
    p_locale text, p_seed text, p_position bigint, p_word_count integer,
    INOUT p_result jsonb DEFAULT NULL
)
LANGUAGE plpgsql AS $$
DECLARE
    first_word text := '<s>';
    second_word text := '<s>';
    word text;
    words text[] := ARRAY[]::text[];
    result_text text;
    model text := 'sql-markov-v1';
BEGIN
    IF p_position IS NULL OR p_position NOT BETWEEN 1 AND 1000000
       OR p_word_count IS NULL OR p_word_count NOT BETWEEN 10 AND 500 THEN
        RAISE EXCEPTION 'Text position must be 1..1000000 and word count 10..500' USING ERRCODE='22023';
    END IF;
    FOR step IN 1..p_word_count LOOP
        CALL faker.markov_next(p_locale,p_seed,p_position,step,first_word,second_word,model,word);
        words := array_append(words,word);
        IF word ~ '[.!?]$' THEN
            first_word := '<s>';
            second_word := '<s>';
        ELSE
            first_word := second_word;
            second_word := word;
        END IF;
    END LOOP;
    result_text := array_to_string(words,' ');
    IF result_text !~ '[.!?]$' THEN
        result_text := regexp_replace(result_text,'[,;:]+$','')||'.';
    END IF;
    p_result := jsonb_build_object('locale',p_locale,'seed',p_seed,'position',p_position,
        'word_count',p_word_count,'text',result_text,'model_version',model,'chain_order',2);
END;
$$;

CALL faker.train_markov('en_US');
CALL faker.train_markov('de_DE');
