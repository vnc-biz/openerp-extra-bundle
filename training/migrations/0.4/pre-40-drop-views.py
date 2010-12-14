__name__ = "Drop views referencing old columns"

def drop_view_if_exists(cr, viewname):
    cr.execute("select count(1) from pg_class where relkind=%s and relname=%s", ('v', viewname,))
    if cr.fetchone()[0]:
        cr.execute("DROP view %s" % (viewname,))

def migrate(cr, v):
    drop_view_if_exists(cr, 'training_report_lecturer_state')

