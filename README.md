# Diagnostic_Szakdoga

Egy Python 3.12-ben írt diagnosztikai program, amely soros port kommunikációt és grafikus felületet használ.

---

## Szükséges függőségek

| Csomag | Leírás | Link |
|--------|--------|------|
| **PySerial** | Soros port kommunikációhoz | [pypi.org/project/pyserial](https://pypi.org/project/pyserial/) |
| **Pygame** | Grafikus felülethez | [pypi.org/project/pygame](https://pypi.org/project/pygame/) |

Telepítés:
```bash
pip install pyserial pygame
```

---

## Ajánlott külső program – Virtuális COM port kapcsolathoz

**VSPE (Virtual Serial Ports Emulator)** – Free Trial  
🔗 [eterlogic.com/Products.VSPE.html](https://eterlogic.com/Products.VSPE.html)

---

## Indítási útmutató

### 1. lépés – VSPE elindítása

Indítsd el a **VSPE Free Trial** programot. Az alábbi főképernyő fogad:

![VSPE főképernyő](https://github.com/user-attachments/assets/d667f3f2-9a17-45a1-96d0-b6de0939e28a)

---

### 2. lépés – Új eszköz létrehozása

Kattints a **piros kerettel jelzett ikonra** az eszköztáron:

![Új eszköz ikon](https://github.com/user-attachments/assets/4d3c6ec1-3ac4-4a77-81a9-f0f14952ac74)

---

### 3. lépés – Virtual Pair kiválasztása

A megjelenő ablakban a legördülő listából válaszd a **„Virtual Pair"** opciót, majd kattints a **Next** gombra:

![Virtual Pair választó](https://github.com/user-attachments/assets/a5b36e2b-51c9-4a59-ae44-6a4beebb2ad4)

---

### 4. lépés – COM portok beállítása

A következő ablakban válaszd ki a két virtuális COM portot:
- **Első port:** `COM7`
- **Második port:** `COM8`

![COM port választó](https://github.com/user-attachments/assets/f7cfdcca-59de-40b2-82a6-458adb01c4f8)

Majd kattints a **Finish** gombra.

---

### 5. lépés – Szimuláció indítása

A létrehozás után az alábbi sort látod az eszközlistában:

![Eszközlista](https://github.com/user-attachments/assets/78bde9df-ef46-407c-b2ee-81ebfac749ff)

A **zöld ikon** segítségével indítsd el a COM-COM port szimulációt:

![Start gomb](https://github.com/user-attachments/assets/870e0190-e3b2-4fd8-a689-651542b65a75)

---

### 6. lépés – Program elindítása

Miután a VSPE szimuláció fut, indítsd el az autó szimulácíót:

```bash
python Dashboard.py
```

illetve a DiagApp programot:

```bash
python DiagApp.py
```


---

## Megjegyzések

- A program **COM7** és **COM8** portokon kommunikál alapértelmezetten.
- Győződj meg róla, hogy a VSPE szimuláció **fut**, mielőtt elindítod a Python programot.
- Python **3.12** verzió szükséges.

#Technikai adatok

Program müködése
--- 
Fő file melyben a fő cikus található a Dashboard.py

Ez felel a aútó műszerfal kirajzolásáért modulok példányositásáért kontroller inicializálásáért kontroller gombok beállitásáért modulok által számolt adatok megjelenitésért a kitrajzolt műszerfalon
"menű" gomb a gyujtás ki be kapcsolásáért felel gyujtás bekapcsolása után a modulok meghivodnak "elkezdődik a kommunikácíó" "áramot kapnak a modulok" az autóban ezek az adatok a kontrollertől kapott inputok alapján modusolnak melyeket valós OBD2 szabvány szerint offsetelnek modositanak majd ezek hexadecimális formában tovább küldödnek a CanController osztály példányaiba egy modul több adat csomagot is más újra küldési frekvencián is át küld a cancontrollernek (erről később).
A gyujtás állapotba valóság hűen olyan adatok olvashatóak melyek elérhetőek motor járása nélkül pl gáz/fék pedál állása, hőmérsékletek, tárolt hibakódók, sebességfokozat, egyéb inputok

Az A gombbal a motor elinditható ilyenkor kezdenek olyan adatok is kiküldésre kerülni melyek csak a motor illetve az autó járásától valóság hűen olvashatok pl fordulat szám

y gomb a DTC hibák random generálása ezek létrehozása jobb fgelűl jelzésre kerülnek piros kiirással

x gomb a DTC hibák törlése Autón belül

# DME modul
lényegében egy valós BMW motorvezérlőjének szimulálása nyilvános dokumentumból kiszedett valamennyi motorvezérlőhöz köthető szenzor/érték modosulásra kerül a felhasználó által megadott inputok alapján ezek az értékek valóság hű formájában modosulnak ezek szintén a műszerfal igényei szerint jelennek meg, valamint a modulon belül történik a szabvány szerinti offsetelés és kerülnek bele3 a data csomagokba valós can/modul ID beosztás szerint (ID és a fent emlitett ismételt kiküldés gyorsasága valós can frame prioritás, adat fontoság alapján kerül meghivásra a cancontroller) kap egy obd2 szabvány kód szerinti illwetve "gyártó" által meghatározott DTC hiba kódót és jelentést. A motor nyomaték görbéje szintén egy nyilvános grafikonból kivett adat bizonyos pontok kivételével van megadva a motor teljesitménye egy listában amely arányositva van a köztes fordulat számok között

#DSC modul
A DTC modulhoz köthető szenzorok érttékeit modositjuk valóság hűen szintén ugyanaz az eljárás mint a DME modul esetében. ennek a modulnak bizonyos értékeit már más modulok állapotának figyelembe vételével modositunk

#EPS modul
A EPS kormányzáshoz fűzhetűő inpőutok alapján valósság hű adatokat modositunk ez DME, DSC modulok értékeit felhasználva bizosit adat modositást. folyamat hasonlo valósághűen  olyan értékek amelyknek számitását befolyásolja más modulok értékei azokat átvéve modosit

A többi modul is ez elv alapján müködik











