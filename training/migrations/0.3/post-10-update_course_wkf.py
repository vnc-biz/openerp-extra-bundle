__name__ = "Update Course Workflow"

def migrate(cr, v):
    cr.execute("UPDATE wkf_instance w SET state = 'active' WHERE res_type = 'training.course' AND EXISTS (SELECT 1 FROM training_course WHERE id = w.res_id AND state_course = 'validated')")

