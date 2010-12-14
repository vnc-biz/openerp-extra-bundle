__name__ = 'Force the recompute of the field training_seance.confirmed_lecturer'

def migrate(cr, v):
    cr.execute("alter table training_seance drop column confirmed_lecturer")

