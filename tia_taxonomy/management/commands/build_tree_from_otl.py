"""
Build the real phylogenetic tree from Open Tree of Life (OTL) API.

For each Animal, resolves its scientific_name to an OTT ID, fetches the full
ancestor lineage, and assembles all lineages into a set of Clade nodes.
Animals are then re-attached to their correct leaf clade.

Responses are cached to import_data/otl_cache/<animal-slug>.json so re-runs
skip HTTP calls. Animals that fail to resolve stay attached to the 'Unresolved'
placeholder so they can be fixed manually.

Flags:
  --limit N      Only process N animals (for testing)
  --dry-run      Fetch and cache lineages but write nothing to the database
  --clear-cache  Delete the OTL cache before running
  --rebuild      Wipe all non-Unresolved Clades and rebuild from scratch
"""
import json
import time
from pathlib import Path

import requests
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from tia_taxonomy.models import Clade
from tia_animals.models import Animal


OTL_BASE = 'https://api.opentreeoflife.org/v3'
CACHE_DIR = Path(__file__).resolve().parents[4] / 'import_data' / 'otl_cache'

# Keys are what's stored in the DB; values are what to send to OTL instead.
# Add entries here as animals fail to resolve.
NAME_CORRECTIONS = {
    'Balaenoptera novaeangliae': 'Megaptera novaeangliae',
    'Panthera Panthera': 'Panthera leo',
    'Panthera (Panthera)': 'Panthera leo',
    # Parenthetical subgenus notation — OTL needs standard binomial
    'Ursus (arctos)': 'Ursus arctos',
    'Ursus (spelaeus)': 'Ursus spelaeus',
    'Corvus (corax)': 'Corvus corax',
    'Giraffa (camelopardalis)': 'Giraffa camelopardalis',
    'Homo (sapiens)': 'Homo sapiens',
    'Lynx (Lynx)': 'Lynx lynx',
    'Macaca (mulatta)': 'Macaca mulatta',
    'Panthera (Tigris)': 'Panthera tigris',
    'Tapirus (terrestris)': 'Tapirus terrestris',
    'Vulpes (Vulpes)': 'Vulpes vulpes',
    'Canis (lupus)': 'Canis lupus',
    'Equus (Hippotigris)': 'Equus quagga',
    # Domestic species
    'Felis lybica catus': 'Felis catus',
    'Canis familiaris familiaris': 'Canis lupus familiaris',
    # Fossil taxa — OTL sometimes uses genus only or alternate names
    'Otodus megalodon': 'Carcharocles megalodon',
    'Dunkleosteus terrelli': 'Dunkleosteus',
    'Morganucodon watsoni': 'Morganucodon',
    'Paraceratherium transouralicum': 'Paraceratherium',
    'Tanystropheus hydroides': 'Tanystropheus',
    'Tiktaalik roseae': 'Tiktaalik',
    # Ichthyosaurus communis, Plesiosaurus dolichodeirus, Australopithecus africanus:
    # no correction needed — original names resolve via approx-match fallback below.
}


