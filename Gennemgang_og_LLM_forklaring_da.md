# Gennemgang af DataQuality.ipynb

Gennemført 20. oktober 2026. Kilden er `C:\GIT_Private\Medium--DataQuality\DataQuality.ipynb`. Den reviderede kopi hedder `DataQuality_gennemgaaet.ipynb`. Originalen og databasen er ikke ændret.

## Dine kommentarer er besvaret i notebooken

- Original celle 29: Quantity-boxplottet er forklaret med de faktiske kvartiler og forskellen fra histogrammet.
- Original celle 35: FD-figuren er forklaret med tæller, nævner, andel og begrænsninger.
- Original celle 38: LLM-afsnittet har fået en ny overskrift og er delt op i mindre trin med grundige danske forklaringer før koden.

Artikelteksten før LLM-afsnittet er forbedret på engelsk, så den passer til den eksisterende artikel. De danske forklaringer kan senere omskrives til artikeltekst, når selve metoden og resultaterne er på plads.

## De vigtigste fund

### 1. Quantity: mange boxplot-outliers er forventelige uden at være fejl

Q1=2, Q3=8, IQR=6 og grænserne er −7 og 17. Quantity over 17 tegnes derfor som outlier, selv om den kan være en korrekt stor ordre. Generatoren bruger en højreskæv lognormalfordeling. Med de samme grænser findes 4,225 flag allerede i de rene ordrelinjer og 4,845 i de korrumperede. Den sidste tæller er ikke antallet af indsprøjtede fejl.

Det nuværende histogram udelader ikke ekstremerne. Det dækker −10.000 til 64.000 med 50 bins, altså ca. 1.480 pr. bin. Næsten alle almindelige mængder ligger i samme bin. Histogrammet og boxplottet summerer data på to forskellige måder. Jeg har bevaret begge og tilføjet numeriske IQR-tællinger samt kode til et supplerende zoom med eksplicit opgørelse af det, som ligger uden for vinduet. Zoomkoden er syntakskontrolleret, men ikke renderet her.

Der er 326 negative quantities. 1 række(r) rammes af både den negative korruption og multiplikationen. Det forklarer minimum −10.000. Gennemsnittet er ca. 40.56, mens medianen fortsat er 5. Mål derfor ikke kun mean/std, og segmentér efter enhed og materiale ved operationel fortolkning.

### 2. Rabat: boxplottet markerer et legitimt niveau

Discount har Q1=0 og Q3=5, så øvre fence er 12,5. Alle 2.622 rækker med 15 % rabat bliver fliers. Men 15 % er udtrykkeligt med i ERP-generatorens tilladte valg. Her kan man derfor ikke bruge en boxplotmarkering som en fejllabel. De diskrete frekvenser er mere informative end et histogram med mange tomme bins.

Clean/corrupt-rabatfordelingerne er næsten ens, som forventet: der er ikke indsat rabatfejl i ERP-delen. Demoen har derimod en anden generator og en rabatfejl på 150. De to forsøg må ikke blandes sammen. Den aktuelle range-evaluator understøtter intervalkontrol, men ikke en liste over tilladte rabatniveauer.

### 3. FD: 0,495 % er en andel af nøgler

25 af 5.050 kundenøgler har konflikt: 0,49505 %. De pågældende grupper indeholder 50 records. Det er hverken 25 forkerte celler i en komplet kvalitetsmåling eller 0,495 % af alle records. Kontrollen markerer konfliktgrupper, ikke hvilken af navnene der er korrekt.

Materialernes tre FD-kontroller har nul konflikter, men hver materialenøgle forekommer kun én gang. De består dermed automatisk; det beviser ikke, at beskrivelser, grupper og priser er korrekte. Der mangler stadig 20 materialebeskrivelser. Entity duplicates med nye kundenøgler fanges ikke af customer_id → customer_name.

### 4. Dubletter og labels

Der vises 25 ekstra eksakte kundedubletter og 324 ekstra eksakte ordrelinjedubletter. 325 ordrelinjer blev oprindeligt kopieret; efterfølgende ændringer bryder et af de eksakte match. Det er efterprøvet på det aktuelle databaseudtræk og med samme corruptor-kald.

`duplicated()` markerer kopier efter første forekomst. `duplicated(keep=False)` markerer hele gruppen. Nøglekollisioner og gentagne forretningsentiteter kræver egne kontroller og egne labels. Corruptor-loggen kan ikke uden videre bruges til ERP-præcision/recall: kildeindeks er ikke entydige nye record-id'er, og tabelfelt mangler i mange events.

### 5. FK og frekvens

