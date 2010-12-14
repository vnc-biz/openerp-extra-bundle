__name__ = "Update training_course_category.parent_category_id"

def migrate(cr, v):
    cr.execute("SELECT id, analytic_account_id FROM training_course_category WHERE parent_category_id IS NULL")
    for cid, aaid in cr.fetchall():
        cr.execute("UPDATE training_course_category "
                   "   SET parent_category_id = (SELECT id"
                   "                               FROM training_course_category"
                   "                              WHERE analytic_account_id = (SELECT parent_id"
                   "                                                             FROM account_analytic_account"
                   "                                                            WHERE id = %s"
                   "                                                          )"
                   "                            )"
                   " WHERE id = %s"
                   , (aaid, cid)
                  )

