__name__ = "Fill Purchase Order Contact"

def migrate(cr, v):
    cr.execute("""
        UPDATE purchase_order po
           SET contact_id = (SELECT j.contact_id 
                               FROM training_participation_stakeholder s 
                         INNER JOIN res_partner_job j ON j.id = s.job_id 
                              WHERE s.purchase_order_line_id in (SELECT id 
                                                                   FROM purchase_order_line 
                                                                  WHERE order_id=po.id 
                                                                  LIMIT 1) 
                            )
         WHERE contact_id IS NULL
           AND EXISTS(SELECT 1 
                        FROM training_participation_stakeholder
                       WHERE purchase_order_line_id in (SELECT id 
                                                          FROM purchase_order_line 
                                                         WHERE order_id = po.id))
               """)

