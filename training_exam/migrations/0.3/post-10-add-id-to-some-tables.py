__name__ = 'Do some cleanup on existing exam participations'

def migrate(cr, v):
    cr.execute("""
               INSERT INTO training_exam_questionnaire_question (question_id, questionnaire_id)
               SELECT question_id, questionnaire_id FROM training_exam_questionnaire_question_rel
               """)
    cr.execute("""
               UPDATE training_exam_questionnaire_question SET
                create_date = (SELECT q.create_date FROM training_exam_questionnaire q WHERE q.id = questionnaire_id),
                create_uid = (SELECT q.create_uid FROM training_exam_questionnaire q WHERE q.id = questionnaire_id),
                write_date = (SELECT q.write_date FROM training_exam_questionnaire q WHERE q.id = questionnaire_id),
                write_uid = (SELECT q.write_uid FROM training_exam_questionnaire q WHERE q.id = questionnaire_id)
               """)

    return

