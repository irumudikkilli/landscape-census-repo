use std::collections::BTreeMap;
use std::env;
use std::fs::File;
use std::io::{BufWriter, Write};
use std::time::Instant;

type StatePermutation = Vec<u8>;

struct GroupData {
    n: usize,
    n_states: usize,
    n_bytes: usize,
    order: usize,
    table: Vec<u32>,
}

fn usage() -> ! {
    eprintln!(
        "usage:
  orbit-census burnside <n>
  orbit-census full <n> [reps.bin]
  orbit-census bench-transform <n> [regions]
  orbit-census scan-prefix <n> <limit>"
    );
    std::process::exit(2);
}

fn parse_usize(s: Option<&String>) -> usize {
    s.and_then(|v| v.parse::<usize>().ok())
        .unwrap_or_else(|| usage())
}

fn parse_u64(s: Option<&String>) -> u64 {
    s.and_then(|v| v.parse::<u64>().ok())
        .unwrap_or_else(|| usage())
}

fn collect_permutations(items: &mut [usize], start: usize, out: &mut Vec<Vec<usize>>) {
    if start == items.len() {
        out.push(items.to_vec());
        return;
    }
    for i in start..items.len() {
        items.swap(start, i);
        collect_permutations(items, start + 1, out);
        items.swap(start, i);
    }
}

fn coordinate_permutations(n: usize) -> Vec<Vec<usize>> {
    let mut items: Vec<usize> = (0..n).collect();
    let mut out = Vec::new();
    collect_permutations(&mut items, 0, &mut out);
    out
}

fn build_state_permutations(n: usize) -> Vec<StatePermutation> {
    if !(1..=5).contains(&n) {
        panic!("this helper supports 1 <= n <= 5");
    }
    let n_states = 1usize << n;
    let mut out = Vec::new();
    for perm in coordinate_permutations(n) {
        for flips in 0..(1usize << n) {
            let mut sp = vec![0u8; n_states];
            for (s, target) in sp.iter_mut().enumerate() {
                let mut t = 0usize;
                for (i, &p_i) in perm.iter().enumerate() {
                    let bit = ((s >> i) & 1) ^ ((flips >> i) & 1);
                    if bit != 0 {
                        t |= 1usize << p_i;
                    }
                }
                *target = t as u8;
            }
            out.push(sp);
        }
    }
    out
}

fn build_group(n: usize) -> GroupData {
    let n_states = 1usize << n;
    let n_bytes = n_states.div_ceil(8);
    let perms = build_state_permutations(n);
    let mut table = vec![0u32; perms.len() * n_bytes * 256];
    for (g, sp) in perms.iter().enumerate() {
        for pos in 0..n_bytes {
            for val in 0..256usize {
                let mut image = 0u32;
                for b in 0..8usize {
                    let state = pos * 8 + b;
                    if state < n_states && ((val >> b) & 1) != 0 {
                        image |= 1u32 << sp[state];
                    }
                }
                table[((g * n_bytes + pos) << 8) + val] = image;
            }
        }
    }
    let order = perms.len();
    GroupData {
        n,
        n_states,
        n_bytes,
        order,
        table,
    }
}

#[inline(always)]
fn transform_region(group: &GroupData, g: usize, region: u32) -> u32 {
    let mut out = 0u32;
    let mut r = region;
    for pos in 0..group.n_bytes {
        out |= group.table[((g * group.n_bytes + pos) << 8) + ((r & 255) as usize)];
        r >>= 8;
    }
    out
}

fn count_cycles(sp: &StatePermutation) -> usize {
    let mut seen = vec![false; sp.len()];
    let mut cycles = 0usize;
    for i in 0..sp.len() {
        if seen[i] {
            continue;
        }
        cycles += 1;
        let mut j = i;
        while !seen[j] {
            seen[j] = true;
            j = sp[j] as usize;
        }
    }
    cycles
}

fn burnside(n: usize) {
    let perms = build_state_permutations(n);
    let mut distribution: BTreeMap<usize, usize> = BTreeMap::new();
    let mut sum = 0u128;
    for sp in &perms {
        let c = count_cycles(sp);
        *distribution.entry(c).or_insert(0) += 1;
        sum += 1u128 << c;
    }
    let orbits = sum / (perms.len() as u128);
    println!("{{");
    println!("  \"n\": {},", n);
    println!("  \"groupOrder\": {},", perms.len());
    println!("  \"cycleDistribution\": {{");
    for (i, (cycles, count)) in distribution.iter().enumerate() {
        let comma = if i + 1 == distribution.len() { "" } else { "," };
        println!("    \"{}\": {}{}", cycles, count, comma);
    }
    println!("  }},");
    println!("  \"regionOrbits\": \"{}\",", orbits);
    println!("  \"fullRegions\": \"{}\"", 1u128 << (1usize << n));
    println!("}}");
}

#[inline(always)]
fn bit_is_set(bits: &[u8], r: u64) -> bool {
    (bits[(r >> 3) as usize] & (1u8 << (r & 7))) != 0
}

