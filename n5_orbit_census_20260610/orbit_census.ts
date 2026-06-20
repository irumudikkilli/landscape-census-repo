type StatePermutation = Uint8Array;

type GroupData = {
  n: number;
  nStates: number;
  nBytes: number;
  order: number;
  perms: StatePermutation[];
  table: Uint32Array;
};

function usage(): never {
  console.error(`usage:
  bun orbit_census.ts burnside <n>
  bun orbit_census.ts full <n> [reps.bin]
  bun orbit_census.ts bench-transform <n> [regions]
  bun orbit_census.ts scan-prefix <n> <limit>
`);
  process.exit(2);
}

function* permutations(items: number[]): Generator<number[]> {
  if (items.length === 0) {
    yield [];
    return;
  }
  for (let i = 0; i < items.length; i++) {
    const head = items[i];
    const rest = items.slice(0, i).concat(items.slice(i + 1));
    for (const tail of permutations(rest)) {
      yield [head, ...tail];
    }
  }
}

function buildStatePermutations(n: number): StatePermutation[] {
  const nStates = 1 << n;
  const out: StatePermutation[] = [];
  for (const perm of permutations(Array.from({ length: n }, (_, i) => i))) {
    for (let flips = 0; flips < (1 << n); flips++) {
      const sp = new Uint8Array(nStates);
      for (let s = 0; s < nStates; s++) {
        let t = 0;
        for (let i = 0; i < n; i++) {
          const bit = ((s >>> i) & 1) ^ ((flips >>> i) & 1);
          if (bit) t |= 1 << perm[i];
        }
        sp[s] = t;
      }
      out.push(sp);
    }
  }
  return out;
}

function buildGroup(n: number): GroupData {
  if (n < 1 || n > 5) throw new Error("this prototype supports 1 <= n <= 5");
  const nStates = 1 << n;
  const nBytes = nStates >>> 3;
  const perms = buildStatePermutations(n);
  const table = new Uint32Array(perms.length * nBytes * 256);
  for (let g = 0; g < perms.length; g++) {
    const sp = perms[g];
    for (let pos = 0; pos < nBytes; pos++) {
      for (let val = 0; val < 256; val++) {
        let image = 0;
        for (let b = 0; b < 8; b++) {
          if ((val >>> b) & 1) {
            const state = pos * 8 + b;
            image = (image | (1 << sp[state])) >>> 0;
          }
        }
        table[((g * nBytes + pos) << 8) + val] = image >>> 0;
      }
    }
  }
  return { n, nStates, nBytes, order: perms.length, perms, table };
}

function transformRegion(group: GroupData, g: number, region: number): number {
  const { nBytes, table } = group;
  let out = 0;
  let r = region >>> 0;
  for (let pos = 0; pos < nBytes; pos++) {
    out = (out | table[((g * nBytes + pos) << 8) + (r & 255)]) >>> 0;
    r = r >>> 8;
  }
  return out >>> 0;
}

function countCycles(sp: StatePermutation): number {
  const seen = new Uint8Array(sp.length);
  let cycles = 0;
  for (let i = 0; i < sp.length; i++) {
    if (seen[i]) continue;
    cycles++;
    let j = i;
    while (!seen[j]) {
      seen[j] = 1;
      j = sp[j];
    }
  }
  return cycles;
}

function burnside(n: number): bigint {
  const perms = buildStatePermutations(n);
  const distribution = new Map<number, number>();
  let sum = 0n;
  for (const sp of perms) {
    const c = countCycles(sp);
    distribution.set(c, (distribution.get(c) ?? 0) + 1);
    sum += 1n << BigInt(c);
  }
  const orbits = sum / BigInt(perms.length);
  console.log(JSON.stringify({
    n,
    groupOrder: perms.length,
    cycleDistribution: Object.fromEntries([...distribution.entries()].sort((a, b) => a[0] - b[0])),
    regionOrbits: orbits.toString(),
    fullRegions: (1n << BigInt(1 << n)).toString(),
  }, null, 2));
  return orbits;
}

