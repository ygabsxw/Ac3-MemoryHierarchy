#!/bin/bash
# run_experiments.sh — gem5 v25.1, build ALL, X86O3CPU
# Working set: 64MB (~25-30min/run) 
#
# Uso:
#   bash scripts/run_experiments.sh noite1   (EXP1+EXP2)
#   bash scripts/run_experiments.sh noite2   (EXP3+EXP4+EXP5)
#   bash scripts/run_experiments.sh noite3   (EXP6+EXP7+EXP8+EXP9)

GEM5=./build/ALL/gem5.opt
CFG=configs/cache_hierarchy.py
HEAVY=./workloads/cache_stress_heavy
MIBENCH=./mibench
THREADS=./tests/test-progs/threads/bin/x86/linux/threads
MAX_JOBS=6
WS=64

mkdir -p results logs
LOG=logs/run_$(date '+%Y%m%d_%H%M%S').log

log() { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"; }

PIDS=()
TOTAL=0

run() {
    local OUTDIR="$1"; shift
    # Pula se já existe resultado válido — permite re-run seguro
    if [ -f "$OUTDIR/stats.txt" ] && [ "$(wc -l < $OUTDIR/stats.txt)" -gt 200 ]; then
        log "[SKIP] já existe: $OUTDIR"
        return
    fi
    while [ ${#PIDS[@]} -ge $MAX_JOBS ]; do
        local NEW=()
        for P in "${PIDS[@]}"; do
            kill -0 "$P" 2>/dev/null && NEW+=("$P")
        done
        PIDS=("${NEW[@]}")
        sleep 15
    done
    mkdir -p "$OUTDIR"
    $GEM5 --outdir="$OUTDIR" "$CFG" --cpu=X86O3CPU "$@" >> "$LOG" 2>&1 &
    PIDS+=($!)
    TOTAL=$((TOTAL+1))
    log "[$TOTAL] $OUTDIR (PID ${PIDS[-1]})"
}

wait_all() {
    log "Aguardando ${#PIDS[@]} simulações..."
    wait; PIDS=()
    log "Bloco concluído."
}

check() {
    local PREFIX="$1" FAIL=0 OK=0
    for f in results/${PREFIX}*/stats.txt; do
        [ -f "$f" ] || continue
        lines=$(wc -l < "$f")
        if [ "$lines" -lt 200 ]; then
            log "FALHOU ($lines linhas): $f"
            FAIL=$((FAIL+1))
        else
            OK=$((OK+1))
        fi
    done
    log "Resultado ${PREFIX}*: $OK OK, $FAIL falhas"
}

done_notify() {
    log "=== $1 CONCLUIDA — $(date) ==="
    notify-send "gem5" "$1 concluida!" 2>/dev/null || true
    paplay /usr/share/sounds/freedesktop/stereo/complete.oga 2>/dev/null || true
}

# ════════════════════════════════════════════════════════════
# NOITE 1 — EXP1: tamanho de cache + EXP2: associatividade
# Tamanho de cache e associatividade
# ════════════════════════════════════════════════════════════
noite1() {
    log "=== NOITE 1: EXP1 (tamanho L1) + EXP2 (associatividade) ==="

    log "--- EXP1a: tamanho de L1 — microbenchmark ---"
    for SIZE in 4kB 8kB 16kB 32kB 64kB 128kB 256kB; do
        run results/exp1_seq_${SIZE}    --binary=$HEAVY --binary-args seq    $WS    --l1d-size=$SIZE --l1d-assoc=4
        run results/exp1_rand_${SIZE}   --binary=$HEAVY --binary-args rand   $WS    --l1d-size=$SIZE --l1d-assoc=4
        run results/exp1_stride_${SIZE} --binary=$HEAVY --binary-args stride $WS 64 --l1d-size=$SIZE --l1d-assoc=4
    done

    log "--- EXP1b: tamanho de L1 — MiBench ---"
    for SIZE in 8kB 16kB 32kB 64kB 128kB; do
        run results/exp1_basicmath_${SIZE} \
            --binary=$MIBENCH/automotive/basicmath/basicmath_small \
            --l1d-size=$SIZE --l1d-assoc=4
        run results/exp1_dijkstra_${SIZE} \
            --binary=$MIBENCH/network/dijkstra/dijkstra_small \
            --binary-args "$MIBENCH/network/dijkstra/input.dat" \
            --l1d-size=$SIZE --l1d-assoc=4
    done

    wait_all
    check "exp1_"

    log "--- EXP2: associatividade (L1=32kB fixo) ---"
    for ASSOC in 1 2 4 8 16; do
        run results/exp2_seq_${ASSOC}way  --binary=$HEAVY --binary-args seq  $WS --l1d-size=32kB --l1d-assoc=$ASSOC
        run results/exp2_rand_${ASSOC}way --binary=$HEAVY --binary-args rand $WS --l1d-size=32kB --l1d-assoc=$ASSOC
    done
    wait_all
    check "exp2_"

    done_notify "NOITE 1"
}

# ════════════════════════════════════════════════════════════
# NOITE 2 — EXP3: níveis de cache + EXP4: latência de memória + EXP5: tamanho de linha
# Níveis de cache, latência de memória, tamanho de linha
# ════════════════════════════════════════════════════════════
noite2() {
    log "=== NOITE 2: EXP3 (hierarquia) + EXP4 (memória) + EXP5 (cache line) ==="

    log "--- EXP3: níveis de cache — L1 vs L1+L2 ---"
    for MODE in seq rand; do
        run results/exp3_${MODE}_no_l2    --binary=$HEAVY --binary-args $MODE $WS --l1d-size=32kB
        run results/exp3_${MODE}_l2_256kB --binary=$HEAVY --binary-args $MODE $WS --l1d-size=32kB --enable-l2 --l2-size=256kB
        run results/exp3_${MODE}_l2_1MB   --binary=$HEAVY --binary-args $MODE $WS --l1d-size=32kB --enable-l2 --l2-size=1MB
        run results/exp3_${MODE}_l2_4MB   --binary=$HEAVY --binary-args $MODE $WS --l1d-size=32kB --enable-l2 --l2-size=4MB
        run results/exp3_${MODE}_l1_256kB --binary=$HEAVY --binary-args $MODE $WS --l1d-size=256kB
    done
    wait_all
    check "exp3_"

    log "--- EXP4: latência de memória — DDR3 vs DDR4 vs DDR5 ---"
    for MEM in DDR3_1600_8x8 DDR4_2400_8x8 DDR5_4400_4x8; do
        run results/exp4_seq_${MEM}  --binary=$HEAVY --binary-args seq  $WS --l1d-size=32kB --mem-type=$MEM
        run results/exp4_rand_${MEM} --binary=$HEAVY --binary-args rand $WS --l1d-size=32kB --mem-type=$MEM
    done
    wait_all
    check "exp4_"

    log "--- EXP5: tamanho de cache line ---"
    for LSIZE in 16 32 64 128 256; do
        run results/exp5_seq_line${LSIZE}    --binary=$HEAVY --binary-args seq    $WS        --l1d-size=32kB --l1-line-size=$LSIZE
        run results/exp5_stride_line${LSIZE} --binary=$HEAVY --binary-args stride $WS $LSIZE --l1d-size=32kB --l1-line-size=$LSIZE
        run results/exp5_rand_line${LSIZE}   --binary=$HEAVY --binary-args rand   $WS        --l1d-size=32kB --l1-line-size=$LSIZE
    done
    wait_all
    check "exp5_"

    done_notify "NOITE 2"
}

# ════════════════════════════════════════════════════════════
# NOITE 3 — EXP6: substituição + EXP7: política de escrita + EXP8: prefetchers + EXP9: número de núcleos
# Políticas de substituição, políticas de escrita, prefetchers, número de núcleos
# ════════════════════════════════════════════════════════════
noite3() {
    log "=== NOITE 3: EXP6 (subst.) + EXP7 (escrita) + EXP8 (prefetch) + EXP9 (cores) ==="

    log "--- EXP6: política de substituição (L1=16kB, pressão alta) ---"
    for POLICY in lru random fifo; do
        run results/exp6_seq_${POLICY}    --binary=$HEAVY --binary-args seq    $WS    --l1d-size=16kB --repl-policy=$POLICY
        run results/exp6_rand_${POLICY}   --binary=$HEAVY --binary-args rand   $WS    --l1d-size=16kB --repl-policy=$POLICY
        run results/exp6_stride_${POLICY} --binary=$HEAVY --binary-args stride $WS 64 --l1d-size=16kB --repl-policy=$POLICY
    done
    wait_all
    check "exp6_"

    log "--- EXP7: política de escrita — write-back vs write-through ---"
    for WP in writeback writethrough; do
        run results/exp7_seq_${WP}    --binary=$HEAVY --binary-args seq    $WS    --l1d-size=32kB --write-policy=$WP
        run results/exp7_rand_${WP}   --binary=$HEAVY --binary-args rand   $WS    --l1d-size=32kB --write-policy=$WP
        run results/exp7_stride_${WP} --binary=$HEAVY --binary-args stride $WS 64 --l1d-size=32kB --write-policy=$WP
    done
    wait_all
    check "exp7_"

    log "--- EXP8: prefetchers — none vs stride vs tagged ---"
    for PF in none stride tagged; do
        run results/exp8_seq_${PF}    --binary=$HEAVY --binary-args seq    $WS    --l1d-size=32kB --prefetcher=$PF
        run results/exp8_stride_${PF} --binary=$HEAVY --binary-args stride $WS 64 --l1d-size=32kB --prefetcher=$PF
        run results/exp8_rand_${PF}   --binary=$HEAVY --binary-args rand   $WS    --l1d-size=32kB --prefetcher=$PF
    done
    wait_all
    check "exp8_"

    log "--- EXP9: número de núcleos — 1/2/4 cores com L2 compartilhado ---"
    for NCORES in 1 2 4; do
        run results/exp9_${NCORES}core \
            --binary=$THREADS \
            --binary-args $NCORES \
            --l1d-size=32kB --enable-l2 --l2-size=1MB \
            --num-cores=$NCORES
    done
    wait_all
    check "exp9_"

    done_notify "NOITE 3"
}

case "${1:-}" in
    noite1) noite1 ;;
    noite2) noite2 ;;
    noite3) noite3 ;;
    tudo)   noite1; noite2; noite3 ;;
    *)
        echo "Uso: bash scripts/run_experiments.sh [noite1|noite2|noite3|tudo]"
        echo ""
        echo "  noite1 — EXP1 tamanho de cache (micro+MiBench) + EXP2 associatividade"
        echo "  noite2 — EXP3 niveis de cache + EXP4 latencia de memoria + EXP5 cache line"
        echo "  noite3 — EXP6 substituicao + EXP7 escrita + EXP8 prefetcher + EXP9 nucleos"
        echo ""
        echo "  Working set: ${WS}MB | CPU: X86O3CPU | Paralelo: $MAX_JOBS jobs"
        exit 1
        ;;
esac