#[inline(always)]
fn bit_set(bits: &mut [u8], r: u32) -> bool {
    let i = (r >> 3) as usize;
    let mask = 1u8 << (r & 7);
    let old = bits[i];
    if (old & mask) != 0 {
        return false;
    }
    bits[i] = old | mask;
    true
}

fn full_scan(n: usize, out_path: Option<&String>, limit: Option<u64>) -> std::io::Result<()> {
    let t0 = Instant::now();
    let group = build_group(n);
    let total_regions = 1u64 << group.n_states;
    let stop = limit.unwrap_or(total_regions).min(total_regions);
    let bit_bytes = (total_regions / 8) as usize;
    println!(
        "{{\"event\":\"start\",\"n\":{},\"totalRegions\":{},\"stop\":{},\"groupOrder\":{},\"bitBytes\":{},\"tableBytes\":{}}}",
        group.n,
        total_regions,
        stop,
        group.order,
        bit_bytes,
        group.table.len() * std::mem::size_of::<u32>()
    );

    let mut bits = vec![0u8; bit_bytes];
    let mut reps = Vec::<u32>::new();
    let mut images = vec![0u32; group.order];
    let mut transforms = 0u64;
    let mut marked = 0u64;
    let mut last = Instant::now();

    for r in 0..stop {
        if bit_is_set(&bits, r) {
            continue;
        }
        let r32 = r as u32;
        let mut min = u32::MAX;
        for (g, image_slot) in images.iter_mut().enumerate() {
            let img = transform_region(&group, g, r32);
            *image_slot = img;
            if img < min {
                min = img;
            }
        }
        transforms += group.order as u64;
        reps.push(min);
        for &img in &images {
            if bit_set(&mut bits, img) {
                marked += 1;
            }
        }

        let elapsed = t0.elapsed().as_secs_f64();
        if last.elapsed().as_secs_f64() >= 5.0 {
            println!(
                "{{\"event\":\"progress\",\"r\":{},\"reps\":{},\"marked\":{},\"elapsed\":{},\"regionsPerSecond\":{},\"transformsPerSecond\":{}}}",
                r,
                reps.len(),
                marked,
                elapsed,
                (r as f64) / elapsed.max(1e-9),
                (transforms as f64) / elapsed.max(1e-9)
            );
            last = Instant::now();
        }
    }

    let elapsed = t0.elapsed().as_secs_f64();
    println!("{{");
    println!("  \"event\": \"done\",");
    println!("  \"n\": {},", group.n);
    println!("  \"scanned\": {},", stop);
    println!("  \"reps\": {},", reps.len());
    println!("  \"marked\": {},", marked);
    println!("  \"elapsed\": {},", elapsed);
    println!("  \"regionsPerSecond\": {},", (stop as f64) / elapsed);
    println!("  \"transforms\": {},", transforms);
    println!(
        "  \"transformsPerSecond\": {}",
        (transforms as f64) / elapsed
    );
    println!("}}");

    if let Some(path) = out_path {
        let file = File::create(path)?;
        let mut writer = BufWriter::new(file);
        for rep in reps {
            writer.write_all(&rep.to_le_bytes())?;
        }
        writer.flush()?;
        println!(
            "{{\"event\":\"wrote\",\"outPath\":\"{}\",\"bytes\":{}}}",
            path,
            std::fs::metadata(path)?.len()
        );
    }
    Ok(())
}

fn bench_transform(n: usize, regions: u64) {
    let t0 = Instant::now();
    let group = build_group(n);
    let build_elapsed = t0.elapsed().as_secs_f64();
    let mut x = 0x9e37_79b9u32;
    let mut checksum = 0u32;
    let t1 = Instant::now();
    for _ in 0..regions {
        x = x.wrapping_mul(1_664_525).wrapping_add(1_013_904_223);
        for g in 0..group.order {
            checksum ^= transform_region(&group, g, x);
        }
    }
    let elapsed = t1.elapsed().as_secs_f64();
    let transforms = regions * (group.order as u64);
    println!("{{");
    println!("  \"n\": {},", n);
    println!("  \"regions\": {},", regions);
    println!("  \"groupOrder\": {},", group.order);
    println!("  \"buildElapsed\": {},", build_elapsed);
    println!("  \"elapsed\": {},", elapsed);
    println!("  \"transforms\": {},", transforms);
    println!(
        "  \"transformsPerSecond\": {},",
        (transforms as f64) / elapsed
    );
    println!("  \"checksum\": {}", checksum);
    println!("}}");
}

fn main() -> std::io::Result<()> {
    let args: Vec<String> = env::args().collect();
    let cmd = args.get(1).unwrap_or_else(|| usage());
    let n = parse_usize(args.get(2));
    match cmd.as_str() {
        "burnside" => burnside(n),
        "full" => full_scan(n, args.get(3), None)?,
        "bench-transform" => {
            let regions = args
                .get(3)
                .and_then(|v| v.parse::<u64>().ok())
                .unwrap_or(20_000);
            bench_transform(n, regions);
        }
        "scan-prefix" => {
            let limit = parse_u64(args.get(3));
            if limit == 0 {
                usage();
            }
            full_scan(n, None, Some(limit))?;
        }
        _ => usage(),
    }
    Ok(())
}
