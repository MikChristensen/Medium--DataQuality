1. Deep Learning approaches

Hvad kan de?

Lære latente repræsentationer af data og dermed mønstre, som ikke er eksplicit defineret.
Identificere og korrigere fejl gennem lærte datamønstre.
Trænes på constraint-compliant subsets og bruge disse som reference for gode data.
Bruge self-supervised learning, så behovet for manuelt labellede data reduceres.
Bruge active learning, hvor modellen gradvist forbedres gennem feedback på de mest informative observationer.

Begrænsninger

Kan være afhængige af clean labels eller stabile constraints.
Har problemer med meget støjfyldte tabeller.
Kan blive beregningsmæssigt dyre på store datasæt.
Det kan være vanskeligt at forklare, hvorfor en observation betragtes som dårlig.
2. Rule-based Data Quality

Eksempler kunne være:

price > 0
product_id IS UNIQUE
category IS NOT NULL
order_date <= current_date

Hvad kan de?

Kontrollere kendte business rules.
Kontrollere datatyper, ranges og constraints.
Finde manglende værdier.
Finde duplicates.
Kontrollere relationer mellem kolonner.
Give deterministiske og reproducerbare resultater.
Er typisk relativt billige at køre.

Begrænsninger

Reglerne skal normalt defineres på forhånd.
Finder primært problemer, som udvikleren allerede har tænkt på.
Har begrænset forståelse af kontekst og betydning.
Kan derfor overse semantiske inkonsistenser.

Det sidste er vigtigt for vores artikel.

3. Statistical / Frequency-based approaches

Selvom udsnittet ikke går særlig dybt ned i dem, synes jeg bestemt, vi skal have dem som en separat kategori.

Hvad kan de?

Lære hvordan et datasæt normalt er fordelt.
Identificere outliers.
Identificere sjældne værdier.
Måle ændringer i kategorifrekvenser.
Opdage distribution drift.
Sammenligne nye batches med en historisk baseline.
Finde problemer uden at kende alle fejltyper på forhånd.

Eksempel:

Baseline:

Camera      32%
Audio       27%
Lighting    23%
Rigging     18%

New batch:

Camera      31%
Audio        6%   ← anomaly
Lighting    24%
Rigging     39%   ← anomaly

Begrænsninger

En statistisk anomaly er ikke nødvendigvis en fejl.
Kan ikke nødvendigvis forstå hvorfor noget er mærkeligt.
Har begrænset semantisk forståelse.

Det er netop dér, hvor LLM'en potentielt kan supplere den.

4. LLM-based Data Quality

Det er den nye komponent.

Hvad kan de potentielt?

Vurdere contextual correctness.
Opdage semantiske inkonsistenser.
Analysere relationer mellem flere tekst-/kategorifelter.
Bruge domæneviden til at vurdere plausibilitet.
Forklare hvorfor en observation virker mistænkelig.
Finde problemer, der ikke kan beskrives nemt med traditionelle constraints.

Tag fx:

Product: Sony FX6
Category: Power Tools
Price/day: €180

Det kan sagtens bestå:

product != NULL        ✓
category != NULL       ✓
price > 0              ✓

Det kan også være, at €180 ikke er en statistisk outlier.

Men semantisk er:

Sony FX6 → Power Tools

forkert.

Det er præcis den type problem, som teksten beskriver, når den siger, at LLM'er potentielt kan identificere anomalier, som traditionelle functional-dependency-regler overser.

Begrænsninger

Ikke-deterministiske resultater.
Risiko for hallucinationer eller fejlagtige vurderinger.
Afhænger af prompt og kontekst.
Dyrere end simple rules/statistics.
Vanskeligere at validere.
Derfor bør en LLM-evaluering ikke automatisk behandles som ground truth.
Og så får vi faktisk et rigtig godt framework til artiklen

Jeg ville visualisere vores argument omtrent sådan:

Method	Rules	Patterns	Anomalies	Semantics	Explain
Rule-based	✓	–	Limited	–	✓
Statistical/Frequency	–	✓	✓	–	Limited
Deep Learning	–	✓	✓	Limited	–
LLM	Limited	✓	✓	✓	✓

Vi skal være lidt forsigtige med tabellen, fordi de præcise egenskaber afhænger af implementeringen. Men som conceptual framework er den interessant.