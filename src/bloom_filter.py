"""
ProductPilot - Bloom Filter Implementation
==========================================
A working Bloom Filter implementation for screening feature request IDs
for potential duplicates. Uses deterministic hashing for reproducibility.

IMPORTANT: A Bloom Filter can produce false positives but NEVER false negatives.
A positive result means "possibly exists" and must be verified against the
exact database. A negative result means "definitely does not exist."
"""

import math
import hashlib
import sys


class BloomFilter:
    """
    Probabilistic data structure for approximate set membership.

    Parameters
    ----------
    size : int
        Size of the bit array in bits.
    num_hashes : int
        Number of hash functions to use.
    """

    def __init__(self, size=1000, num_hashes=3):
        if size < 1:
            raise ValueError("Bit array size must be >= 1")
        if num_hashes < 1:
            raise ValueError("Number of hash functions must be >= 1")

        self.size = size
        self.num_hashes = num_hashes
        self.bit_array = [0] * size
        self.item_count = 0

    def _hashes(self, item):
        """
        Generate `num_hashes` deterministic hash positions for an item.
        Uses double-hashing technique with SHA-256 and MD5 for determinism.
        """
        item_str = str(item).encode("utf-8")
        h1 = int(hashlib.sha256(item_str).hexdigest(), 16)
        h2 = int(hashlib.md5(item_str).hexdigest(), 16)

        positions = []
        for i in range(self.num_hashes):
            pos = (h1 + i * h2) % self.size
            positions.append(pos)
        return positions

    def insert(self, item):
        """Insert an item into the Bloom Filter."""
        for pos in self._hashes(item):
            self.bit_array[pos] = 1
        self.item_count += 1

    def lookup(self, item):
        """
        Check if an item MIGHT be in the set.

        Returns True if the item is POSSIBLY in the set (may be false positive).
        Returns False if the item is DEFINITELY NOT in the set.
        """
        for pos in self._hashes(item):
            if self.bit_array[pos] == 0:
                return False
        return True

    def fill_ratio(self):
        """Fraction of bits that are set to 1."""
        return sum(self.bit_array) / self.size

    def memory_bytes(self):
        """Approximate memory usage of the bit array in bytes."""
        # Python list of ints — each int is ~28 bytes in CPython
        # For comparison purposes, we report the theoretical bit array size
        return self.size / 8  # Ideal bit-packed size

    def expected_false_positive_rate(self):
        """
        Theoretical false positive probability after inserting `item_count` items.
        Formula: (1 - e^(-k*n/m))^k
        """
        if self.item_count == 0:
            return 0.0
        k = self.num_hashes
        n = self.item_count
        m = self.size
        return (1 - math.exp(-k * n / m)) ** k

    def get_bit_array_summary(self):
        """Return a summary of the bit array state."""
        total_bits = self.size
        set_bits = sum(self.bit_array)
        return {
            "total_bits": total_bits,
            "set_bits": set_bits,
            "unset_bits": total_bits - set_bits,
            "fill_ratio": round(set_bits / total_bits, 4),
            "items_inserted": self.item_count,
        }

    def get_bit_array_visual(self, max_display=200):
        """Return a visual string representation of the bit array."""
        if self.size <= max_display:
            return "".join(str(b) for b in self.bit_array)
        # Show first and last portions
        portion = max_display // 2
        head = "".join(str(b) for b in self.bit_array[:portion])
        tail = "".join(str(b) for b in self.bit_array[-portion:])
        return f"{head} ... ({self.size - max_display} bits omitted) ... {tail}"


def evaluate_bloom_filter(inserted_ids, test_existing, test_new, size=10000, num_hashes=5):
    """
    Run a complete Bloom Filter evaluation.

    Parameters
    ----------
    inserted_ids : list
        IDs to insert into the filter.
    test_existing : list
        IDs that ARE in the filter (should all return True).
    test_new : list
        IDs that are NOT in the filter (True results = false positives).
    size : int
        Bit array size.
    num_hashes : int
        Number of hash functions.

    Returns
    -------
    dict
        Evaluation results including false positive count and rate.
    """
    bf = BloomFilter(size=size, num_hashes=num_hashes)

    # Insert all IDs
    for item in inserted_ids:
        bf.insert(item)

    # Test existing IDs (should all be True — no false negatives)
    true_positives = 0
    false_negatives = 0
    for item in test_existing:
        if bf.lookup(item):
            true_positives += 1
        else:
            false_negatives += 1  # Should NEVER happen

    # Test new IDs (True = false positive)
    false_positives = 0
    true_negatives = 0
    for item in test_new:
        if bf.lookup(item):
            false_positives += 1
        else:
            true_negatives += 1

    # Exact set comparison
    exact_set = set(str(x) for x in inserted_ids)
    exact_memory = sys.getsizeof(exact_set)
    for item in inserted_ids:
        exact_memory += sys.getsizeof(str(item))

    fp_rate = false_positives / len(test_new) if test_new else 0
    expected_fp = bf.expected_false_positive_rate()

    return {
        "bloom_filter": bf,
        "size": size,
        "num_hashes": num_hashes,
        "items_inserted": len(inserted_ids),
        "true_positives": true_positives,
        "false_negatives": false_negatives,
        "false_positives": false_positives,
        "true_negatives": true_negatives,
        "measured_fp_rate": round(fp_rate, 6),
        "expected_fp_rate": round(expected_fp, 6),
        "bloom_memory_bytes": bf.memory_bytes(),
        "exact_set_memory_bytes": exact_memory,
        "memory_ratio": round(exact_memory / max(1, bf.memory_bytes()), 2),
        "fill_ratio": bf.fill_ratio(),
        "bit_summary": bf.get_bit_array_summary(),
    }


@staticmethod
def optimal_size(n, fp_rate=0.01):
    """Calculate optimal bit array size for n items and desired FP rate."""
    if n <= 0 or fp_rate <= 0 or fp_rate >= 1:
        return 1000
    m = -(n * math.log(fp_rate)) / (math.log(2) ** 2)
    return int(math.ceil(m))


@staticmethod
def optimal_hashes(m, n):
    """Calculate optimal number of hash functions for m bits and n items."""
    if n <= 0 or m <= 0:
        return 3
    k = (m / n) * math.log(2)
    return max(1, int(math.ceil(k)))
