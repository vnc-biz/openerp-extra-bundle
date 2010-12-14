__name__ = 'Do some cleanup on existing exam participations'

def migrate(cr, v):

    # Mark all participations imported before *GoLive* as "printed"
    # and "received" (INFO: imported data only contains results exam,
    # so it's good if we don't check seance type)
    cr.execute("""
            UPDATE training_participation
                SET certif_printed = True
            WHERE date < DATE('2009-09-01');
    """)
    cr.execute("""
            UPDATE training_participation
                SET result_received = True
            WHERE date < DATE('2009-09-01');
    """)

    # Mark all participations which 
    cr.execute("""
        UPDATE training_participation
            SET result_received = True
        WHERE id in (
                SELECT tp.id
                FROM training_participation tp
                    LEFT JOIN training_seance ts ON tp.seance_id = ts.id
                WHERE ts.kind = 'exam'
                    AND tp.date >= DATE('2009-09-01') and tp.result > 0.0
        )
    """)

    return

