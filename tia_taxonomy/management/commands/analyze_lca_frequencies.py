"""
Compute how often each Clade appears as the LCA across all unique animal pairs.

Iterates over all C(289, 2) = 41,616 pairs, computes the LCA using path
string comparison (no per-pair DB query), and reports the top 100 clades
by frequency. Also writes import_data/lca_frequencies.csv for reference.

Read-only — makes no changes to the database.
"""
import csv
import itertools
from collections import Counter
from pathlib import Path

from django.core.management.base import BaseCommand

from tia_animals.models import Animal
from tia_taxonomy.models import Clade


REPORT_PATH = Path(__file__).resolve().parents[4] / 'import_data' / 'lca_frequencies.csv'
TOP_N = 100


def _lca_pk(path_a: str, path_b: str):
    """Return the pk of the deepest common ancestor given two materialized paths."""
    ids_a = path_a.strip('/').split('/')
    ids_b = path_b.strip('/').split('/')
    last_common = None
    for a, b in zip(ids_a, ids_b):
        if a == b:
            last_common = int(a)
        else:
            break
    return last_common


class Command(BaseCommand):
    help = 'Report the most frequent LCA clades across all animal pairs (read-only).'

    def handle(self, *args, **options):
        # Load every animal with its clade path in two queries
        animals = list(
            Animal.objects.select_related('clade')
                          .only('common_name', 'clade__id', 'clade__path')
        )
        self.stdout.write(f"Loaded {len(animals)} animals.")

        total_pairs = len(animals) * (len(animals) - 1) // 2
        self.stdout.write(f"Computing LCA for {total_pairs:,} pairs...")

        freq: Counter = Counter()
        for a, b in itertools.combinations(animals, 2):
            pk = _lca_pk(a.clade.path, b.clade.path)
            if pk is not None:
                freq[pk] += 1

        top_pks = [pk for pk, _ in freq.most_common(TOP_N)]
        clade_map = {c.pk: c for c in Clade.objects.filter(pk__in=top_pks)}

        # --- terminal table ---
        header = f"{'Rank':>4}  {'Count':>6}  {'Clade name':<28}  {'Rank':<14}  {'Depth':>5}  Existing date"
        self.stdout.write('\n' + header)
        self.stdout.write('-' * len(header))

        rows = []
        for rank, (pk, count) in enumerate(freq.most_common(TOP_N), 1):
            clade = clade_map.get(pk)
            if clade is None:
                continue
            date_str = f"{clade.divergence_mya} mya" if clade.divergence_mya is not None else '(null)'
            self.stdout.write(
                f"{rank:>4}  {count:>6}  {clade.name:<28}  {clade.rank:<14}  "
                f"{clade.depth:>5}  {date_str}"
            )
            rows.append({
                'rank': rank,
                'count': count,
                'slug': clade.slug,
                'name': clade.name,
                'rank_label': clade.rank,
                'depth': clade.depth,
                'divergence_mya': clade.divergence_mya or '',
            })

        # --- CSV ---
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(REPORT_PATH, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

        self.stdout.write(self.style.SUCCESS(
            f"\nWrote {len(rows)} rows to {REPORT_PATH}"
        ))
