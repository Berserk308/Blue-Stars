===============================================================================
Dataset: blue_stars_results.csv
Project: Photometric analysis of hot stars (spectral types O, B, A)
Author: [Berserk 308]
Version: [1.0.0]
===============================================================================

📌 DESCRIPTION:
This dataset includes UBV photometric data for 50 well-known hot stars,
including bright field stars, early-type main sequence stars, and members
of the Pleiades cluster and Orion/Scorpius associations.

Each row contains:
- Star name
- Visual magnitude (V)
- Color indices: B–V and U–B
- Estimated effective temperature (Teff) in Kelvin
- Approximate RGB color (for visualization purposes)
- Hex color code derived from the RGB value
- Status: 'ok', 'error', or 'not found'

📊 TEMPERATURE ESTIMATION FORMULA:
T_eff = 4600 * [ 1 / (0.92 * (B–V) + 1.7) + 1 / (0.92 * (B–V) + 0.62) ]
(from Ballesteros, 2012)

🌈 COLOR MAPPING:
The RGB color is an approximate mapping from temperature to visible color
based on blackbody radiation models. It is for visualization only and not
meant to be spectroscopically accurate.

===============================================================================
📡 DATA SOURCES
===============================================================================

Primary photometric data source:
- General Catalogue of Photometric Data (GCPD)
- VizieR catalog ID: II/215
- Accessed via: https://vizier.cds.unistra.fr
- Hosted by: CDS — Centre de Données astronomiques de Strasbourg
Additional catalogues queried:
- APASS DR9 (II/336)
- Tycho-2 (I/259)
- Simbad photometry service

Data access method:
- Queried using Astroquery’s VizieR module (Python)
- Star names resolved through VizieR object search
- When necessary, Simbad is queried for missing photometry

===============================================================================
📂 FILES INCLUDED
===============================================================================

- blue_stars.csv .................... Input star list (50 stars)
- blue_stars_query.py ............... Python script to retrieve and process data
- blue_stars_results.csv ............ Final results with photometry, Teff, RGB, hex color
- README_blue_stars.md ............. This documentation file

===============================================================================