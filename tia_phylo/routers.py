class PhyloRouter:
    """Route all models in the 'phylo' app to the read-only getphylopics DB."""

    APP = 'tia_phylo'
    DB = 'getphylopics'

    def db_for_read(self, model, **hints):
        if model._meta.app_label == self.APP:
            return self.DB
        return None

    def db_for_write(self, model, **hints):
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label == self.APP and obj2._meta.app_label == self.APP:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if db == self.DB:
            return False  # never run any migrations on the read-only getphylopics DB
        if app_label == self.APP:
            return False  # don't migrate phylo unmanaged models to the default DB either
        return None
