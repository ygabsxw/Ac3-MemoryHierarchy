#!/usr/bin/env python3
"""
Gera gráficos para o artigo IEEE a partir dos CSVs extraídos do gem5.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from pathlib import Path

ANALYSIS = Path.home() / "gem5" / "analysis"
PLOTS    = Path.home() / "gem5" / "plots"
PLOTS.mkdir(exist_ok=True)

plt.rcParams.update({
    "font.family":  "serif",
    "font.size":    11,
    "axes.titlesize": 12,
    "axes.labelsize": 11,
    "legend.fontsize": 9,
    "figure.dpi":   150,
})

COLORS  = ["#2196F3", "#F44336", "#4CAF50", "#FF9800", "#9C27B0", "#00BCD4"]
MARKERS = ["o", "s", "^", "D", "v", "P"]

def save(fig, name):
    path = PLOTS / f"{name}.pdf"
    fig.savefig(path, bbox_inches="tight")
    path2 = PLOTS / f"{name}.png"
    fig.savefig(path2, bbox_inches="tight")
    print(f"  ✅ {path.name}")
    plt.close(fig)

# ── Ordem de tamanhos ──────────────────────────────────────
SIZE_ORDER = ["4kB","8kB","16kB","32kB","64kB","128kB","256kB"]
def size_key(s):
    try: return SIZE_ORDER.index(s)
    except: return 99

# ═══════════════════════════════════════════════════════════
# EXP1a — Tamanho de L1 (microbenchmark)
# ═══════════════════════════════════════════════════════════
print("\n[EXP1a] Tamanho de L1 — microbenchmark")
df1 = pd.read_csv(ANALYSIS / "exp1.csv")
df1m = df1[df1["pattern"].isin(["seq","rand","stride"])].copy()
df1m["order"] = df1m["param"].apply(size_key)
df1m = df1m.sort_values("order")

fig, axes = plt.subplots(1, 2, figsize=(10, 4))

for i, (pat, color, marker) in enumerate(zip(["seq","rand","stride"], COLORS, MARKERS)):
    sub = df1m[df1m["pattern"] == pat]
    axes[0].plot(sub["param"], sub["ipc"],      marker=marker, color=color, label=pat, linewidth=1.8)
    axes[1].plot(sub["param"], sub["mpki"],     marker=marker, color=color, label=pat, linewidth=1.8)

axes[0].set_title("IPC vs Tamanho de L1")
axes[0].set_xlabel("Tamanho da Cache L1D")
axes[0].set_ylabel("IPC")
axes[0].legend(); axes[0].grid(True, alpha=0.3)

axes[1].set_title("MPKI vs Tamanho de L1")
axes[1].set_xlabel("Tamanho da Cache L1D")
axes[1].set_ylabel("MPKI (Misses por Kilo-Instrução)")
axes[1].legend(); axes[1].grid(True, alpha=0.3)

fig.suptitle("EXP1: Impacto do Tamanho da Cache L1D", fontweight="bold")
fig.tight_layout()
save(fig, "exp1a_tamanho_l1_micro")

# ═══════════════════════════════════════════════════════════
# EXP1b — MiBench
# ═══════════════════════════════════════════════════════════
print("\n[EXP1b] Tamanho de L1 — MiBench")
df1b = df1[df1["pattern"].isin(["basicmath","dijkstra"])].copy()
df1b["order"] = df1b["param"].apply(size_key)
df1b = df1b.sort_values("order")

fig, axes = plt.subplots(1, 2, figsize=(10, 4))
for i, (pat, color, marker) in enumerate(zip(["basicmath","dijkstra"], COLORS, MARKERS)):
    sub = df1b[df1b["pattern"] == pat]
    axes[0].plot(sub["param"], sub["ipc"],  marker=marker, color=color, label=pat, linewidth=1.8)
    axes[1].plot(sub["param"], sub["mpki"], marker=marker, color=color, label=pat, linewidth=1.8)

axes[0].set_title("IPC vs Tamanho de L1 (MiBench)")
axes[0].set_xlabel("Tamanho da Cache L1D"); axes[0].set_ylabel("IPC")
axes[0].legend(); axes[0].grid(True, alpha=0.3)
axes[1].set_title("MPKI vs Tamanho de L1 (MiBench)")
axes[1].set_xlabel("Tamanho da Cache L1D"); axes[1].set_ylabel("MPKI")
axes[1].legend(); axes[1].grid(True, alpha=0.3)
fig.suptitle("EXP1b: Impacto do Tamanho da Cache L1D — MiBench", fontweight="bold")
fig.tight_layout()
save(fig, "exp1b_tamanho_l1_mibench")

# ═══════════════════════════════════════════════════════════
# EXP2 — Associatividade
# ═══════════════════════════════════════════════════════════
print("\n[EXP2] Associatividade")
df2 = pd.read_csv(ANALYSIS / "exp2.csv")
ASSOC_ORDER = ["1way","2way","4way","8way","16way"]
df2["order"] = df2["param"].apply(lambda x: ASSOC_ORDER.index(x) if x in ASSOC_ORDER else 99)
df2 = df2.sort_values("order")

fig, axes = plt.subplots(1, 2, figsize=(10, 4))
for pat, color, marker in zip(["seq","rand"], COLORS, MARKERS):
    sub = df2[df2["pattern"] == pat]
    axes[0].plot(sub["param"], sub["ipc"],      marker=marker, color=color, label=pat, linewidth=1.8)
    axes[1].plot(sub["param"], sub["l1d_miss_rate"]*100, marker=marker, color=color, label=pat, linewidth=1.8)

axes[0].set_title("IPC vs Associatividade")
axes[0].set_xlabel("Associatividade"); axes[0].set_ylabel("IPC")
axes[0].legend(); axes[0].grid(True, alpha=0.3)
axes[1].set_title("Miss Rate vs Associatividade")
axes[1].set_xlabel("Associatividade"); axes[1].set_ylabel("Miss Rate (%)")
axes[1].legend(); axes[1].grid(True, alpha=0.3)
fig.suptitle("EXP2: Impacto da Associatividade (L1D=32kB)", fontweight="bold")
fig.tight_layout()
save(fig, "exp2_associatividade")

# ═══════════════════════════════════════════════════════════
# EXP3 — Níveis de Cache
# ═══════════════════════════════════════════════════════════
print("\n[EXP3] Níveis de cache")
df3 = pd.read_csv(ANALYSIS / "exp3.csv")
CONFIG_ORDER = ["no_l2","l2_256kB","l2_1MB","l2_4MB","l1_256kB"]
CONFIG_LABELS = ["Sem L2","L2 256kB","L2 1MB","L2 4MB","L1 256kB"]
df3["order"] = df3["param"].apply(lambda x: CONFIG_ORDER.index(x) if x in CONFIG_ORDER else 99)
df3 = df3.sort_values("order")

fig, axes = plt.subplots(1, 2, figsize=(10, 4))
x = np.arange(len(CONFIG_ORDER))
w = 0.35
for i, (pat, color) in enumerate(zip(["seq","rand"], COLORS)):
    sub = df3[df3["pattern"] == pat].set_index("param").reindex(CONFIG_ORDER)
    axes[0].bar(x + i*w - w/2, sub["ipc"],          width=w, color=color, label=pat, alpha=0.85)
    axes[1].bar(x + i*w - w/2, sub["l1d_miss_rate"]*100, width=w, color=color, label=pat, alpha=0.85)

for ax in axes:
    ax.set_xticks(x); ax.set_xticklabels(CONFIG_LABELS, rotation=15, ha="right")
    ax.legend(); ax.grid(True, alpha=0.3, axis="y")

axes[0].set_title("IPC vs Hierarquia de Cache"); axes[0].set_ylabel("IPC")
axes[1].set_title("Miss Rate L1 vs Hierarquia"); axes[1].set_ylabel("Miss Rate (%)")
fig.suptitle("EXP3: Impacto dos Níveis de Cache", fontweight="bold")
fig.tight_layout()
save(fig, "exp3_niveis_cache")

# ═══════════════════════════════════════════════════════════
# EXP4 — Tipo de Memória
# ═══════════════════════════════════════════════════════════
print("\n[EXP4] Latência de memória")
df4 = pd.read_csv(ANALYSIS / "exp4.csv")
MEM_ORDER  = ["DDR3_1600_8x8","DDR4_2400_8x8","DDR5_4400_4x8"]
MEM_LABELS = ["DDR3-1600","DDR4-2400","DDR5-4400"]

fig, axes = plt.subplots(1, 2, figsize=(10, 4))
x = np.arange(len(MEM_ORDER)); w = 0.35
for i, (pat, color) in enumerate(zip(["seq","rand"], COLORS)):
    sub = df4[df4["pattern"] == pat].set_index("param").reindex(MEM_ORDER)
    axes[0].bar(x + i*w - w/2, sub["ipc"],         width=w, color=color, label=pat, alpha=0.85)
    axes[1].bar(x + i*w - w/2, sub["l1d_avg_lat"]/1000, width=w, color=color, label=pat, alpha=0.85)

for ax in axes:
    ax.set_xticks(x); ax.set_xticklabels(MEM_LABELS)
    ax.legend(); ax.grid(True, alpha=0.3, axis="y")

axes[0].set_title("IPC vs Tipo de Memória"); axes[0].set_ylabel("IPC")
axes[1].set_title("Latência Média de Miss L1"); axes[1].set_ylabel("Latência (ns aprox.)")
fig.suptitle("EXP4: Impacto do Tipo de Memória (DDR3/4/5)", fontweight="bold")
fig.tight_layout()
save(fig, "exp4_memoria")

# ═══════════════════════════════════════════════════════════
# EXP5 — Tamanho de Linha
# ═══════════════════════════════════════════════════════════
print("\n[EXP5] Tamanho de cache line")
df5 = pd.read_csv(ANALYSIS / "exp5.csv")
LINE_ORDER = ["line64","line128","line256"]
LINE_LABELS = ["64B","128B","256B"]
df5["order"] = df5["param"].apply(lambda x: LINE_ORDER.index(x) if x in LINE_ORDER else 99)
df5 = df5.sort_values("order")

fig, axes = plt.subplots(1, 2, figsize=(10, 4))
for pat, color, marker in zip(["seq","rand","stride"], COLORS, MARKERS):
    sub = df5[df5["pattern"] == pat].set_index("param").reindex(LINE_ORDER).reset_index()
    axes[0].plot(LINE_LABELS, sub["ipc"],  marker=marker, color=color, label=pat, linewidth=1.8)
    axes[1].plot(LINE_LABELS, sub["mpki"], marker=marker, color=color, label=pat, linewidth=1.8)

axes[0].set_title("IPC vs Tamanho de Linha"); axes[0].set_ylabel("IPC")
axes[0].legend(); axes[0].grid(True, alpha=0.3)
axes[1].set_title("MPKI vs Tamanho de Linha"); axes[1].set_ylabel("MPKI")
axes[1].legend(); axes[1].grid(True, alpha=0.3)
fig.suptitle("EXP5: Impacto do Tamanho da Linha de Cache", fontweight="bold")
fig.tight_layout()
save(fig, "exp5_cache_line")

# ═══════════════════════════════════════════════════════════
# EXP6 — Política de Substituição
# ═══════════════════════════════════════════════════════════
print("\n[EXP6] Política de substituição")
df6 = pd.read_csv(ANALYSIS / "exp6.csv")
REPL_ORDER  = ["lru","random","fifo"]
REPL_LABELS = ["LRU","Random","FIFO"]

fig, axes = plt.subplots(1, 2, figsize=(10, 4))
x = np.arange(len(REPL_ORDER)); w = 0.25
for i, (pat, color) in enumerate(zip(["seq","rand","stride"], COLORS)):
    sub = df6[df6["pattern"] == pat].set_index("param").reindex(REPL_ORDER)
    axes[0].bar(x + (i-1)*w, sub["ipc"],          width=w, color=color, label=pat, alpha=0.85)
    axes[1].bar(x + (i-1)*w, sub["mpki"],         width=w, color=color, label=pat, alpha=0.85)

for ax in axes:
    ax.set_xticks(x); ax.set_xticklabels(REPL_LABELS)
    ax.legend(); ax.grid(True, alpha=0.3, axis="y")

axes[0].set_title("IPC vs Política de Substituição"); axes[0].set_ylabel("IPC")
axes[1].set_title("MPKI vs Política de Substituição"); axes[1].set_ylabel("MPKI")
fig.suptitle("EXP6: Impacto da Política de Substituição (L1=16kB)", fontweight="bold")
fig.tight_layout()
save(fig, "exp6_substituicao")

# ═══════════════════════════════════════════════════════════
# EXP7 — Política de Escrita (só writeback disponível)
# ═══════════════════════════════════════════════════════════
print("\n[EXP7] Política de escrita")
df7 = pd.read_csv(ANALYSIS / "exp7.csv")
fig, ax = plt.subplots(figsize=(6, 4))
pats = df7["pattern"].tolist()
ipcs = df7["ipc"].tolist()
bars = ax.bar(pats, ipcs, color=COLORS[:len(pats)], alpha=0.85)
ax.bar_label(bars, fmt="%.3f", padding=3)
ax.set_title("EXP7: IPC — Write-Back\n(Write-Through abortado: impraticável com WS=64MB)")
ax.set_ylabel("IPC"); ax.set_xlabel("Padrão de Acesso")
ax.grid(True, alpha=0.3, axis="y")
fig.tight_layout()
save(fig, "exp7_escrita")

# ═══════════════════════════════════════════════════════════
# EXP8 — Prefetchers
# ═══════════════════════════════════════════════════════════
print("\n[EXP8] Prefetchers")
df8 = pd.read_csv(ANALYSIS / "exp8.csv")
PF_ORDER  = ["none","stride","tagged"]
PF_LABELS = ["None","Stride","Tagged"]

fig, axes = plt.subplots(1, 2, figsize=(10, 4))
x = np.arange(len(PF_ORDER)); w = 0.25
for i, (pat, color) in enumerate(zip(["seq","rand","stride"], COLORS)):
    sub = df8[df8["pattern"] == pat].set_index("param").reindex(PF_ORDER)
    axes[0].bar(x + (i-1)*w, sub["ipc"],  width=w, color=color, label=pat, alpha=0.85)
    axes[1].bar(x + (i-1)*w, sub["mpki"], width=w, color=color, label=pat, alpha=0.85)

for ax in axes:
    ax.set_xticks(x); ax.set_xticklabels(PF_LABELS)
    ax.legend(); ax.grid(True, alpha=0.3, axis="y")

axes[0].set_title("IPC vs Prefetcher"); axes[0].set_ylabel("IPC")
axes[1].set_title("MPKI vs Prefetcher"); axes[1].set_ylabel("MPKI")
fig.suptitle("EXP8: Impacto dos Prefetchers", fontweight="bold")
fig.tight_layout()
save(fig, "exp8_prefetcher")

# ═══════════════════════════════════════════════════════════
# EXP9 — Número de núcleos
# ═══════════════════════════════════════════════════════════
print("\n[EXP9] Número de núcleos")
df9 = pd.read_csv(ANALYSIS / "exp9.csv")
df9_valid = df9[df9["ipc"].notna()]

fig, ax = plt.subplots(figsize=(6, 4))
cores = df9_valid["pattern"].str.replace("core","").astype(int).tolist()
ipcs  = df9_valid["ipc"].tolist()
ax.plot(cores, ipcs, marker="o", color=COLORS[0], linewidth=2)
ax.plot(cores, cores, "--", color="gray", label="Speedup ideal", linewidth=1.2)
ax.set_title("EXP9: IPC vs Número de Núcleos (L2=1MB compartilhado)")
ax.set_xlabel("Número de Núcleos"); ax.set_ylabel("IPC")
ax.set_xticks(cores); ax.legend(); ax.grid(True, alpha=0.3)
fig.tight_layout()
save(fig, "exp9_nucleos")

print(f"\n✅ Todos os gráficos salvos em: {PLOTS}")
print(f"   Arquivos: {len(list(PLOTS.glob('*.pdf')))} PDFs + {len(list(PLOTS.glob('*.png')))} PNGs")
