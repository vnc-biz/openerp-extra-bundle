__name__ = "Update state of requests and participations"

def migrate(cr, v):
    for old, new in [('confirmed', 'accepted'), ('undermined', 'refused'), ('pending', 'requested')]:
        cr.execute('UPDATE training_participation_stakeholder_request SET state=%s WHERE state=%s', (new, old))
        
    for old, new in [('confirmed', 'accepted'), ('undermined', 'refused'), ('requested', 'draft')]:
        cr.execute('UPDATE training_participation_stakeholder SET state=%s WHERE state=%s', (new, old))
