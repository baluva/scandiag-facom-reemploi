# Réemploi RSE — FACOM SCANDIAG (TEXA Laser Examiner, DX.TSCANPB)

Dépôt de rendu du concours : rétro-ingénierie + preuve de concept de seconde vie.

## 1. Ce qu'est l'appareil (résultat de la rétro-ingénierie)

Analyseur portatif d'usure freins/pneus par **triangulation optique** (laser vert + micro-caméra),
fabriqué par **TEXA S.p.A.** et rebadgé FACOM. Carte **PC524-E** (2019).

**Architecture (centrée sur le STM32) :**

| Bloc | Composant | Rôle |
|------|-----------|------|
| MCU | **STM32F429** (ARM Cortex-M4 @180 MHz, FPU) | cœur ; DCMI (caméra), FMC (SDRAM), USB OTG |
| Framebuffer | SDRAM **ISSI IS42S16400J** (64 Mbit) | image caméra |
| Mémoire | flash/NAND BGA + **EEPROM Atmel** SOIC-8 | firmware, ~500 rapports, config |
| Caméra | CMOS WXGA **1 Mpx 30 fps** | sur DCMI |
| Laser | diode **verte 510–530 nm, >5 mW, classe 3R** | + driver courant constant |
| Sans-fil | module **Bluetooth SPP** (antenne PCB) | sur USART du STM32 |
| Alim | batterie **EEMB LP602248** 620 mAh/3,7 V + charge USB 5 V + DC-DC/LDO 3,3 V | |
| UI | bouton multifonction + **LED RGB** | GPIO |

> ⚠️ Les pilotes FTDI / Cypress « Uniprobe » du pack d'installation sont **génériques à la gamme TEXA**
> et ne correspondent pas à cette carte : le lien USB filaire passe par l'**USB natif du STM32F429**.

## 2. Accès / reprogrammation (sans sonde SWD)

Le STM32F429 possède un **bootloader d'usine** en mémoire système :
- **USB DFU** : mettre **BOOT0=1** au reset → l'appareil énumère en *STM32 BOOTLOADER* (`VID 0483 / PID DF11`).
  Flash : `STM32CubeProgrammer` ou `dfu-util -a 0 -s 0x08000000:leave -D firmware.bin`.
- **UART bootloader** : BOOT0=1, sur un USART → `stm32flash` / `stm32loader`.
- **SWD** (si sonde dispo) : pads SWDIO/SWCLK/GND/3V3/NRST.

Protection en lecture (RDP) à vérifier : si RDP=1, lecture du firmware d'origine bloquée,
mais effacement + reprogrammation toujours possibles (suffit à prouver la maîtrise du MCU).

## 3. Preuve de concept

**Plan A (sûr) — rétro-ingénierie du protocole série + pilotage maison :**
1. Connexion série (Bluetooth SPP ou USB).
2. Capture des trames logiciel TEXA ↔ device (`tools/scandiag_serial.py sniff`).
3. Décodage du protocole (mesure, batterie, version, laser).
4. Script Python qui pilote l'appareil sans le logiciel TEXA.

**Plan B (bonus) — firmware custom :** entrée en DFU et flash d'un firmware de test
(clignotement LED RGB, lecture bouton, laser ON/OFF) → preuve de contrôle total.

## 4. Outils

- `tools/scandiag_serial.py` — sniff / scanbaud / send / terminal série (voir entête du fichier).
- Installés : `pyserial`, `stm32loader`, `esptool`. À ajouter pour le flash : `STM32CubeProgrammer` ou `dfu-util`.

```bash
python tools/scandiag_serial.py ports            # lister les ports COM
python tools/scandiag_serial.py scanbaud COM5    # trouver le baudrate
python tools/scandiag_serial.py sniff COM5 115200
```

## 5. Arborescence

```
SCANDIAG_reemploi/
├── README.md
├── tools/        scripts de rétro-ingénierie / pilotage
├── datasheets/   datasheets des composants clés
├── firmware/     firmware POC (DFU de test) — à venir
└── docs/         documentation des fonctions développées
```
