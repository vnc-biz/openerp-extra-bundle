__name__ = "Rename the sequence of the participation request"

def migrate(cr, v):
    cr.execute('ALTER SEQUENCE training_participation_stakeholder_session_id_seq RENAME TO training_participation_stakeholder_request_id_seq')
