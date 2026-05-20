from django.db import models

from tia_animals.models import Animal
from tia_taxonomy.models import Clade


class AnimalPair(models.Model):
    """Precomputed Wikidata least-common-ancestor for every pair of animals.

    Pairs are stored with slug1 < slug2 alphabetically (same convention as
    lca_pairs.csv). To look up a pair, always sort the two slugs before querying.
    """
    animal1 = models.ForeignKey(Animal, on_delete=models.PROTECT, related_name='pairs_as_first')
    animal2 = models.ForeignKey(Animal, on_delete=models.PROTECT, related_name='pairs_as_second')
    lca = models.ForeignKey(Clade, on_delete=models.PROTECT, related_name='animal_pairs')

    class Meta:
        db_table = 'game_animalpair'
        unique_together = [('animal1', 'animal2')]
        indexes = [
            models.Index(fields=['animal1', 'animal2']),
            models.Index(fields=['lca']),
        ]

    def __str__(self):
        return f"{self.animal1} + {self.animal2} → {self.lca.name}"
