from django.db import models


class PhyloAnimal(models.Model):
    uuid = models.CharField(max_length=100)
    common_name = models.CharField(max_length=255)
    taxon_name = models.CharField(max_length=255)
    local_thumbnail = models.CharField(max_length=500)
    license_type = models.CharField(max_length=50)
    license_url = models.CharField(max_length=500)
    contributor_name = models.CharField(max_length=255)
    contributor_url = models.CharField(max_length=500)
    group_name = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'animals_animalimage'

    def __str__(self):
        return self.common_name


class PhyloLineageNode(models.Model):
    node_uuid = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    image_uuid = models.CharField(max_length=100)
    local_thumbnail = models.CharField(max_length=500)
    license_type = models.CharField(max_length=50)
    license_url = models.CharField(max_length=500)
    contributor_name = models.CharField(max_length=255)
    contributor_url = models.CharField(max_length=500)

    class Meta:
        managed = False
        db_table = 'animals_lineagenode'

    def __str__(self):
        return self.name


class PhyloAnimalLineage(models.Model):
    animal = models.ForeignKey(
        PhyloAnimal, on_delete=models.DO_NOTHING, db_constraint=False
    )
    node = models.ForeignKey(
        PhyloLineageNode, on_delete=models.DO_NOTHING, db_constraint=False
    )
    depth = models.PositiveIntegerField()

    class Meta:
        managed = False
        db_table = 'animals_animallineage'
