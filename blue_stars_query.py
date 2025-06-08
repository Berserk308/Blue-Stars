"""Retrieve photometric data for a list of hot stars.

This script queries a few VizieR catalogues in order to obtain the
photometric B--V colour index for each star in ``blue_stars.csv`` and
computes the corresponding effective temperature and an approximate RGB
colour.  The results are written to ``blue_stars_results.csv``.

Usage::

    python blue_stars_query.py --input blue_stars.csv --output results.csv

``astroquery`` is required to actually run the catalogue queries.  When
network access is not available the script will still run but will mark
the stars as ``not found``.
"""

import argparse
import sys

import pandas as pd
import numpy as np
from astroquery.vizier import Vizier
from astroquery.simbad import Simbad

def bv_to_temperature(bv):
    return 4600 * ((1 / (0.92 * bv + 1.7)) + (1 / (0.92 * bv + 0.62)))

def temperature_to_rgb(temp_k):
    """Map a temperature in Kelvin to an RGB triple and its hexadecimal code."""
    t = temp_k / 100.0
    if t < 66:
        r = 255
        g = 99.47 * np.log(t) - 161.12
        b = 0 if t < 19 else 138.51 * np.log(t - 10) - 305.04
    else:
        r = 329.69 * ((t - 60) ** -0.1332)
        g = 288.12 * ((t - 60) ** -0.0755)
        b = 255
    rgb = tuple(np.clip([r, g, b], 0, 255) / 255.0)
    hex_color = "#{:02X}{:02X}{:02X}".format(
        int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255)
    )
    return rgb, hex_color

def try_catalog(vizier, name, catalog_id, extract_tycho=False):
    try:
        result = vizier.query_object(name, catalog=catalog_id)
        if not result or len(result) == 0:
            return None
        for row in result[0]:
            try:
                if extract_tycho:
                    bt = float(row['BTmag']) if 'BTmag' in row.colnames else None
                    vt = float(row['VTmag']) if 'VTmag' in row.colnames else None
                    vmag = vt
                    bv = bt - vt if bt is not None and vt is not None else None
                    return bv, None, vmag if bv is not None else None
                else:
                    bv = float(row['B-V']) if 'B-V' in row.colnames else None
                    ub = float(row['U-B']) if 'U-B' in row.colnames else None
                    vmag = float(row.get('Vmag', np.nan))
                    if bv is not None:
                        return bv, ub, vmag
            except Exception:
                continue
    except Exception:
        return None
    return None

def try_simbad(name):
    """Try to get B, V and U fluxes from Simbad."""
    try:
        sim = Simbad()
        sim.add_votable_fields("flux(U)", "flux(B)", "flux(V)")
        res = sim.query_object(name)
        if res is None:
            return None
        bmag = res["FLUX_B"][0]
        vmag = res["FLUX_V"][0]
        umag = res["FLUX_U"][0]
        if bmag is None or vmag is None:
            return None
        bv = float(bmag) - float(vmag)
        ub = None if umag is None else float(bmag) - float(umag)
        return bv, ub, float(vmag)
    except Exception:
        return None

def process_star_catalog(csv_input="blue_stars.csv", csv_output="blue_stars_results.csv"):
    """Process the input catalogue and write the results."""
    df = pd.read_csv(csv_input)
    total = len(df)
    Vizier.ROW_LIMIT = 200
    gcpd = Vizier(columns=["Star", "Vmag", "B-V", "U-B"])
    apass = Vizier(columns=["B-V", "Vmag", "Bmag"])
    tycho = Vizier(columns=["BTmag", "VTmag"])

    results = []

    for idx, (_, row) in enumerate(df.iterrows(), start=1):
        name_candidates = [
            row[col] for col in ["name_input", "name_resolved", "name_alt1"]
            if pd.notna(row[col])
        ]
        print(f"[{idx}/{total}] {name_candidates[0]}")
        bv = ub = vmag = None
        source = "none"
        status = "not found"
        resolved_used = None

        for name in name_candidates:
            gcpd_result = try_catalog(gcpd, name, "II/215")
            if gcpd_result:
                bv, ub, vmag = gcpd_result
                source = "GCPD"
                resolved_used = name
                break

        if bv is None:
            for name in name_candidates:
                apass_result = try_catalog(apass, name, "II/336/apass9")
                if apass_result:
                    bv, ub, vmag = apass_result
                    source = "APASS"
                    resolved_used = name
                    break

        if bv is None:
            for name in name_candidates:
                tycho_result = try_catalog(tycho, name, "I/259/tyc2", extract_tycho=True)
                if tycho_result:
                    bv, ub, vmag = tycho_result
                    source = "Tycho-2"
                    resolved_used = name
                    break

        if bv is None:
            for name in name_candidates:
                simbad_result = try_simbad(name)
                if simbad_result:
                    bv, ub, vmag = simbad_result
                    source = "Simbad"
                    resolved_used = name
                    break

        if bv is None:
            status = "no B-V"
            temp = rgb = hex_color = None
            print(f"⚠️ No usable B–V found for {name_candidates[0]}")
        else:
            try:
                temp = bv_to_temperature(bv)
                rgb, hex_color = temperature_to_rgb(temp)
                status = "ok"
                print(
                    f"✅ {name_candidates[0]} resolved via {resolved_used}"
                    f" → T_eff = {temp:.0f} K ({source})"
                )
            except Exception as e:
                temp = rgb = hex_color = None
                status = "processing error"
                print(f"⚠️ Error for {name_candidates[0]}: {e}")

        results.append({
            'name': name_candidates[0],
            'resolved_used': resolved_used,
            'V': vmag,
            'B-V': bv,
            'U-B': ub,
            'T_eff_K': round(temp) if status == 'ok' and not np.isnan(temp) else None,
            'RGB': rgb if status == 'ok' else None,
            'hex_color': hex_color if status == 'ok' else None,
            'source': source,
            'status': status
        })

    pd.DataFrame(results).to_csv(csv_output, index=False)
    print(f"\n✅ Results saved to '{csv_output}'")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query photometry for hot stars")
    parser.add_argument("--input", default="blue_stars.csv", help="CSV file with the star list")
    parser.add_argument("--output", default="blue_stars_results.csv", help="Output CSV file")
    args = parser.parse_args()
    try:
        process_star_catalog(args.input, args.output)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)