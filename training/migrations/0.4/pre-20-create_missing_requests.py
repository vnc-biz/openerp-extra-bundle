__name__ = "Create missing requests"

import uuid

def gen_guid():
    return str(uuid.uuid4()).split('-')[0]

def migrate(cr, v):
    # apply an original session if missing
    cr.execute("""
               SELECT tssr.seance_id, MIN(tssr.session_id) AS min_session_id
               FROM training_seance tse, training_session_seance_rel tssr, training_session ts
               WHERE tse.id = tssr.seance_id
               AND tse.original_session_id IS NULL
               AND tssr.session_id = ts.id
               GROUP BY tssr.seance_id
               ORDER BY tssr.seance_id
               """)

    for seance_id, min_session_id in cr.fetchall():
        cr.execute("""UPDATE training_seance SET original_session_id = %s WHERE id = %s""", (min_session_id, seance_id,))

    # create requests for existing participations

    statemap = {
        'confirmed': 'accepted',
        'undermined': 'refused',
    }

    cr.execute("""SELECT sh.id, s.original_session_id, sh.job_id, sh.email, sh.payment_mode, sh.note, p.order_id, sh.state
                  FROM training_participation_stakeholder sh 
            INNER JOIN training_seance s ON s.id = sh.seance_id
       LEFT OUTER JOIN purchase_order_line p ON p.id = sh.purchase_order_line_id
                 WHERE sh.request_id IS NULL""")
    for sh_id, session_id, job_id, email, payment_mode, notes, po_id, state in cr.fetchall():
        # create the request
        guid = gen_guid()

        new_state = statemap.get(state, state)

        cr.execute("INSERT INTO training_participation_stakeholder_request(session_id, job_id, email, payment_mode, notes, purchase_order_id, state)"
                   "     VALUES (%s, %s, %s, %s, %s, %s, %s)", (session_id, job_id, email, payment_mode, notes, po_id, guid))
        cr.execute("SELECT id FROM training_participation_stakeholder_request WHERE state = %s", (guid,))
        request_id = cr.fetchone()[0]
        cr.execute("UPDATE training_participation_stakeholder_request SET state=%s WHERE id=%s", (new_state, request_id))
        cr.execute("UPDATE training_participation_stakeholder SET request_id=%s WHERE id=%s", (request_id, sh_id))

        
