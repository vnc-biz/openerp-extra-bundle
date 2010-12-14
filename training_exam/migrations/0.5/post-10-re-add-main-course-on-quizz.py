__name__ = 'Re-Add main course on Quizz'

def migrate(cr, v):
    cr.execute("""
        UPDATE
            training_exam_questionnaire teq
        SET
            main_course_id = z.main_course_id
        FROM
            (SELECT
                teqc.questionnaire_id as id,
                teqc.course_id as main_course_id
             FROM
                training_exam_questionnaire_course teqc
             LEFT
                JOIN training_exam_questionnaire teq ON teqc.questionnaire_id = teq.id
             WHERE
                teq.type = 'examen') as z
        WHERE
            teq.id = z.id;
    """)

    return

