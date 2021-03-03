# Implementačná dokumentácia k 2. úlohe do IPP 2019/2020

### Meno a priezvisko: Adam Múdry

### Login: xmudry01

## Interpret XML reprezentácie kódu - Implementácia

Program **interpret.py** príjma vstup (vstupný program) buď na STDIN po riadkoch (ak je aktívny prepínač ```--input=``` a ```--source=``` nie), alebo ho načíta zo súboru pomocou ```--source=``` prepínača a vstup do programu sa načíta zo STDIN alebo pomocou ```--input=```. Po spracovaní argumentov a načítaní dát sa spustí načítanie náveští, tokenizácia inštrukcií a ich následná interpretácia, kde sa poza jej behu dejú všetky potrebné kontroly. Celý interpret sa skladá spolu zo 4 tried, ktoré po sebe dedia a 1 trieda navyše pre tokeny.
Takúta hierarchia je použitá preto, aby sa jednotlivé časti mohli implementovať podľa logickej postupnosti:

Inicializácia potrebných štruktúr -> implementacia sémantiky a pomocných funkcií -> implementácia jendotlivých inštrukcií -> implementácia interpretu (tvorenie tokenov z načítaných inštrukcií a ich spúštanie).

To je implementované v triedach nasledovne:

- **Token**
- **Initialize**
- **Semantics_Tools(Initialize)**
- **Instructions(Semantics_Tools)**
- **Interpreter(Instructions)**

### Použitie

Na zobrazenie pomocnej hlášky spustíme program s ```--help``` prepínačom. Tj. ```interpret.py --help```.

Program spustíme nasledovne: ```python3 interpret.py --source=src.xml --input=in.txt```, kde ```src.xml``` je XML reprezentácia kódu a ```in.txt``` vstup pre daný interpretovaný program.

## Testovací rámec - Implementácia

Program **test.php** skenuje zložky podľa zadaných prepínačov, spúšťa nájdené testy a generuje HTML s výsledkami do STDOUT. Je možné ho spustiť v 3 režimoch, testovanie buď programu **parse.php**, **interpret.py** alebo oboch naraz.

Program je rozdelený na tieto funckie:

- **print_css()** - vypíše CSS do HTML
- **print_html_up()** - vypíše vrchnú časť HTML po body
- **print_html_down()** - vypíše spodnú časť HTML
- **print_body()** - vypisuje jendotlivé testy
- **print_recursive_scan()** - rekurzívne hľadá zložky

### Použitie

Na zobrazenie pomocnej hlášky spustíme program s ```--help``` prepínačom. Tj. ```test.php --help```.

Základné spustienie: ```php test.php```.

Program môžeme spúšťať s prepínačmi:
```--recursive```, ktorý z povoľuje rekurzívne hľadanie testov v podzložkách,

```--directory=```, ktorý z uvedenej cesty načíta testy,

```--parse-script=```, ktorý z uvedenej cesty načíta program **parse.php**,

```--int-script=```, ktorý z uvedenej cesty načíta program **interpret.py**,

predvolená hodnota pre tieto prepínače je cesta zložky, z ktorej program spúšťame.

```--parse-only```, ktorý testuje len program **parse.php** (vylučuje sa s ```--int-only``` a ```--int-script=```),

```--int-only```, ktorý testuje len program **interpret.py** (vylučuje sa s ```--parse-only``` a ```--parse-script=```),

predvolená hodnota pre tieto prepínače je testovanie oboch programov.

```--jexamxml=```, ktorý z uvedenej cesty načíta testy,

predvolená hodnota pre tento prepínač je cesta ```'/pub/courses/ipp/jexamxml/jexamxml.jar'```.