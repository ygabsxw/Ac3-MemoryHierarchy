#!/usr/bin/env python3
"""
Extrai métricas relevantes dos stats.txt do gem5 e gera CSVs por experimento.
"""

import os
import re
import csv
from pathlib import Path

RESULTS_DIR = Path.home() / "gem5" / "results"
OUTPUT_DIR  = Path.home() / "gem5" / "analysis"
OUTPUT_DIR.mkdir(exist_ok=True)

# Métricas a extrair do stats.txt
METRICS = {
    "ipc":           r"^system\.cpu\.ipc\s+([\d.]+)",
    "cpi":           r"^system\.cpu\.cpi\s+([\d.]+)",
    "sim_seconds":   r"^simSeconds\s+([\d.]+)",
    "sim_insts":     r"^simInsts\s+([\d.]+)",
    "l1d_miss_rate": r"^system\.cpu\.dcache\.overallMissRate::total\s+([\d.]+)",
    "l1d_hits":      r"^system\.cpu\.dcache\.overallHits::total\s+([\d.]+)",
    "l1d_misses":    r"^system\.cpu\.dcache\.overallMisses::total\s+([\d.]+)",
    "l1d_accesses":  r"^system\.cpu\.dcache\.overallAccesses::total\s+([\d.]+)",
    "l1d_avg_lat":   r"^system\.cpu\.dcache\.overallAvgMissLatency::total\s+([\d.]+)",
    "l2_miss_rate":  r"^system\.l2cache\.overallMissRate::total\s+([\d.]+)",
    "l2_hits":       r"^system\.l2cache\.overallHits::total\s+([\d.]+)",
    "l2_misses":     r"^system\.l2cache\.overallMisses::total\s+([\d.]+)",
    "mem_reads":     r"^system\.mem_ctrl\.dram\.readReqs\s+([\d.]+)",
    "mem_writes":    r"^system\.mem_ctrl\.dram\.writeReqs\s+([\d.]+)",
}

def extract(stats_file):
    """Lê um stats.txt e retorna dict com as métricas."""
    data = {}
    try:
        text = stats_file.read_text(errors="ignore")
        for key, pattern in METRICS.items():
            m = re.search(pattern, text, re.MULTILINE)
            data[key] = float(m.group(1)) if m else None
        # MPKI calculado
        if data.get("l1d_misses") and data.get("sim_insts"):
            data["mpki"] = (data["l1d_misses"] / data["sim_insts"]) * 1000
        else:
            data["mpki"] = None
    except Exception as e:
        print(f"  ERRO ao ler {stats_file}: {e}")
    return data

def parse_exp_name(name):
    """Tenta extrair experimento, padrão de acesso e parâmetro do nome do diretório."""
    # Ex: exp1_seq_32kB, exp2_rand_4way, exp6_stride_lru
    parts = name.split("_", 2)
    exp     = parts[0] if len(parts) > 0 else name
    pattern = parts[1] if len(parts) > 1 else ""
    param   = parts[2] if len(parts) > 2 else ""
    return exp, pattern, param

# Agrupa por experimento
rows = []
for d in sorted(RESULTS_DIR.iterdir()):
    if not d.is_dir():
        continue
    stats = d / "stats.txt"
    if not stats.exists() or stats.stat().st_size < 500:
        print(f"[SKIP] {d.name} — stats.txt ausente ou vazio")
        continue
    exp, pattern, param = parse_exp_name(d.name)
    metrics = extract(stats)
    row = {"dir": d.name, "exp": exp, "pattern": pattern, "param": param, **metrics}
    rows.append(row)
    print(f"[OK]   {d.name:40s}  IPC={metrics.get('ipc','?')}  miss%={metrics.get('l1d_miss_rate','?')}")

# Salva CSV geral
all_csv = OUTPUT_DIR / "all_results.csv"
if rows:
    fieldnames = list(rows[0].keys())
    with open(all_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"\n✅ CSV geral salvo em: {all_csv}")

# Salva CSVs por experimento
from collections import defaultdict
by_exp = defaultdict(list)
for r in rows:
    by_exp[r["exp"]].append(r)

for exp, exp_rows in by_exp.items():
    csv_path = OUTPUT_DIR / f"{exp}.csv"
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(exp_rows[0].keys()))
        w.writeheader()
        w.writerows(exp_rows)
    print(f"✅ {csv_path.name} ({len(exp_rows)} linhas)")

print(f"\nTotal: {len(rows)} experimentos extraídos.")
