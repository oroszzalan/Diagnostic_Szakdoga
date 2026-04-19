# 🔌 Diagnostic_Szakdoga

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







