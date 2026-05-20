"""
Replace fabricated clade content with real scraped data.

Step 1: Wipe all divergence_mya and AI-written description/notable_traits from
        every Clade row.

Step 2: For each of the 203 LCA clades (those with a wikidata_qid):
        a. Resolve the English Wikipedia title via the Wikidata API (batch).
        b. Fetch the plain-text summary via the Wikipedia REST summary endpoint.
        c. Store the result in clade.description.

The REST summary API follows redirects automatically, returning exactly the
first paragraph of the article's intro — no normalization ambiguity.

Flags:
  --dry-run     Print counts without writing anything.
"""
import time

import requests
from django.core.management.base import BaseCommand

from tia_taxonomy.models import Clade

WIKIDATA_API = 'https://www.wikidata.org/w/api.php'
WIKIPEDIA_REST = 'https://en.wikipedia.org/api/rest_v1/page/summary'
BATCH_SIZE = 50
HEADERS = {'User-Agent': 'TiaTrex/1.0 (phylogenetics game; dawngoodnight@gmail.com)'}


class Command(BaseCommand):
    help = 'Wipe fabricated clade content and scrape real Wikipedia intro paragraphs.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help='Print counts without writing to the DB.')

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        if self.dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN — no DB writes.'))

        self.wipe_fabricated()
        if not self.dry_run:
            self.scrape_intros()

    # ------------------------------------------------------------------
    # Step 1: wipe
    # ------------------------------------------------------------------

    def wipe_fabricated(self):
        desc_qs = Clade.objects.exclude(description='')
        div_qs = Clade.objects.filter(divergence_mya__isnull=False)

        if self.dry_run:
            self.stdout.write(f'Would clear description from {desc_qs.count()} clades')
            self.stdout.write(f'Would clear divergence_mya from {div_qs.count()} clades')
            return

        desc_count = desc_qs.update(description='', notable_traits='')
        div_count = div_qs.update(divergence_mya=None, divergence_source='', divergence_confidence='')
        self.stdout.write(f'Cleared description/notable_traits from {desc_count} clades')
        self.stdout.write(f'Cleared divergence_mya from {div_count} clades')

    # ------------------------------------------------------------------
    # Step 2: scrape
    # ------------------------------------------------------------------

    def scrape_intros(self):
        clades = list(Clade.objects.exclude(wikidata_qid=''))
        self.stdout.write(f'Fetching Wikipedia titles for {len(clades)} clades...')

        # a. Resolve QID → enwiki title via Wikidata (batched)
        qid_to_title = {}
        for i in range(0, len(clades), BATCH_SIZE):
            batch_qids = [c.wikidata_qid for c in clades[i:i + BATCH_SIZE]]
            qid_to_title.update(self._fetch_enwiki_titles(batch_qids))
            time.sleep(0.5)

        self.stdout.write(f'  {len(qid_to_title)}/{len(clades)} QIDs resolved to Wikipedia titles')

        # b. Fetch summary for each clade via Wikipedia REST API (one request each)
        self.stdout.write('Fetching Wikipedia summaries...')
        updated = 0
        no_article = 0

        for clade in clades:
            title = qid_to_title.get(clade.wikidata_qid)
            if not title:
                no_article += 1
                continue

            extract = self._fetch_summary(title)
            if not extract:
                self.stdout.write(self.style.WARNING(
                    f'  no extract: {clade.name} → {title!r}'
                ))
                no_article += 1
                continue

            clade.description = extract
            clade.save(update_fields=['description', 'updated_at'])
            updated += 1
            time.sleep(0.1)

        self.stdout.write(self.style.SUCCESS(
            f'\n=== scrape_clade_descriptions complete ===\n'
            f'Updated: {updated}   No article found: {no_article}'
        ))

    # ------------------------------------------------------------------
    # API helpers
    # ------------------------------------------------------------------

    def _fetch_enwiki_titles(self, qids):
        """Return {qid: enwiki_title} for each QID that has an English WP article."""
        try:
            resp = requests.get(WIKIDATA_API, headers=HEADERS, params={
                'action': 'wbgetentities',
                'ids': '|'.join(qids),
                'props': 'sitelinks',
                'sitefilter': 'enwiki',
                'format': 'json',
            }, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            self.stdout.write(self.style.WARNING(f'  Wikidata batch failed: {exc}'))
            return {}

        result = {}
        for qid, entity in data.get('entities', {}).items():
            title = entity.get('sitelinks', {}).get('enwiki', {}).get('title')
            if title:
                result[qid] = title
        return result

    def _fetch_summary(self, title):
        """Return the plain-text extract from the Wikipedia REST summary endpoint.

        Follows redirects automatically. Returns empty string on any failure or
        if the article has no extract (e.g. disambiguation pages).
        """
        encoded = requests.utils.quote(title.replace(' ', '_'), safe='')
        try:
            resp = requests.get(
                f'{WIKIPEDIA_REST}/{encoded}',
                headers=HEADERS,
                timeout=15,
            )
            if resp.status_code == 404:
                return ''
            resp.raise_for_status()
            return resp.json().get('extract', '').strip()
        except Exception as exc:
            self.stdout.write(self.style.WARNING(f'  REST failed for {title!r}: {exc}'))
            return ''
