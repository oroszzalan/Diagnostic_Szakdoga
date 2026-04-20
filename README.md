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

# BMW F90 M5 — CAN Bus Szimuláció és OBD2 Diagnosztikai Rendszer

> **Szakdolgozat projekt** — Miskolci Egyetem, Gépészmérnöki és Informatikai Kar  
> Programtervező informatikus szak

Egy szoftveres rendszer, amely egy **BMW F90 M5** gépjármű fedélzeti elektronikájának CAN bus kommunikációját szimulálja. A szimuláció valós idejű adatokat generál egy játékvezérlő bemenetei alapján, ezeket OBD2 szabvány szerint kódolja és CAN keretként virtuális soros porton keresztül továbbítja egy diagnosztikai alkalmazás felé — mindezt valós hardver nélkül.

---

## Tartalomjegyzék

- [A rendszer felépítése](#a-rendszer-felépítése)
- [Fájlok és modulok](#fájlok-és-modulok)
- [Program működése részletesen](#program-működése-részletesen)
  - [Dashboard.py — Főciklus](#dashboardpy--főciklus)
  - [DME modul](#dme-modul--digital-motor-electronics)
  - [DSC modul](#dsc-modul--dynamic-stability-control)
  - [EGS modul](#egs-modul--elektronisches-getriebe-steuergerät)
  - [EPS modul](#eps-modul--electric-power-steering)
  - [DTCManager](#dtcmanager--hibakód-kezelés)
  - [CanController](#cancontroller--can-keretkódoló)
  - [OBD2Gateway](#obd2gateway--soros-kommunikáció)
  - [DiagApp](#diagapp--diagnosztikai-alkalmazás)
- [CAN frame azonosítók](#can-frame-azonosítók)
- [DTC hibakódok](#dtc-hibakódok)
- [Telepítés és futtatás](#telepítés-és-futtatás)
- [Vezérlők](#vezérlők)

---

## A rendszer felépítése

```
┌─────────────────────────────────────────────────────────────┐
│                    Dashboard.py (főciklus)                  │
│   Pygame grafikus műszerfal · Kontroller input olvasás      │
└────────┬───────────┬───────────┬───────────────────────────┘
         │           │           │
    ┌────▼───┐  ┌────▼───┐  ┌───▼────┐  ┌─────────┐
    │  DME   │  │  DSC   │  │  EGS   │  │   EPS   │
    │ modul  │  │ modul  │  │ modul  │  │  modul  │
    └────┬───┘  └────┬───┘  └───┬────┘  └────┬────┘
         │           │          │             │
         └───────────┴──────────┴─────────────┘
                          │
                  ┌───────▼────────┐
                  │  CanController │  (bit stuffing, CRC-15)
                  └───────┬────────┘
                          │  CAN bitsorozat
                  ┌───────▼────────┐
                  │  OBD2Gateway   │  (soros port, threading)
                  └───────┬────────┘
                          │  Virtuális COM port
                  ┌───────▼────────┐
                  │    DiagApp     │  (Tkinter GUI, dekódolás)
                  └────────────────┘
```

A rendszer három rétegre bontható:

| Réteg | Komponensek | Feladat |
|---|---|---|
| **Szimulációs** | DME, DSC, EGS, EPS | Valós idejű járműparaméter-számítás |
| **Kommunikációs** | CanController, OBD2Gateway | CAN keret kódolás + soros átvitel |
| **Diagnosztikai** | DiagApp, DiagReceiverThread | Fogadás, dekódolás, megjelenítés |

---

## Fájlok és modulok

```
├── Dashboard.py          # Főciklus, Pygame műszerfal, kontroller kezelés
├── DMEModule.py          # Motor vezérlőegység szimuláció
├── DSCModule.py          # Dinamikus stabilitásvezérlés szimuláció
├── EGSModule.py          # Automata váltó szimuláció
├── EPSModule.py          # Elektromos szervokormány szimuláció
├── DTCManager.py         # Hibakód-kezelés alaposztály (örököltetett)
├── DTC_Database.py       # OBD2 DTC hibakód adatbázis (200+ kód)
├── CanController.py      # CAN keret kódoló (bit stuffing, CRC-15)
├── OBD2.py               # Gateway soros kommunikációs szál
├── DiagApp.py            # Tkinter diagnosztikai alkalmazás
├── HexInt.py             # Hexadecimális megjelenítés segédosztály
├── dtc_dme.json          # DME tárolt DTC kódok (perzisztens)
├── dtc_dsc.json          # DSC tárolt DTC kódok (perzisztens)
├── dtc_egs.json          # EGS tárolt DTC kódok (perzisztens)
└── dtc_eps.json          # EPS tárolt DTC kódok (perzisztens)
```

---

## Program működése részletesen

### Dashboard.py — Főciklus

A `Dashboard.py` a rendszer belépési pontja és egyben a grafikus műszerfal megvalósítója. Pygame könyvtár segítségével 60 fps-es valós idejű renderelést végez.

**Feladatai:**
- A négy szimulációs modul (DME, DSC, EGS, EPS) példányosítása és összekapcsolása
- Az OBD2Gateway elindítása háttérszálként
- A játékvezérlő (gamepad) inicializálása és bemenetének olvasása
- A modulok szimulációs ciklusának meghívása minden képkockában
- A kiszámított adatok megjelenítése a grafikus műszerfalon

**Grafikus elemek:**
- Analóg sebességmérő (0–330 km/h)
- Analóg fordulatszámmérő (0–8000 rpm, piros figyelmeztető zóna 6500 rpm felett)
- Hőmérő és üzemanyagszint kisgauge ívelt skálával
- Középső panel: aktuális fokozat, kormányszög-csík, nyomaték/teljesítmény értékek
- Figyelmeztető jelzőfények: `ABS`, `TC`, `DSC`, `CHECK ENGINE` — villogó animációval
- DTC számláló a jobb felső sarokban (aktív/tárolt különbséggel)
- Állapotsor: gyújtás/motor státusz, sebesség, hűtővíz hőmérséklet, óra

**Gyújtás és motorállapot kezelése:**

A `menu` gomb a gyújtást kapcsolja be/ki. Valóság hűen a gyújtás bekapcsolásakor a modulok „áramot kapnak", a szimulációs ciklus elindul, az OBD2Gateway elindítja a CAN adatfolyamot a soros porton. Gyújtás bekapcsolt állapotban, de motor nélkül is olvasható adatok érhetők el: gáz/fékpedál állása, hőmérsékletek, tárolt hibakódok, fokozatválasztó állása — ahogy egy valós autóban is.

Az `A` gomb a motort indítja/állítja le. Motor járása esetén az RPM, nyomaték, teljesítmény, O2 szenzor és egyéb motor-specifikus értékek is elkezdődnek módosulni és kiadásra kerülni a CAN buszra.

```
Gyújtás OFF  →  Gyújtás ON  →  Motor ON
     │               │               │
  Minden OFF    Statikus adatok   Összes adat
                (pedálok, hőmér-  (RPM, nyomaték,
                séklet, DTC-k)    O2, MAF, stb.)
```

---

### DME modul — Digital Motor Electronics

A DME modul egy valós BMW motorvezérlő szoftveres szimulációja. Nyilvánosan elérhető műszaki dokumentációk alapján a motorvezérlőhöz köthető összes szenzorérték módosul a felhasználói inputok (gáz, fékezés, RPM) alapján, valóság hű fizikai modelleken keresztül.

**Szimulált értékek:**

| Érték | Leírás | Tartomány |
|---|---|---|
| `rpm` | Motorfordulatszám | 0–6700 rpm |
| `throttlePosition` | Fojtószelep pozíció | 0–100% |
| `coolantTemp` | Hűtővíz hőmérséklet | 40–170°C |
| `oilTemp` | Olajhőmérséklet | 5–120°C |
| `oilPressure` | Olajnyomás | 0–5 bar |
| `batteryVoltage` | Akkufeszültség | 12.0 / 13.8 V |
| `massAirflow` | Légtömegáram | g/s |
| `knockSensor` | Kopogásérzékelő | 0–10 |
| `O2sensor` | Lambda szonda feszültség | 0–1.2 V |
| `Torque` | Motor nyomaték | 0–750 Nm |
| `HorsePower` | Teljesítmény | 0–625 LE |
| `fuelLevelLiters` | Üzemanyagszint | 0–67 liter |

**Nyomatékmodell:**

A motor nyomatéka szakaszos lineáris interpolációval kerül számításra, amelynek alappontjai egy nyilvánosan elérhető S63 motor nyomatékgörbe adatai:

```
RPM:      700  1000  1500  1800  2500  3500  4500  5500  6000  6500  6700
Nyomaték: 100   300   550   750   750   750   750   750   720   650   550  [Nm]
```

A köztes fordulatszámok értékei a szomszédos pontok között lineárisan interpolálódnak. A tényleges nyomaték a fojtószelep pozíciójával arányos:

```
T = T_idle + (T_max - T_idle) × throttle
P [LE] = (Nyomaték [Nm] × RPM) / 7127
```

**OBD2 kódolás és CAN küldés:**

A szimulált értékek OBD2 szabvány szerinti offseteléssel és skálázással kerülnek a CAN adatcsomagokba. Például a hűtővíz hőmérséklet: `byte = coolantTemp + 40` (OBD2 PID 0x05 szabvány). A DME **5 különböző CAN keretet** küld eltérő frekvenciával, valós BMW CAN frame prioritás alapján:

| CAN ID | Frekvencia | Tartalom |
|---|---|---|
| `0x0A0` | 50 Hz (20 ms) | RPM, fojtószelep, légtömegáram |
| `0x0A3` | 20 Hz (50 ms) | O2 szenzor, kopogásérzékelő |
| `0x0A1` | 10 Hz (100 ms) | Hőmérsékletek |
| `0x0A4` | 50 Hz (20 ms) | Nyomaték, teljesítmény |
| `0x0A2` | 5 Hz (200 ms) | Akkufeszültség, olajnyomás |

Az eltérő küldési frekvencia valós CAN rendszerekben is így működik: a kritikus, gyorsan változó adatokat (RPM) magasabb prioritással és sűrűbben küldi a vezérlőegység.

---

### DSC modul — Dynamic Stability Control

A DSC modul szimulációja a stabilitásvezérlő rendszer valóság hű modellje. Más modulok állapotait (DME fojtószelep, EPS kormányszög, EGS sebesség) felhasználva számítja ki az értékeit.

**Szimulált értékek:**

| Érték | Leírás |
|---|---|
| `vehicle_speed` | Jármű sebesség (km/h) — EGS kimeneti fordulatból számítva |
| `wheelSpeedFL/FR/RL/RR` | Négy kerék sebessége (km/h) |
| `brakePressure` | Féknyomás (0–160 bar) |
| `yawRate` | Forgássebesség (°/s) — EPS kormányszögből |
| `lateralAccel` | Oldalirányú gyorsulás (m/s²) |
| `absActive` | ABS aktív-e (bool) |
| `tractionControlActive` | Trakciókontroll aktív-e (bool) |
| `stabilityControlActive` | Menetstabilizáló aktív-e (bool) |

**Keréksebesség modell:**

Az egyes kerekek sebessége a jármű sebességéből, a kormányszögből és a gázadásból adódik:
- **Kanyarodás:** A belső ívű kerekek lassabban, a külső ívűek gyorsabban forognak a kormányszög arányában
- **Fékezés:** Minden kerék sebessége arányosan csökken a féknyomással
- **Erős gázadás:** Ha `throttle > 65%` és nincs féknyomás, a hajtott (hátsó) kerekek csúszni kezdenek

**Aktiválási logika:**

```python
# ABS: féknyomás + kerékcsúszás detekció
absActive = brakePressure > 40 and speed > 10 and
            any(wheel < speed * 0.80 for wheel in [FL, FR, RL, RR])

# TC: hátsó kerékcsúszás gázadásnál
tractionControlActive = speed > 5 and brakePressure < 5 and
                        (wheelRL > speed + 5 or wheelRR > speed + 5)

# DSC: túl nagy forgássebesség
stabilityControlActive = abs(yawRate) > 10 and speed > 30
```

**3 CAN keretet** küld (0x2C1, 0x2C3, 0x2C8) 10–20 Hz frekvenciával.

---

### EGS modul — Elektronisches Getriebe Steuergerät

A ZF 8HP90 8 fokozatú automata váltó szimulációja. A fokozatváltást a kontroller RB/LB gombjaival lehet vezérelni (M Steptronic mód).

**Áttételi számok (ZF 8HP90):**

| Fokozat | R | N | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|---|---|
| Áttétel | 3.478 | 0 | 5.000 | 3.200 | 2.143 | 1.720 | 1.313 | 1.000 | 0.882 | 0.823 |

**Nyomatékátalakító modell:**

A nyomatékátalakító csúszása (slip) dinamikusan változik sebesség és terhelés alapján. `Lockup` üzemmódba lép ha `sebesség ≥ 25 km/h`, `gáz ≤ 50%`, nincs váltás és az olajhőmérséklet `≥ 40°C`. Lockup esetén a csúszás minimális (2%), egyébként sebességfüggően 8–45%.

```
n_out = n_turbine / i_gear
v [km/h] = (n_out / 3.15) × 2.22 × 60 / 1000
```

**2 CAN keretet** küld (0x1B2 100 Hz, 0x1B4 10 Hz).

---

### EPS modul — Electric Power Steering

Az elektromos szervokormány szimulációja. A kontroller bal analóg karjától olvassa a kormányszöget, DME és DSC értékeket felhasználva számítja a rásegítési tényezőt.

**Szimulált értékek:**

| Érték | Leírás |
|---|---|
| `steeringAngle` | Kormányszög: ±540° |
| `steeringRate` | Kormányszög változási sebessége (°/s) |
| `steeringTorqueDriver` | Vezető által kifejtett nyomaték (Nm) |
| `steeringAssistTorque` | EPS segédnyomaték (Nm) |
| `epsMotorCurrent` | EPS villanymotorának áramfelvétele (A) |
| `assistFactor` | Rásegítési tényező: 20–100% |

**Sebességfüggő rásegítés:**

```
assistFactor = max(0.20, 1.0 - vehicle_speed / 180)
```

Alacsony sebességnél (pl. parkolás) közel 100% rásegítést ad, 180 km/h felett a minimumra (20%) csökken, valósabb visszajelzést biztosítva.

**Holtzonaszűrő** a gamepad analóg kar pontatlanságának kiszűrésére: ±15% holtzona, ezen kívüli értékeknél arányos skálázás.

**2 CAN keretet** küld (0x3D0 100 Hz, 0x3D2 50 Hz).

---

### DTCManager — Hibakód kezelés

Közös alaposztály, amelyből minden modul örököl. Kezeli az OBD2 szabványú Diagnostic Trouble Code (DTC) hibakódokat.

**Állapotok:**

| Állapot | Leírás | Törlés |
|---|---|---|
| `activeDTC` | Jelenleg fennálló hiba | Automatikus (szenzor visszaáll) vagy manuális |
| `storedDTC` | Korábban előfordult hiba | Csak explicit `CLEAR_DTC` parancsra |

**Automatikus DTC logika — példák:**

| Modul | DTC kód | Feltétel |
|---|---|---|
| DME | P0217 | Hűtővíz hőmérséklet > 130°C |
| DME | P0520 | RPM > 1000 és olajnyomás < 0.5 bar |
| DME | P0562 | Akkufeszültség < 11.5 V |
| DSC | C0021 | FL keréksebesség > 50%-kal eltér az átlagtól |
| EGS | P0711 | Váltóolaj hőmérséklet > 130°C |
| EPS | C0475 | Motor áramerősség > 95% (túlmelegedés) |

**Perzisztens tárolás:** A tárolt DTC kódok JSON fájlba mentődnek (`dtc_dme.json` stb.), és az alkalmazás újraindításakor visszatöltődnek — ahogy egy valós autóban sem vesznek el a kódok a motor leállításakor.

**Y gomb — Random DTC injektálás:** 2–4 modult érint véletlenszerűen, modulonként 1–2 kód kerül be a pool-ból kiválasztva. Fejlesztési és tesztelési célokra készült.

**X gomb — DTC törlés:** Minden modul összes aktív és tárolt DTC kódját törli, a JSON fájlokat is frissíti.

---

### CanController — CAN keretkódoló

Felelős a nyers bájt adatokból szabványos CAN keret előállításáért. Az ISO 11898 szabványt követi.

**Keretfelépítés:**

```
SOF(1) + ID(11) + RTR(1) + IDE(1) + r0(1) + DLC(4) + DATA(0-64 bit)
  → CRC-15 számítás az előbbiekre (generátorpolinom: 0x4599)
  → + CRC(15) + CRC_delim(1)
  → Bit stuffing alkalmazása az eddigiekre
  → + ACK(2) + EOF(7)
```

**Bit stuffing:** Minden 5 egymást követő azonos bit után egy ellentétes „stuff bit" kerül beszúrásra. A vevő oldal (DiagApp) destuffing után ellenőrzi a CRC-t és értelmezi a keretet.

---

### OBD2Gateway — Soros kommunikáció

`threading.Thread` leszármazott, amely a háttérben fut és kezeli a soros port kommunikációt.

Élő módban (`LIVE_START`) 50 ms-onként elküldi az összes modul összes aktuális CAN keretét a soros porton ASCII bitsorozatként. Bejövő parancsokat olvas és értelmez szöveges, sortörés-határolt protokollon.

**Parancsok:**

| Parancs | Válasz | Leírás |
|---|---|---|
| `LIVE_START` | `OK LIVE_START` | Élő adatfolyam indítása |
| `LIVE_STOP` | `OK LIVE_STOP` | Élő adatfolyam leállítása |
| `READ_LIVE` | CAN keretek | Egyszeri snapshot |
| `READ_DTC_ACTIVE` | 0x700 CAN keret(ek) | Aktív DTC kódok lekérése |
| `READ_DTC_STORED` | 0x701 CAN keret(ek) | Tárolt DTC kódok lekérése |
| `CLEAR_DTC` | `OK CLEAR_DTC` | Összes DTC törlése |

**DTC kódolás CAN keretben:** Egy kód 2 bájtot foglal (OBD2 szabvány szerint), tehát egy 8 bájtos keretbe 4 DTC kód fér. Ha több kód van, több egymást követő keret kerül kiküldésre a 0x700/0x701 azonosítón.

---

### DiagApp — Diagnosztikai alkalmazás

Tkinter alapú asztali GUI alkalmazás, amely a soros porton fogadott CAN kereteket valós időben dekódolja és megjeleníti.

**Főbb funkciók:**
- COM port kiválasztás és csatlakozás kezelése
- Élő adatmegjelenítés tabfüles elrendezésben:
  - **Overview:** Sebesség, RPM, fokozat, nyomaték, hőmérsékletek, ABS/TC/DSC státusz
  - **DME tab:** Összes motorparaméter
  - **DSC tab:** Keréksebesség értékek, fékedatok, gyorsulások
  - **EPS tab:** Kormányszög, nyomatékok, motor áram
  - **EGS tab:** Váltóadatok, csúszás, lockup állapot
  - **DTC tab:** Aktív és tárolt DTC kódok listája OBD2 leírással
- DTC listboxban a kódok típus szerint színezve: `P`=piros, `C`=sárga, `U`=kék, `B`=zöld
- Nyers CAN frame napló időbélyeggel
- Adatvesztés jelzés: 2 másodperc után `⚠ Nincs adat` figyelmeztetés

---

## CAN frame azonosítók

| CAN ID | Forrás | Küldési frekvencia | Tartalom |
|---|---|---|---|
| `0x0A0` | DME | 50 Hz | RPM, fojtószelep, légtömegáram |
| `0x0A1` | DME | 10 Hz | Hűtővíz, szívólevegő, olajhőmérséklet |
| `0x0A2` | DME | 5 Hz | Akkufeszültség, olajnyomás |
| `0x0A3` | DME | 20 Hz | O2 szenzor, kopogásérzékelő |
| `0x0A4` | DME | 50 Hz | Nyomaték, referencia nyomaték, teljesítmény |
| `0x1B2` | EGS | 100 Hz | Fokozat, turbina RPM, kimeneti RPM, lockup |
| `0x1B4` | EGS | 10 Hz | Váltóolaj hőmérséklet, nyomatékátalakító csúszás |
| `0x2C1` | DSC | 100 Hz | Jármű sebesség, FL/FR keréksebesség, ABS/TC/DSC státusz |
| `0x2C3` | DSC | 100 Hz | Fékpedál, féknyomás, yaw rate, gyorsulások |
| `0x2C8` | DSC | 50 Hz | RL/RR keréksebesség, oldalirányú gyorsulások |
| `0x3D0` | EPS | 100 Hz | Kormányszög, szögsebesség, vezető nyomaték, segédnyomaték |
| `0x3D2` | EPS | 50 Hz | EPS motor áramerősség, rásegítési tényező |
| `0x700` | GW | igény | Aktív DTC kódok (4 kód/keret) |
| `0x701` | GW | igény | Tárolt DTC kódok (4 kód/keret) |

---

## DTC hibakódok

A rendszer 200+ OBD2 szabványos hibakódot tartalmaz a `DTC_Database.py` fájlban, négy modul szerint szervezve:

| Modul | Kód prefix | Példa kódok |
|---|---|---|
| DME | P0xxx | P0217 (túlmelegedés), P0300 (gyújtáskimaradás), P0562 (feszültség alacsony) |
| DSC | C0xxx | C0021 (keréksebesség szenzor), C0196 (yaw rate szenzor), C0267 (pumpa motor) |
| EGS | P07xx | P0700 (váltóvezérlés hiba), P0741 (nyomatékátalakító csúszás), P0783 (3-4 váltás) |
| EPS | C04xx–C05xx | C0450 (kormányszög szenzor), C0471 (EPS motor), C0510 (csökkentett rásegítés) |

---

## Telepítés és futtatás

### Rendszerkövetelmények

- Python 3.10+
- Virtuális COM port szoftver (Windows: [com0com](https://com0com.sourceforge.net/))
- XInput kompatibilis USB gamepad (pl. Xbox kontroller)

### Telepítés

```bash
git clone https://github.com/<felhasználónév>/<repository-név>.git
cd <repository-név>
pip install pygame pyserial
```

### Virtuális COM port beállítása

1. Telepítsd a **com0com** szoftvert
2. Hozz létre egy COM port párt: pl. **COM8 ↔ COM9**
3. A szimuláció a COM8 porton küld, a DiagApp a COM9 porton fogad

> A portszám a `Dashboard.py`-ban és a `DiagApp.py`-ban módosítható.

### Futtatás

```bash
# 1. terminal — Szimuláció és műszerfal
python Dashboard.py

# 2. terminal — Diagnosztikai alkalmazás
python DiagApp.py
```

A DiagApp-ban:
1. Válaszd ki a **COM9** portot a legördülő menüből
2. Kattints a **Csatlakozás** gombra
3. Kattints az **Élő adatok indítása** gombra

---

## Vezérlők

| Gomb / tengely | Funkció | Xbox megfelelő |
|---|---|---|
| Bal analóg (X tengely) | Kormányszög (±540°) | Bal joystick vízszintes |
| Jobb trigger | Gázpedál (0–100%) | RT |
| Bal trigger | Fékpedál (0–100%) | LT |
| Jobb váll gomb | Váltás felfelé | RB |
| Bal váll gomb | Váltás lefelé | LB |
| Menu gomb | Gyújtás BE/KI | ☰ Menu |
| A gomb | Motor indítás / leállítás | A |
| Y gomb | Random DTC hibakód injektálás | Y |
| X gomb | Összes DTC törlése | X |

---

## Licenc

Ez a projekt szakdolgozat keretében készült oktatási és kutatási célból.

---

*Miskolci Egyetem — Gépészmérnöki és Informatikai Kar — Programtervező informatikus*











