import pandas as pd
import numpy as np
from astroquery.vizier import Vizier

def bv_to_temperature(bv):
    return 4600 * ((1 / (0.92 * bv + 1.7)) + (1 / (0.92 * bv + 0.62)))

def temperature_to_rgb(temp_k):
    t = temp_k / 100.0
    if t < 66:
        r = 255
        g = 99.47 * np.log(t) - 161.12
        b = 0 if t < 19 else 138.51 * np.log(t - 10) - 305.04
    else:
        r = 329.69 * ((t - 60) ** -0.1332)
        g = 288.12 * ((t - 60) ** -0.0755)
        b = 255
    return tuple(np.clip([r, g, b], 0, 255) / 255.0)

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

def process_star_catalog(csv_input="blue_stars.csv", csv_output="blue_stars_results.csv"):
    df = pd.read_csv(csv_input)
    Vizier.ROW_LIMIT = 50
    gcpd = Vizier(columns=["Star", "Vmag", "B-V", "U-B"])
    apass = Vizier(columns=["B-V", "Vmag", "Bmag"])
    tycho = Vizier(columns=["BTmag", "VTmag"])

    results = []

    for _, row in df.iterrows():
        name_candidates = [row[col] for col in ['name_input', 'name_resolved', 'name_alt1'] if pd.notna(row[col])]
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
            status = "no B-V"
            print(f"⚠️ No usable B–V found for {name_candidates[0]}")
        else:
            try:
                temp = bv_to_temperature(bv)
                rgb = temperature_to_rgb(temp)
                status = "ok"
                print(f"✅ {name_candidates[0]} resolved via {resolved_used} → T_eff = {temp:.0f} K ({source})")
            except Exception as e:
                temp = rgb = None
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
            'source': source,
            'status': status
        })

    pd.DataFrame(results).to_csv(csv_output, index=False)
    print(f"\n✅ Results saved to '{csv_output}'")

if __name__ == "__main__":
    process_star_catalog()
