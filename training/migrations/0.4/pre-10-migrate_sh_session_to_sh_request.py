__name__ = 'Convert participation to session to participation request'


def migrate(cr, v):
    ## This part is really tricky:
    # The new object "training.participation.stakeholder.request" really look like the old "training.participaiton.stakeholder.session" but is not intended to be used in the same way.
    # The fact that a lot of columns stay the same, we can just rename the table and remove or rename some columns.

    cr.execute('ALTER TABLE training_participation_stakeholder_session RENAME TO training_participation_stakeholder_request')
    cr.execute('ALTER TABLE training_participation_stakeholder_request RENAME COLUMN note TO notes')
    
    for c in 'group_id generated contact_id partner_id offer_id date price'.split():
        # note: date and price are dropped to force the reevaluation of the values (as there are stored functions)
        cr.execute('ALTER TABLE training_participation_stakeholder_request DROP COLUMN %s' % (c,))
    
    cr.execute('ALTER TABLE training_participation_stakeholder RENAME COLUMN participation_sh_session_id TO request_id')

    return


