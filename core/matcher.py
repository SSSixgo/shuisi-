import re
from rapidfuzz import fuzz
from utils.helpers import _safe_str

def calculate_match_score(new_proj, new_mat, new_spec, lib_proj, lib_mat, lib_spec):
    new_proj, new_mat, new_spec = _safe_str(new_proj), _safe_str(new_mat), _safe_str(new_spec)
    lib_proj, lib_mat, lib_spec = _safe_str(lib_proj), _safe_str(lib_mat), _safe_str(lib_spec)

    name_score = 0.0
    spec_score = 0.0

    if new_mat and lib_mat:
        if new_mat == lib_mat: name_score = 100.0
        elif new_mat in lib_mat or lib_mat in new_mat:
            min_len = min(len(new_mat), len(lib_mat))
            max_len = max(len(new_mat), len(lib_mat))
            name_score = 80.0 + (20.0 * (min_len / max_len)) if max_len > 0 else 80.0
        else:
            name_score = fuzz.token_sort_ratio(new_mat, lib_mat)
            if name_score < 65: name_score *= 0.7

    if new_spec and lib_spec:
        if new_spec == lib_spec: spec_score = 100.0
        elif new_spec in lib_spec or lib_spec in new_spec:
            min_len = min(len(new_spec), len(lib_spec))
            max_len = max(len(new_spec), len(lib_spec))
            spec_score = 70.0 + (30.0 * (min_len / max_len)) if max_len > 0 else 70.0
        else:
            spec_score = fuzz.token_set_ratio(new_spec, lib_spec)
            if spec_score < 65: spec_score *= 0.7

    if name_score >= 80 and new_spec and lib_spec:
        new_dn = re.findall(r'dn\s*(\d+)', new_spec.lower())
        lib_dn = re.findall(r'dn\s*(\d+)', lib_spec.lower())
        if new_dn and lib_dn and new_dn != lib_dn: spec_score = min(spec_score, 30.0)
        
        new_pn = re.findall(r'(\d+\.?\d*)\s*mpa', new_spec.lower())
        lib_pn = re.findall(r'(\d+\.?\d*)\s*mpa', lib_spec.lower())
        if new_pn and lib_pn and new_pn != lib_pn: spec_score = min(spec_score, 40.0)

    if new_mat and new_spec:
        if name_score < 30 or spec_score < 30: final = name_score * 0.8 + spec_score * 0.2
        else: final = name_score * 0.6 + spec_score * 0.4
    elif new_mat: final = name_score
    elif new_spec: final = spec_score
    else: final = 0.0

    if new_proj and lib_proj:
        if new_proj == lib_proj: final += 5.0
        elif new_proj in lib_proj or lib_proj in new_proj: final += 3.0
        elif fuzz.token_set_ratio(new_proj, lib_proj) >= 85: final += 1.0

    return round(min(100.0, final), 1)