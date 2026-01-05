import json
from pathlib import Path
import numpy as np
from scipy.interpolate import interp1d

CANDIDATE_KEYS = ("irradiance", "transmittance",
                  "absorbance", "values", "data")


def fix_file(path: Path):
    with path.open("r", encoding="utf-8") as f:
        j = json.load(f)

    modified = False
    report = []

    for name, obj in j.items():
        wl = obj.get("wavelengths")
        if not isinstance(wl, list) or len(wl) == 0:
            continue

        wl = np.array(wl, dtype=float)
        found_key = None
        for k in CANDIDATE_KEYS:
            if k in obj:
                found_key = k
                break

        if not found_key:
            report.append((name, "no data array"))
            continue

        fp = obj.get(found_key)
        if not isinstance(fp, list):
            report.append((name, f"{found_key} not a list"))
            continue

        fp = np.array(fp, dtype=float)
        if wl.size == fp.size:
            continue  # ok

        # handle trivial cases
        if fp.size == 0:
            new_fp = np.zeros_like(wl, dtype=float)
            reason = "fp empty -> zeros"
        elif fp.size == 1:
            new_fp = np.full_like(wl, float(fp[0]), dtype=float)
            reason = "fp single value -> broadcast"
        else:
            # assume fp sampled uniformly across wl range -> map onto wl
            xp_fp = np.linspace(wl.min(), wl.max(), fp.size)
            try:
                f = interp1d(xp_fp, fp, kind="linear",
                             bounds_error=False, fill_value=0.0)
                new_fp = f(wl)
                reason = f"interpolated from {fp.size} -> {wl.size}"
            except Exception as e:
                new_fp = np.zeros_like(wl, dtype=float)
                reason = f"interp failed: {e} -> zeros"

        # write back
        obj[found_key] = new_fp.tolist()
        modified = True
        report.append((name, found_key, fp.size, wl.size, reason))

    if modified:
        bak = path.with_suffix(path.suffix + ".bak")
        path.replace(bak)  # move original to .bak
        with path.open("w", encoding="utf-8") as f:
            json.dump(j, f, indent=2, ensure_ascii=False)
    return report, modified


if __name__ == "__main__":
    p = Path(__file__).parents[1] / "spectra_data.json"
    report, modified = fix_file(p)
    for r in report:
        print(r)
    print("Modified:", modified)
