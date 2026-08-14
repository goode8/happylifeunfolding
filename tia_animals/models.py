from django.db import models
from tia_taxonomy.models import Clade, Category


class Animal(models.Model):
    """A species players can pick. Always attaches to a leaf-ish clade."""
    
    # Identity
    common_name = models.CharField(max_length=255, unique=True)  # "T. Rex", "Blue Whale"
    scientific_name = models.CharField(max_length=255)           # "Tyrannosaurus rex"
    slug = models.SlugField(max_length=255, unique=True)
    
    # Tree position
    clade = models.ForeignKey(Clade, on_delete=models.PROTECT, related_name='animals')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='animals')
    
    # Existence dates — distinct from the clade's divergence date
    is_extinct = models.BooleanField(default=False)
    first_appearance_mya = models.FloatField(null=True, blank=True)
    last_appearance_mya = models.FloatField(null=True, blank=True)  # 0 for living
    geologic_range = models.CharField(max_length=255, blank=True)
    
    conservation_status = models.CharField(max_length=100, blank=True)

    # Game tuning
    QUALITY_TIERS = [
        (1, 'Ready'),         # silhouette good, taxonomy correct, facts curated
        (2, 'Playable'),      # works, but facts sparse or imagery imperfect
        (3, 'Draft'),         # something is wrong — hide from games
    ]
    quality_tier = models.IntegerField(choices=QUALITY_TIERS, default=3)
    is_published = models.BooleanField(default=False)
    difficulty = models.IntegerField(default=3)        # 1-5, used in round generation
    popularity = models.IntegerField(default=0)        # bumps charismatic species
    
    # Source tracking
    wikidata_qid = models.CharField(max_length=20, blank=True, db_index=True)
    wikipedia_url = models.URLField(blank=True)
    description = models.TextField(blank=True)         # short intro paragraph
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'animals_animal'
        ordering = ['common_name']
        indexes = [
            models.Index(fields=['is_published', 'quality_tier']),
            models.Index(fields=['category', 'is_published']),
        ]
    
    def __str__(self):
        return self.common_name

    @staticmethod
    def _fmt_mya(mya):
        """Return (text, unit) where unit is 'million', 'thousand', or 'ce'."""
        if mya >= 1:
            return f'~{mya:g}', 'million'
        if mya >= 0.001:
            return f'~{round(mya * 1000):,}', 'thousand'
        return str(round(2026 - mya * 1_000_000)), 'ce'

    @property
    def lifespan_display(self):
        """Full span, e.g. 'alive during ~255–245 million years ago' or '~7.5 million years ago – present'."""
        first = self.first_appearance_mya
        last = self.last_appearance_mya

        def fmt(mya):
            n, unit = self._fmt_mya(mya)
            if unit == 'million':
                return f'{n} million years ago'
            if unit == 'thousand':
                return f'{n} thousand years ago'
            return f'{n} CE'

        if self.is_extinct:
            if first is not None and last is not None:
                fn, fu = self._fmt_mya(first)
                ln, lu = self._fmt_mya(last)
                if fu == lu and fu in ('million', 'thousand'):
                    return f'alive during {fn}–{ln.lstrip("~")} {fu} years ago'
                return f'alive during {fmt(first)} – {fmt(last)}'
            if last is not None:
                return f'alive during until {fmt(last)}'
            if first is not None:
                return f'alive during from {fmt(first)}'
        else:
            if first is not None:
                return f'{fmt(first)} – present'
        return ''


class Silhouette(models.Model):
    """PhyloPic silhouette. Separate table because licensing matters and animals can have multiple."""
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name='silhouettes')
    is_primary = models.BooleanField(default=True)
    
    phylopic_uuid = models.CharField(max_length=100, unique=True)
    image = models.ImageField(upload_to='silhouettes/')
    
    contributor_name = models.CharField(max_length=255)
    contributor_url = models.URLField(blank=True)
    license_type = models.CharField(max_length=50)              # "CC0 1.0", "CC BY 4.0"
    license_url = models.URLField()
    source_url = models.URLField()
    image_page_url = models.URLField(blank=True)               # phylopic.org page for attribution
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'animals_silhouette'
        indexes = [
            models.Index(fields=['animal', 'is_primary']),
        ]
    
    def __str__(self):
        return f"Silhouette of {self.animal.common_name}"


class Fact(models.Model):
    """A game-suitable fact. Replaces the v1 fun_facts JSON blob with proper structure."""
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name='facts')
    
    # Use {animal} as the placeholder — render with .format() at display time
    text_template = models.TextField(
        help_text="Use {animal} as a placeholder for the animal's name."
    )
    
    # Game metadata that v1 was missing
    is_approved = models.BooleanField(default=False)
    difficulty = models.IntegerField(default=3)         # 1-5
    is_obvious = models.BooleanField(default=False)     # "the lion roars" — too easy for matching
    
    source = models.CharField(max_length=255, blank=True)
    source_url = models.URLField(blank=True)
    
    # Analytics — fills in once gameplay starts
    times_shown = models.IntegerField(default=0)
    times_correct = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'animals_fact'
        indexes = [
            models.Index(fields=['animal', 'is_approved']),
        ]
    
    def __str__(self):
        return f"Fact for {self.animal.common_name}: {self.text_template[:50]}..."
    
    def render(self, name_override=None):
        """Render the fact with the animal's name (or a custom replacement like 'this animal')."""
        return self.text_template.format(animal=name_override or self.animal.common_name)


class AnimalSuggestion(models.Model):
    """A player's request to add an animal that isn't in the game yet."""
    name = models.CharField(max_length=100, blank=True)
    message = models.TextField()
    feedback = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        db_table = 'animals_suggestion'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name or 'Anonymous'} — {self.created_at.strftime('%b %d %Y')}"