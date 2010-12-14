__name__ = 'Migrate the workflow items'

import uuid

def gen_guid():
    return str(uuid.uuid4()).split('-')[0]

def imd(cr, name, module='training'):
    cr.execute('SELECT res_id FROM ir_model_data WHERE module=%s AND name=%s', (module, name))
    return cr.fetchone()[0]

def migrate(cr, v):
    
    wkf_id = imd(cr, 'wkf_participation_stakeholder_request')
    state_to_activity = {
        'draft': imd(cr, 'wkf_act_pshr_draft'),
        'valid': imd(cr, 'wkf_act_pshr_valid'),
        'requested': imd(cr, 'wkf_act_pshr_requested'),
        'accepted': imd(cr, 'wkf_act_pshr_accepted'),
        'refused': imd(cr, 'wkf_act_pshr_refused'),
        'cancelled': imd(cr, 'wkf_act_pshr_cancelled'),
        'done': imd(cr, 'wkf_act_pshr_done'),
    }

    cr.execute("SELECT id, state FROM training_participation_stakeholder_request")
    for request_id, request_state in cr.fetchall():
        guid = gen_guid()
        cr.execute('INSERT INTO wkf_instance(wkf_id, uid, res_id, res_type, state) VALUES (%s, %s, %s, %s, %s)', (wkf_id, 1, request_id, 'training.participation.stakeholder.request', guid))
        
        cr.execute('SELECT id FROM wkf_instance WHERE state=%s', (guid,))
        inst_id = cr.fetchone()[0]
        
        inst_state = ['active', 'complete'][request_state in ('cancelled', 'done')]
        cr.execute('UPDATE wkf_instance SET state=%s WHERE id=%s', (inst_state, inst_id))
        
        cr.execute('INSERT INTO wkf_workitem(act_id, inst_id, state) VALUES (%s, %s, %s)', (state_to_activity[request_state], inst_id, 'complete'))

    
    # delete old workflow
    old_wkf_id = imd(cr, 'workflow_participation_stakeholder_session')
    cr.execute("DELETE FROM wkf WHERE id=%s", (old_wkf_id,))

