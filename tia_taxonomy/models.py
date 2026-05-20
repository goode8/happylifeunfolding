from django.db import models


class PhyloDivergence(models.Model):
    """Divergence time for a getphylopics LineageNode, keyed by node name.

    The getphylopics data uses OTL node names that don't always match the local
    Clade taxonomy (e.g. 'Nephrozoa' vs 'Bilateria', 'Boreotheria' vs
    'Boreoeutheria'). This table provides a curated name→MYA lookup so the
    Play tab can show divergence times without needing a clean cross-DB join.
    """
    name = models.CharField(max_length=255, unique=True, db_index=True)
    divergence_mya = models.FloatField()
    source = models.CharField(max_length=255, blank=True)
    fun_fact = models.TextField(blank=True)

    class Meta:
        db_table = 'taxonomy_phylodivergence'
        ordering = ['name']
        verbose_name = 'Phylo Divergence'
        verbose_name_plural = 'Phylo Divergences'

    def __str__(self):
        return f'{self.name} ({self.divergence_mya} mya)'


class Category(models.Model):
    """UI grouping like 'Mammals — Marine'."""
    parent_group = models.CharField(max_length=100)
    sub_group = models.CharField(max_length=100, blank=True)
    display_order = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'taxonomy_category'
        unique_together = [('parent_group', 'sub_group')]
        ordering = ['display_order', 'parent_group', 'sub_group']
        verbose_name_plural = 'categories'
    
    def __str__(self):
        if self.sub_group:
            return f"{self.parent_group} — {self.sub_group}"
        return self.parent_group


class Clade(models.Model):
    """A node in the tree of life."""
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    rank = models.CharField(max_length=100)
    
    ott_id = models.IntegerField(unique=True, null=True, blank=True, db_index=True)
    wikidata_qid = models.CharField(max_length=20, blank=True, db_index=True)
    
    parent = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.PROTECT,
        related_name='children'
    )
    
    path = models.CharField(max_length=1000, db_index=True, blank=True)
    depth = models.IntegerField(default=0, db_index=True)
    
    divergence_mya = models.FloatField(null=True, blank=True)
    divergence_source = models.CharField(max_length=100, blank=True)
    divergence_confidence = models.CharField(max_length=20, blank=True)
    
    description = models.TextField(blank=True)
    notable_traits = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'taxonomy_clade'
        indexes = [
            models.Index(fields=['path']),
            models.Index(fields=['parent', 'name']),
            models.Index(fields=['depth']),
        ]
        ordering = ['depth', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.rank})"
    
    def save(self, *args, **kwargs):
        if self.parent:
            self.depth = self.parent.depth + 1
            if not self.pk:
                super().save(*args, **kwargs)
                self.path = f"{self.parent.path}{self.pk}/"
                kwargs['force_insert'] = False
                return super().save(*args, **kwargs)
            self.path = f"{self.parent.path}{self.pk}/"
        else:
            self.depth = 0
            if not self.pk:
                super().save(*args, **kwargs)
                self.path = f"/{self.pk}/"
                kwargs['force_insert'] = False
                return super().save(*args, **kwargs)
            self.path = f"/{self.pk}/"
        super().save(*args, **kwargs)
    
    def ancestors(self):
        if not self.path:
            return Clade.objects.none()
        ids = [int(x) for x in self.path.strip('/').split('/') if x and int(x) != self.pk]
        return Clade.objects.filter(pk__in=ids).order_by('depth')
    
    def descendants(self):
        return Clade.objects.filter(path__startswith=self.path).exclude(pk=self.pk)
    
    @staticmethod
    def common_ancestor(clade_a, clade_b):
        path_a = clade_a.path.strip('/').split('/')
        path_b = clade_b.path.strip('/').split('/')
        common_ids = []
        for a, b in zip(path_a, path_b):
            if a == b:
                common_ids.append(int(a))
            else:
                break
        if not common_ids:
            return None
        return Clade.objects.get(pk=common_ids[-1])