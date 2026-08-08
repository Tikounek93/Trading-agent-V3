# Module: frontend

## Ucel modulu

Frontend je lokalni operator workspace pro moduly v3. Poskytuje jeden webovy
App Shell s navigaci, prehledem stavu a pracovnimi obrazovkami pro Source
Intake a Knowledge Processing.

## Funkcni zadani modulu

Status zadani: `candidate_v0_3`

Schvaleni clovekem: `confirmed_for_current_iteration`

Verze modulu: `0.3.0`.

## Stav oproti zadani

Status: `candidate`

Frontend umi zobrazit stav katalogu, ovladat acquisition, spustit zpracovani
knowledge, prohlizet timeline, chunky a knowledge units a zapisovat oddelenou
append-only korekcni vrstvu. Budouci strategicke a trading obrazovky jsou
zatim pouze navigacni placeholdery.

## Hlavni odpovednosti

- Poskytnout navigaci mezi aktivnimi a planovanymi castmi systemu.
- Komponovat verejne workflow source_intake, data_platform a knowledge_processing.
- Zobrazit stav zdroju, artefaktu, processingu a historie vystupu.
- Umoznit operatorovi prohlizet a korigovat znalostni podklady bez prepisu originalu.

## Vstupy

- SourceCatalog, source artifacts a knowledge artifacts.
- Operator formulare pro URL, lokalni soubor, spusteni processingu a korekci.
- Stavove vysledky workflow a validacni informace.

## Vystupy

- Lokalni HTTP UI a JSON API pro operator workspace.
- Append-only correction record v knowledge_processing.
- Operator stavove zpravy a zobrazeni modulu.

## Hlavni tok zpracovani

App Shell nacte stav aplikace. Operator prejde do Source Intake nebo Knowledge
Processing. Vybere zdroj, nacte jeho artefakt, prohlizi timeline, chunky nebo
knowledge units a muze ulozit korekci s cilem, polem, hodnotou a duvodem.
Korekce se zapisuje mimo vygenerovany artefakt.

## Zavislosti

Frontend pouziva source_intake pro acquisition, data_platform pro katalog a
ulozene artefakty a knowledge_processing pro zpracovani, cteni artefaktu a
korekce. Neobsahuje obchodni nebo strategickou logiku.

## Testy

- modules/frontend/tests/test_source_intake_app.py

## Datove kontrakty

Frontend poskytuje status a knowledge workspace API. Verejne operace zahrnuji
stav aplikace, nacteni knowledge artefaktu, spusteni knowledge processingu a
zapis korekce. Korekce musi obsahovat source_id, target_type, target_id, field,
corrected_value a reason.

## Rizika a slaba mista

- Standard-library HTTP server je lokalni vyvojovy zaklad, ne produkcni gateway.
- Velke knowledge artefakty se nyni nacitaji jako JSON projekce.
- Budouci moduly potrebuji vlastni obrazovky a stabilni UI kontrakty.

## Otevrene otazky

- Kdy se frontend presune na samostatny webovy runtime.
- Ktera prava budou potreba pro vice operatoru.
- Jak se budou zobrazovat a schvalovat dalsi verze strategie.

## Zdrojove soubory

- modules/frontend/source_intake_app.py
- modules/frontend/static/index.html
- modules/frontend/static/app.js
- modules/frontend/static/styles.css
- modules/frontend/module_metadata.py
