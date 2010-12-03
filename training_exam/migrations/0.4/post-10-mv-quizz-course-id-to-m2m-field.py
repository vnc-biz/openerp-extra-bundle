__name__ = 'Move course related field  on Questionnaire Course (o2m) field'

def migrate(cr, v):
    cr.execute("""
        INSERT INTO training_exam_questionnaire_course (questionnaire_id, course_id, passing_score)
            SELECT id AS questionnaire_id, course_id, passing_score
            FROM training_exam_questionnaire
            WHERE course_id IS NOT NULL;
    """)

    return