class Command(BaseCommand):
    help = 'Build the phylogenetic tree from Open Tree of Life and re-attach animals.'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=None,
                            help='Only process N animals.')
        parser.add_argument('--dry-run', action='store_true',
                            help='Fetch and cache but write nothing to DB.')
        parser.add_argument('--clear-cache', action='store_true',
                            help='Delete cached OTL responses before running.')
        parser.add_argument('--rebuild', action='store_true',
                            help='Wipe all non-Unresolved Clades and rebuild from scratch.')

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def handle(self, *args, **options):
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

        if options['clear_cache']:
            files = list(CACHE_DIR.glob('*.json'))
            for f in files:
                f.unlink()
            self.stdout.write(f"Cleared {len(files)} cached files from {CACHE_DIR}")

        if options['rebuild'] and not options['dry_run']:
            self._reset_clades()

        animals = list(Animal.objects.select_related('clade').order_by('common_name'))
        if options['limit']:
            animals = animals[:options['limit']]

        self.stdout.write(f"Processing {len(animals)} animals...")

        lineages = {}   # animal.pk -> leaf ott_id
        all_nodes = {}  # ott_id -> node dict (every unique node across all lineages)
        failed = []

        for i, animal in enumerate(animals, 1):
            self.stdout.write(
                f"  [{i}/{len(animals)}] {animal.common_name} ({animal.scientific_name})"
            )
            try:
                lineage = self._fetch_lineage(animal)
            except Exception as exc:
                self.stdout.write(self.style.WARNING(
                    f"    !! {animal.common_name}: unexpected error — {exc}"
                ))
                failed.append(animal)
                continue

            if lineage is None:
                failed.append(animal)
                continue  # warning already printed inside _fetch_lineage

            leaf = lineage[0]  # most-derived (leaf) node is first
            lineages[animal.pk] = leaf['ott_id']
            for node in lineage:
                ott_id = node['ott_id']
                if ott_id not in all_nodes:
                    all_nodes[ott_id] = node

            self.stdout.write(
                f"    ok → ott:{leaf['ott_id']} ({leaf['name']}, {len(lineage)} nodes in chain)"
            )

        self.stdout.write(
            f"\nResolved {len(lineages)}/{len(animals)} animals. "
            f"Unique nodes: {len(all_nodes)}. Failed: {len(failed)}."
        )

        if options['dry_run']:
            self.stdout.write(self.style.WARNING("--dry-run: no database writes."))
            self._report()
            return

        with transaction.atomic():
            ott_to_clade = self._upsert_clades(all_nodes)
            attached, skipped = self._attach_animals(animals, lineages, ott_to_clade)

        self.stdout.write(
            f"Attached {attached} animals to their leaf clades ({skipped} stayed Unresolved)."
        )

        self._maybe_delete_unresolved()

        if failed:
            self.stdout.write(self.style.WARNING("\nAnimals that failed to resolve:"))
            for a in failed:
                self.stdout.write(self.style.WARNING(f"  - {a.common_name} ({a.scientific_name})"))

        self._report()

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def _reset_clades(self):
        self.stdout.write("Resetting: re-attaching all animals to Unresolved...")
        unresolved = Clade.objects.get(slug='unresolved')
        Animal.objects.all().update(clade=unresolved)
        deleted_count, _ = Clade.objects.exclude(slug='unresolved').delete()
        self.stdout.write(f"  Deleted {deleted_count} non-Unresolved Clades.")

    # ------------------------------------------------------------------
    # OTL fetch & cache
    # ------------------------------------------------------------------

    def _cache_path(self, animal):
        return CACHE_DIR / f"{animal.slug}.json"

    def _fetch_lineage(self, animal):
        """Return list of node dicts leaf→root, or None on failure. Uses disk cache."""
        cache_file = self._cache_path(animal)

        if cache_file.exists():
            try:
                return json.loads(cache_file.read_text())
            except (json.JSONDecodeError, OSError):
                pass  # corrupt cache — re-fetch

        query_name = NAME_CORRECTIONS.get(animal.scientific_name, animal.scientific_name)
        if query_name != animal.scientific_name:
            self.stdout.write(
                f"    (name correction: '{animal.scientific_name}' → '{query_name}')"
            )

        ott_id = self._tnrs_match(animal.common_name, query_name)
        if ott_id is None:
            self.stdout.write(self.style.WARNING(
                f"    !! {animal.common_name}: TNRS found no match for '{query_name}'"
            ))
            return None

        lineage = self._taxon_lineage(animal.common_name, ott_id)
        if lineage is None:
            return None

        cache_file.write_text(json.dumps(lineage))
        return lineage

    def _tnrs_match(self, common_name, query_name):
        """POST to /tnrs/match_names; return the best OTT ID or None.

        First tries exact matching. If the exact-match index returns nothing (a
        known OTL gap for fossil taxa whose names aren't fully indexed), retries
        with approximate matching but only accepts a hit whose matched_name equals
        the query — i.e. the name is correct, the index just missed it.
        """
        ott_id = self._tnrs_post(common_name, query_name, approximate=False)
        if ott_id is not None:
            return ott_id

        # Fallback: approximate, but only accept an exact-name hit
        ott_id = self._tnrs_post(common_name, query_name, approximate=True,
                                 require_exact_name=True)
        if ott_id is not None:
            self.stdout.write(
                f"    (resolved via approx-match fallback for '{query_name}')"
            )
        return ott_id

    def _tnrs_post(self, common_name, query_name, approximate, require_exact_name=False):
        """Single TNRS HTTP call; returns ott_id or None."""
        try:
            resp = requests.post(
                f"{OTL_BASE}/tnrs/match_names",
                json={"names": [query_name], "do_approximate_matching": approximate},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            self.stdout.write(self.style.WARNING(
                f"    !! {common_name}: TNRS request failed — {exc}"
            ))
            return None
        finally:
            time.sleep(0.1)

        results = data.get('results', [])
        if not results:
            return None
        matches = results[0].get('matches', [])
        if not matches:
            return None

        if require_exact_name:
            matches = [m for m in matches
                       if m.get('matched_name', '').lower() == query_name.lower()]
            if not matches:
                return None

        # Prefer exact, non-synonym matches; fall back to the first hit
        preferred = [m for m in matches
                     if not m.get('is_synonym')
                     and m.get('matched_name', '').lower() == query_name.lower()]
        best = preferred[0] if preferred else matches[0]
        return best.get('taxon', {}).get('ott_id')

    def _taxon_lineage(self, common_name, ott_id):
        """POST to /taxonomy/taxon_info; return list of node dicts leaf→root, or None."""
        try:
            resp = requests.post(
                f"{OTL_BASE}/taxonomy/taxon_info",
                json={"ott_id": ott_id, "include_lineage": True},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            self.stdout.write(self.style.WARNING(
                f"    !! {common_name}: taxon_info request failed for ott:{ott_id} — {exc}"
            ))
            return None
        finally:
            time.sleep(0.1)

        leaf_node = {
            'ott_id': ott_id,
            'name': data.get('name', ''),
            'rank': data.get('rank', 'no rank'),
            'parent_ott_id': None,
        }

        nodes = [leaf_node]
        for ancestor in data.get('lineage', []):
            ancestor_ott = ancestor.get('ott_id')
            if ancestor_ott is None:
                continue
            nodes.append({
                'ott_id': ancestor_ott,
                'name': ancestor.get('name', ''),
                'rank': ancestor.get('rank', 'no rank'),
                'parent_ott_id': None,
            })

        # Wire parent pointers: each node's parent is the next entry in the list
        for i in range(len(nodes) - 1):
            nodes[i]['parent_ott_id'] = nodes[i + 1]['ott_id']
        nodes[-1]['parent_ott_id'] = None  # root

        return nodes  # leaf first, root last

    # ------------------------------------------------------------------
    # DB writes
    # ------------------------------------------------------------------

    def _upsert_clades(self, all_nodes):
        """BFS from root(s), inserting each node only after its parent exists.

        Returns an ott_id → Clade mapping for the attach step.
        """
        node_ids = set(all_nodes.keys())

        # Build a children map once so BFS is O(n) not O(n²)
        children_map: dict = {oid: [] for oid in node_ids}
        for node in all_nodes.values():
            p = node['parent_ott_id']
            if p in children_map:
                children_map[p].append(node)

        # Roots: no parent, or parent is outside our node set (e.g. cellular organisms)
        roots = [n for n in all_nodes.values()
                 if n['parent_ott_id'] is None or n['parent_ott_id'] not in node_ids]

        ordered = []
        visited = set()
        queue = list(roots)
        while queue:
            node = queue.pop(0)
            oid = node['ott_id']
            if oid in visited:
                continue
            visited.add(oid)
            ordered.append(node)
            queue.extend(children_map.get(oid, []))

        # Safety net: catch any nodes unreachable from roots (shouldn't happen)
        for node in all_nodes.values():
            if node['ott_id'] not in visited:
                ordered.append(node)

        self.stdout.write(f"Upserting {len(ordered)} clades (root-first)...")
        ott_to_clade = {}

        for node in ordered:
            ott_id = node['ott_id']
            name = node['name'] or f"ott{ott_id}"
            rank = node['rank'] or 'no rank'
            parent_ott = node['parent_ott_id']
            parent_clade = ott_to_clade.get(parent_ott) if parent_ott else None

            clade, _ = Clade.objects.update_or_create(
                ott_id=ott_id,
                defaults={
                    'name': name,
                    'slug': self._unique_slug(name, ott_id),
                    'rank': rank,
                    'parent': parent_clade,
                },
            )
            ott_to_clade[ott_id] = clade

        self.stdout.write(f"  Done. Total Clades now: {Clade.objects.count()}")
        return ott_to_clade

    def _unique_slug(self, name, ott_id):
        base = slugify(name) or f"ott{ott_id}"
        # Allow the slug if no *other* clade already uses it
        if not Clade.objects.filter(slug=base).exclude(ott_id=ott_id).exists():
            return base
        return f"{base}-{ott_id}"

    def _attach_animals(self, animals, lineages, ott_to_clade):
        """Re-point each resolved animal at its leaf clade."""
        attached = 0
        skipped = 0
        for animal in animals:
            leaf_ott = lineages.get(animal.pk)
            if leaf_ott is None:
                skipped += 1
                continue
            clade = ott_to_clade.get(leaf_ott)
            if clade is None:
                self.stdout.write(self.style.WARNING(
                    f"  No clade found for ott:{leaf_ott} ({animal.common_name}), staying Unresolved"
                ))
                skipped += 1
                continue
            animal.clade = clade
            animal.save(update_fields=['clade', 'updated_at'])
            attached += 1
        return attached, skipped

    def _maybe_delete_unresolved(self):
        """Delete the 'Unresolved' placeholder if no animals remain attached to it."""
        try:
            unresolved = Clade.objects.get(slug='unresolved')
        except Clade.DoesNotExist:
            return
        remaining = Animal.objects.filter(clade=unresolved).count()
        if remaining == 0:
            unresolved.delete()
            self.stdout.write("Deleted 'Unresolved' placeholder clade (no animals remain).")
        else:
            self.stdout.write(self.style.WARNING(
                f"'Unresolved' clade kept — {remaining} animal(s) still attached."
            ))

    # ------------------------------------------------------------------
    # Report
    # ------------------------------------------------------------------

    def _report(self):
        unresolved_count = Animal.objects.filter(clade__slug='unresolved').count()
        self.stdout.write(self.style.SUCCESS("\n=== build_tree_from_otl complete ==="))
        self.stdout.write(f"Clades:              {Clade.objects.count()}")
        self.stdout.write(f"Animals total:       {Animal.objects.count()}")
        self.stdout.write(f"  resolved:          {Animal.objects.count() - unresolved_count}")
        self.stdout.write(f"  still Unresolved:  {unresolved_count}")
        self.stdout.write(
            f"Cache dir:           {CACHE_DIR} ({len(list(CACHE_DIR.glob('*.json')))} files)"
        )