Alle fire konfigurerede FK-relationer viser nul ugyldige referencer. Der er heller ikke indsprøjtet FK-fejl i ERP-forsøget, så resultatet fortæller ikke om recall. Missing keys og unikke parent keys kræver separate kontroller, og inventory-relationen er ikke med i listen.

Materialegruppernes fordeling fra 14,20 % til 28,95 % er en beskrivelse af datasammensætningen. Det er ikke tidsdrift, og forskellene er ikke automatisk datakvalitetsproblemer. At alle materialer er EUR er tilsigtet i generatoren. Kreditgrænser på kunder bør ikke sammenlignes som finansielle beløb på tværs af valutaer uden en dokumenteret omregning.

## LLM-delen forklaret samlet

Tænk på LLM'en som en assistent, der foreslår kontrollister. Profilen er et resumé af, hvad data indeholder. Kontrakten beskriver, hvad virksomheden kræver. JSON-skemaet beskriver, hvordan en regel skal skrives. Validatoren kontrollerer, at forslaget kan læses og henviser til eksisterende felter. En faglig gennemgang afgør, om reglen er rimelig. Evaluatoren anvender de valgte regler på records. Ground truth bruges bagefter til at måle rigtige og forkerte fund.

De trin er nu adskilt i notebooken:

1. Lav de små demotabeller og profilér kolonnerne.
2. Definér det understøttede regelsprog (`not_null`, `range`, `unique`, `foreign_key`).
3. Kontrollér den foreslåede regelstruktur og kolonnereferencer.
4. Send profiler og kontrakt til lokal Ollama og læs JSON-svaret.
5. Vis en eksplicit status, så »ikke kørt« og »ingen regler fra modellen« ikke forveksles.
6. Opret de håndskrevne demo-regler og anvend dem deterministisk.
7. Indsprøjt fire kendte fejl i et separat testudtræk og sammenlign cellefund med labels.
8. Sammenlign fordelinger på tværs af snapshots og adskil drift fra kendte fejl.
9. Vis, hvordan den samme profilfunktion kan anvendes på de rene ERP-tabeller uden at blande demo-regler og ERP-data.

### Hvad viser resultaterne faktisk?

Baselinen finder to af fire fejl. Den håndskrevne udvidelse finder fire af fire. Begge har nul falske positiver i det lille kontrollerede eksempel. Det er en funktionstest med én fejl pr. type. Den viser ikke, at en sprogmodel er bedre end traditionelle regler.

Originalens output `[]` ved modelkaldet fortæller alene ikke, om kaldet blev sprunget over eller modellen foreslog nul regler. Koden gør nu denne forskel eksplicit. I denne gennemgang er modellen ikke kaldt. Evalueringskoden anvender `demo_rules`, og `candidate_rules` bruges ikke i scorerne. Der mangler derfor stadig et faktisk LLM-forsøg for at besvare artiklens titel empirisk.

### Hvad bør næste faktiske LLM-forsøg indeholde?

Bevar et urørt testudtræk og separate labels. Generér forslag på udviklingsdata. Gennemgå hvert forslag mod domænekrav og kendt gyldige edge cases. Frys regelsættet før evalueringen. Sammenlign baseline med baseline plus godkendte modelregler på præcis samme testdata. Opgør ekstra korrekte fund, ekstra falske positiver, afviste regler og tidsforbrug. Gentag på flere seeds og fejlprocenter. For dubletter og FD skal måleenheden være dokumenteret som par, gruppe eller række, ikke stiltiende blandet med cellefejl.

## Hvad er kontrolleret, og hvad er ikke?

- Alle seks gemte figurer er åbnet og visuelt gennemgået.
- Notebookens kode, kommentarer og gemte tekstoutputs er læst.
- Corruptor, generatorens relevante antagelser og databaseadgangen er undersøgt.
- De centrale ERP-tal er genskabt i hukommelsen med SQLite `mode=ro`. Generatoren blev ikke kørt, og databasen blev ikke erstattet.
- De nye IQR-tællinger samt den opsplittede selvstændige demo er kørt med assertions, inklusive ugyldige regler, parsefejl, infinity og tomme tabeller.
- Alle kodeceller er syntakskontrolleret.
- Den ekstra zoomfigur er ikke renderet: det tilgængelige Python-miljø mangler Matplotlib. De originale plotoutputs er bevaret.
- Der er ikke foretaget et nyt Ollama-kald. Ingen modelresultater er opfundet.

## Kilder til værktøjernes adfærd

- [Matplotlib: boxplot og standarden whis=1.5](https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.boxplot.html)
- [Ollama: structured outputs og JSON Schema](https://docs.ollama.com/capabilities/structured-outputs)

De konkrete tal og forretningsmæssige begrænsninger ovenfor stammer fra din notebook, kildekode og det lokale databaseudtræk, ikke fra dokumentationssiderne.
