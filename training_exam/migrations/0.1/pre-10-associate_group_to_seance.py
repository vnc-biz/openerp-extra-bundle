__name__ = 'Associate the missing group to the seance without a group'

def migrate(cr, v):
    
    cr.execute("""
               SELECT ts.id, tssr.session_id
               FROM training_session_seance_rel tssr, training_seance ts
               WHERE ts.id = tssr.seance_id
               AND ts.group_id is null
               AND ts.kind = %s
               """, ('exam',))
    rows = cr.fetchall()
    for row in rows:
        cr.execute('SELECT id FROM training_group WHERE session_id = %s LIMIT 1', (row[1],))
        res = cr.fetchone()

        try:
            group_id = res[0]
        except:
            cr.execute('INSERT INTO training_group(name, session_id) VALUES(%s, %s)',
                       ('Class 1', row[1],))
            cr.execute('SELECT id FROM training_group WHERE session_id = %s LIMIT 1', (row[1],))
            group_id = cr.fetchone()[0]

        cr.execute('UPDATE training_seance SET group_id = %s WHERE id = %s', (group_id, row[0]))

    return