function bitIsSet(bits: Uint8Array, r: number): boolean {
  return (bits[r >>> 3] & (1 << (r & 7))) !== 0;
}

function bitSet(bits: Uint8Array, r: number): boolean {
  const i = r >>> 3;
  const mask = 1 << (r & 7);
  const old = bits[i];
  if ((old & mask) !== 0) return false;
  bits[i] = old | mask;
  return true;
}

function now(): number {
  return performance.now() / 1000;
}

function fullScan(n: number, outPath?: string, limit?: number): void {
  const t0 = now();
  const group = buildGroup(n);
  const totalRegions = 2 ** group.nStates;
  const stop = limit === undefined ? totalRegions : Math.min(limit, totalRegions);
  const bitBytes = totalRegions / 8;
  console.log(JSON.stringify({
    event: "start",
    n,
    totalRegions,
    stop,
    groupOrder: group.order,
    bitBytes,
    tableBytes: group.table.byteLength,
  }));
  const bits = new Uint8Array(bitBytes);
  const reps: number[] = [];
  let transforms = 0;
  let marked = 0;
  let last = now();
  for (let r = 0; r < stop; r++) {
    if (bitIsSet(bits, r)) continue;
    let min = 0xffffffff;
    const images = new Uint32Array(group.order);
    for (let g = 0; g < group.order; g++) {
      const img = transformRegion(group, g, r);
      images[g] = img;
      if (img < min) min = img;
    }
    transforms += group.order;
    reps.push(min >>> 0);
    for (let i = 0; i < images.length; i++) {
      if (bitSet(bits, images[i])) marked++;
    }
    const t = now();
    if (t - last >= 5) {
      console.log(JSON.stringify({
        event: "progress",
        r,
        reps: reps.length,
        marked,
        elapsed: t - t0,
        regionsPerSecond: r / Math.max(1e-9, t - t0),
        transformsPerSecond: transforms / Math.max(1e-9, t - t0),
      }));
      last = t;
    }
  }
  const elapsed = now() - t0;
  console.log(JSON.stringify({
    event: "done",
    n,
    scanned: stop,
    reps: reps.length,
    marked,
    elapsed,
    regionsPerSecond: stop / elapsed,
    transforms,
    transformsPerSecond: transforms / elapsed,
  }, null, 2));
  if (outPath) {
    const buf = Buffer.allocUnsafe(reps.length * 4);
    for (let i = 0; i < reps.length; i++) buf.writeUInt32LE(reps[i] >>> 0, i * 4);
    Bun.write(outPath, buf);
    console.log(JSON.stringify({ event: "wrote", outPath, bytes: buf.byteLength }));
  }
}

function benchTransform(n: number, regions = 20_000): void {
  const t0 = now();
  const group = buildGroup(n);
  const buildElapsed = now() - t0;
  let x = 0x9e3779b9 >>> 0;
  let checksum = 0;
  const t1 = now();
  for (let i = 0; i < regions; i++) {
    x = (Math.imul(x, 1664525) + 1013904223) >>> 0;
    for (let g = 0; g < group.order; g++) {
      checksum = (checksum ^ transformRegion(group, g, x)) >>> 0;
    }
  }
  const elapsed = now() - t1;
  const transforms = regions * group.order;
  console.log(JSON.stringify({
    n,
    regions,
    groupOrder: group.order,
    buildElapsed,
    elapsed,
    transforms,
    transformsPerSecond: transforms / elapsed,
    checksum,
  }, null, 2));
}

const [cmd, nRaw, arg] = process.argv.slice(2);
if (!cmd) usage();
const n = Number(nRaw);
if (!Number.isInteger(n)) usage();

if (cmd === "burnside") {
  burnside(n);
} else if (cmd === "full") {
  fullScan(n, arg);
} else if (cmd === "bench-transform") {
  benchTransform(n, arg ? Number(arg) : 20_000);
} else if (cmd === "scan-prefix") {
  const limit = Number(arg);
  if (!Number.isFinite(limit) || limit <= 0) usage();
  fullScan(n, undefined, limit);
} else {
  usage();
}
