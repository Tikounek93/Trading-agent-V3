# Module: knowledge_processing

## Ucel modulu

Modul prevadi jiz ziskane titulky nebo transcripty na dohledatelne, strukturovane a pouze poradenske znalostni artefakty. Neziskava zdroje, nestavi strategii, neschvaluje strategii a neobchoduje.

## Funkcni zadani modulu

Status zadani: `stable_v1`

Schvaleni clovekem: `confirmed_for_v1`

Verze modulu: `1.0.0`.

## Stav oproti zadani

Status: `stable`

Modul umi zpracovat jeden zdroj i vsechny pripravene zdroje z katalogu, pripojit volitelne frame a OCR podklady, vytvorit znalostni jednotky, overit jejich kvalitu a ulozit aktualni vystup i historii. Opakovane zpracovani stejneho vstupu je idempotentni.

## Hlavni odpovednosti

- Vytvorit casovou osu a semanticke chunky.
- Zachovat puvod zdroje, casove vazby a vazby jednotek na chunky.
- Vyhledat udalosti, koncepty, faze setupu a poradenske relevance skore.
- Overit povinna pole, poradi casu, provenance a hranici proti exekucni autorite.
- Ulozit JSON projekci a append-only historii.

## Vstupy

- Zdrojovy identifikator a lokalni VTT subtitle nebo transcript.
- Metadata zdroje z katalogu.
- Volitelny seznam frame indexu.
- Volitelne OCR zaznamy s casovym udajem.
- SourceCatalog a koren promovanych source artifacts pro katalogovy workflow.

## Vystupy

- Canonical timeline se segmenty, transcript textem, frame cestami, OCR zaznamy a udalostmi.
- Semanticke chunky s tematickym obohacenim.
- Dohledatelne knowledge units s koncepty, setup stages, score a duvody skore.
- Quality report.
- Aktualni knowledge JSON a timestampovana historie pro kazdy zdroj.
- Stav processed, already_current, blocked nebo failed pri davkovem behu.

## Hlavni tok zpracovani

Katalog vybere pripraveny zdroj. Workflow najde dostupny subtitle nebo transcript, nacte metadata a volitelne sidecary. Pipeline vytvori timeline, priradi multimodalni evidence, extrahuje udalosti, sestavi chunky a knowledge units, prida advisory score, overi vystup a ulozi jej. Chybejici transcript zdroj zablokuje bez vytvoreni nekompletniho vystupu.

## Zavislosti

Modul cte verejne kontrakty source_intake pro zdroje a artefakty a data_platform pro SourceCatalog. Nezapisuje do zdrojovych artefaktu ani do katalogu. Vystup je urcen jako vstup pro budoucí strategy blueprint, ne jako obchodni rozhodnuti.

## Testy

- modules/knowledge_processing/tests/test_pipeline.py
- modules/knowledge_processing/tests/test_v1_workflow.py

## Datove kontrakty

Verejne tvary jsou timeline, knowledge artifact, knowledge storage receipt a quality validation report. Knowledge artifact musi obsahovat source_id, append_only true, raw_data_modified false, timeline, chunks a knowledge_units. Knowledge units musi zachovat source_chunk_id a poradenske score. Zakazane jsou pole nebo autorita pro schvaleni, exekuci, brokera nebo aktivaci strategie.

## Rizika a slaba mista

- Pipeline je v1 deterministicka a text-first; produkce videoframu a OCR patri do nahraditelnych zdrojovych nastroju.
- Kvalita vysledku zavisi na kvalite titulku, OCR a metadat.
- Modul pripravuje podklady, ale nevytvari blueprint ani neupravuje strategii.

## Otevrene otazky

- Ktere embeddingy a vektorove uloziste pozdeji pouzijeme pro hlubsi analyzu objektu.
- Ktere dalsi typy dokumentu budou mit stabilni parser vedle VTT.
- Ktera pole z knowledge artifact se stanou stabilnim kontraktem pro strategy blueprint.

## Zdrojove soubory

- modules/knowledge_processing/contracts/knowledge.py
- modules/knowledge_processing/module_metadata.py
- modules/knowledge_processing/storage/knowledge_artifact_store.py
- modules/knowledge_processing/tools/
- modules/knowledge_processing/workflows/
- modules/knowledge_processing/tests/
