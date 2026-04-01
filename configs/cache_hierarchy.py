# cache_hierarchy.py — gem5 v25.1, build ALL

import argparse
import m5
from m5.objects import *
from m5.util import addToPath

addToPath("../")

parser = argparse.ArgumentParser(description="Hierarquia de cache — gem5 v25.1")

parser.add_argument("--cpu", default="X86O3CPU",
    choices=["X86TimingSimpleCPU", "X86MinorCPU", "X86O3CPU"])
parser.add_argument("--num-cores",    type=int, default=1)
parser.add_argument("--l1d-size",     default="32kB")
parser.add_argument("--l1i-size",     default="32kB")
parser.add_argument("--l1d-assoc",    type=int, default=4)
parser.add_argument("--l1i-assoc",    type=int, default=4)
parser.add_argument("--l1-line-size", type=int, default=64)
parser.add_argument("--repl-policy",  default="lru",
    choices=["lru", "random", "fifo"])
parser.add_argument("--write-policy", default="writeback",
    choices=["writeback", "writethrough"])
parser.add_argument("--enable-l2",    action="store_true", default=False)
parser.add_argument("--l2-size",      default="256kB")
parser.add_argument("--l2-assoc",     type=int, default=8)
parser.add_argument("--l2-latency",   type=int, default=20)
parser.add_argument("--prefetcher",   default="none",
    choices=["none", "stride", "tagged"])
parser.add_argument("--mem-type",     default="DDR4_2400_8x8",
    choices=["DDR3_1600_8x8", "DDR4_2400_8x8", "DDR5_4400_4x8"])
parser.add_argument("--binary",       required=True)
parser.add_argument("--binary-args",  nargs="*", default=[])

args = parser.parse_args()

# ── Política de substituição ──────────────────────────────
repl_map = {"lru": LRURP(), "random": RandomRP(), "fifo": FIFORP()}
repl = repl_map[args.repl_policy]

# ── Prefetcher ────────────────────────────────────────────
def make_prefetcher(kind):
    if kind == "stride": return StridePrefetcher()
    if kind == "tagged": return TaggedPrefetcher()
    return NULL

# ── Sistema ───────────────────────────────────────────────
system = System()
system.mem_mode        = "timing"
system.mem_ranges      = [AddrRange("512MiB")]
system.cache_line_size = args.l1_line_size
system.clk_domain      = SrcClockDomain(
    clock="3GHz",
    voltage_domain=VoltageDomain(voltage="1V")
)

# ── CPUs ──────────────────────────────────────────────────
cpu_class = {
    "X86TimingSimpleCPU": X86TimingSimpleCPU,
    "X86MinorCPU":        X86MinorCPU,
    "X86O3CPU":           X86O3CPU,
}[args.cpu]
system.cpu = [cpu_class(cpu_id=i) for i in range(args.num_cores)]

# ── Barramento principal ───────────────────────────────────
system.membus = SystemXBar()

# ── Cache L1 ─────────────────────────────────────────
def make_l1(size, assoc, is_dcache=False):
    kwargs = dict(
        size=size, assoc=assoc,
        tag_latency=4, data_latency=4, response_latency=1,
        mshrs=16, tgts_per_mshr=20,
        replacement_policy=repl,
        clusivity="mostly_incl",
    )
    # Política de escrita -> write-through desabilita write buffer
    if args.write_policy == "writethrough":
        kwargs["write_buffers"] = 0
    # Prefetcher só na dcache
    if is_dcache and args.prefetcher != "none":
        kwargs["prefetcher"] = make_prefetcher(args.prefetcher)
    return Cache(**kwargs)

# ── L2 compartilhado (opcional) ───────────────────────────
if args.enable_l2:
    system.l2bus = L2XBar()
    system.l2cache = Cache(
        size=args.l2_size, assoc=args.l2_assoc,
        tag_latency=args.l2_latency,
        data_latency=args.l2_latency,
        response_latency=1,
        mshrs=32, tgts_per_mshr=12,
        replacement_policy=LRURP(),
        clusivity="mostly_incl",
    )
    system.l2cache.cpu_side = system.l2bus.mem_side_ports
    system.l2cache.mem_side = system.membus.cpu_side_ports

# ── Conecta cada CPU ──────────────────────────────────────
for cpu in system.cpu:
    cpu.icache = make_l1(args.l1i_size, args.l1i_assoc, is_dcache=False)
    cpu.dcache = make_l1(args.l1d_size, args.l1d_assoc, is_dcache=True)
    cpu.icache_port = cpu.icache.cpu_side
    cpu.dcache_port = cpu.dcache.cpu_side

    if args.enable_l2:
        cpu.icache.mem_side = system.l2bus.cpu_side_ports
        cpu.dcache.mem_side = system.l2bus.cpu_side_ports
    else:
        cpu.icache.mem_side = system.membus.cpu_side_ports
        cpu.dcache.mem_side = system.membus.cpu_side_ports

    cpu.createInterruptController()
    cpu.interrupts[0].pio           = system.membus.mem_side_ports
    cpu.interrupts[0].int_requestor = system.membus.cpu_side_ports
    cpu.interrupts[0].int_responder = system.membus.mem_side_ports

system.system_port = system.membus.cpu_side_ports

# ── Memória principal ─────────────────────────────────────
mem_class = {
    "DDR3_1600_8x8": DDR3_1600_8x8,
    "DDR4_2400_8x8": DDR4_2400_8x8,
    "DDR5_4400_4x8": DDR5_4400_4x8,
}[args.mem_type]

system.mem_ctrl      = MemCtrl()
system.mem_ctrl.dram = mem_class()
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports

# ── Workload ──────────────────────────────────────────────
system.workload = SEWorkload.init_compatible(args.binary)

process = Process()
process.cmd = [args.binary] + (args.binary_args or [])

for cpu in system.cpu:
    cpu.workload = process
    cpu.createThreads()

# ── Instancia e roda ──────────────────────────────────────
root = Root(full_system=False, system=system)
m5.instantiate()

print(f"\n[gem5] CPU: {args.cpu} x{args.num_cores}")
print(f"[gem5] L1D: {args.l1d_size} {args.l1d_assoc}-way | "
      f"line={args.l1_line_size}B | repl={args.repl_policy} | write={args.write_policy}")
print(f"[gem5] L2:  {'habilitado ' + args.l2_size if args.enable_l2 else 'desabilitado'}")
print(f"[gem5] Mem: {args.mem_type} | Prefetcher: {args.prefetcher}")
print(f"[gem5] Bin: {args.binary} {' '.join(args.binary_args or [])}\n")

exit_event = m5.simulate()
print(f"\n[gem5] Saiu: {exit_event.getCause()}\n")
