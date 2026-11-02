"""
ProductPilot - DGIM Algorithm Implementation
=============================================
Implements the Datar-Gionis-Indyk-Motwani (DGIM) algorithm for
approximate counting of 1-bits in a sliding window over a binary stream.

Use case: Monitor event volumes (e.g., new feature requests, blocker reports)
over a sliding time window using sublinear memory.

DGIM trades perfect accuracy for significantly reduced memory usage.
The approximation error is at most 50% of the true count, and in practice
is typically much lower.
"""

import math


class DGIMBucket:
    """Represents a DGIM bucket with a timestamp and size (power of 2)."""

    def __init__(self, timestamp, size=1):
        self.timestamp = timestamp
        self.size = size

    def __repr__(self):
        return f"Bucket(t={self.timestamp}, size={self.size})"


class DGIM:
    """
    DGIM streaming counter for approximate 1-bit counting in a sliding window.

    Parameters
    ----------
    window_size : int
        The size of the sliding window (number of stream positions).
    """

    def __init__(self, window_size=100):
        if window_size < 1:
            raise ValueError("Window size must be >= 1")
        self.window_size = window_size
        self.buckets = []  # Ordered from newest (front) to oldest (back)
        self.current_time = 0
        self.stream_history = []  # For exact comparison (limited to window)

    def process_bit(self, bit):
        """
        Process the next bit in the stream.

        Parameters
        ----------
        bit : int
            0 or 1
        """
        self.current_time += 1
        bit = int(bool(bit))

        # Track exact history for comparison
        self.stream_history.append(bit)
        if len(self.stream_history) > self.window_size:
            self.stream_history = self.stream_history[-self.window_size:]

        # Remove expired buckets
        self._remove_expired()

        # If bit is 1, create a new bucket of size 1
        if bit == 1:
            self.buckets.insert(0, DGIMBucket(self.current_time, size=1))
            self._merge_buckets()

    def process_stream(self, bits):
        """Process a sequence of bits."""
        for bit in bits:
            self.process_bit(bit)

    def _remove_expired(self):
        """Remove buckets whose timestamp is outside the window."""
        cutoff = self.current_time - self.window_size
        self.buckets = [b for b in self.buckets if b.timestamp > cutoff]

    def _merge_buckets(self):
        """
        Merge buckets to maintain the DGIM invariant:
        At most 2 buckets of each size (except possibly the largest size).
        When 3 buckets of the same size exist, merge the two oldest.
        """
        # Group buckets by size and merge from smallest to largest
        changed = True
        while changed:
            changed = False
            size_groups = {}
            for i, b in enumerate(self.buckets):
                if b.size not in size_groups:
                    size_groups[b.size] = []
                size_groups[b.size].append(i)

            for size, indices in sorted(size_groups.items()):
                if len(indices) > 2:
                    # Merge the two oldest (highest indices since list is newest-first)
                    i2 = indices[-1]
                    i1 = indices[-2]
                    # New merged bucket takes the timestamp of the newer one
                    merged = DGIMBucket(
                        timestamp=self.buckets[i1].timestamp,
                        size=size * 2
                    )
                    # Remove both and insert merged
                    # Remove in reverse order to preserve indices
                    self.buckets.pop(i2)
                    self.buckets.pop(i1)
                    # Insert at position i1
                    self.buckets.insert(i1, merged)
                    changed = True
                    break  # Restart since indices changed

    def query(self):
        """
        Return the approximate count of 1-bits in the current window.

        The estimate counts all buckets fully, except the oldest bucket
        which is counted at half its size (since it may be partially
        outside the window).
        """
        if not self.buckets:
            return 0

        total = 0
        for i, bucket in enumerate(self.buckets):
            if i == len(self.buckets) - 1:
                # Oldest bucket: count half
                total += bucket.size / 2
            else:
                total += bucket.size
        return int(math.ceil(total))

    def exact_count(self):
        """Return the exact count of 1-bits in the current window."""
        return sum(self.stream_history[-self.window_size:])

    def get_error(self):
        """Return absolute and relative estimation error."""
        approx = self.query()
        exact = self.exact_count()
        abs_error = abs(approx - exact)
        rel_error = abs_error / exact if exact > 0 else 0.0
        return {
            "approximate_count": approx,
            "exact_count": exact,
            "absolute_error": abs_error,
            "relative_error": round(rel_error, 4),
            "relative_error_pct": round(rel_error * 100, 2),
        }

    def get_buckets_info(self):
        """Return information about current buckets."""
        return [
            {"timestamp": b.timestamp, "size": b.size}
            for b in self.buckets
        ]

    def memory_usage(self):
        """Compare memory: DGIM buckets vs storing all bits."""
        dgim_entries = len(self.buckets)  # Each bucket = (timestamp, size)
        exact_entries = self.window_size  # Store every bit
        return {
            "dgim_entries": dgim_entries,
            "exact_entries": exact_entries,
            "memory_ratio": round(exact_entries / max(1, dgim_entries), 2),
            "dgim_bytes_approx": dgim_entries * 16,  # 2 ints per bucket
            "exact_bytes_approx": exact_entries,  # 1 bit per entry (packed)
        }

    def get_bucket_visualization(self):
        """Return data for visualizing bucket sizes and positions."""
        return {
            "current_time": self.current_time,
            "window_start": max(0, self.current_time - self.window_size),
            "window_size": self.window_size,
            "buckets": self.get_buckets_info(),
            "total_buckets": len(self.buckets),
        }


def run_dgim_demo(stream, window_size=100, alert_threshold=None):
    """
    Run a DGIM demonstration with a given binary stream.

    Parameters
    ----------
    stream : list of int
        Binary stream (0s and 1s).
    window_size : int
        Sliding window size.
    alert_threshold : int, optional
        Alert if approximate count exceeds this value.

    Returns
    -------
    dict
        Demo results including counts, errors, and alerts.
    """
    dgim = DGIM(window_size=window_size)

    snapshots = []
    alerts = []

    for i, bit in enumerate(stream):
        dgim.process_bit(bit)

        # Take snapshots at regular intervals
        if (i + 1) % max(1, len(stream) // 20) == 0 or i == len(stream) - 1:
            error = dgim.get_error()
            snapshots.append({
                "position": i + 1,
                "bit": bit,
                **error,
                "num_buckets": len(dgim.buckets),
            })

        # Check alerts
        if alert_threshold is not None:
            count = dgim.query()
            if count >= alert_threshold:
                alerts.append({
                    "position": i + 1,
                    "count": count,
                    "message": f"Alert at position {i+1}: count {count} >= threshold {alert_threshold}"
                })

    final_error = dgim.get_error()
    memory = dgim.memory_usage()

    return {
        "dgim": dgim,
        "window_size": window_size,
        "stream_length": len(stream),
        "final_error": final_error,
        "memory": memory,
        "snapshots": snapshots,
        "alerts": alerts,
        "buckets": dgim.get_buckets_info(),
    }
