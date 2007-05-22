{
	"name" : "Point Of Sale",
	"version" : "1.0",
	"author" : "Tiny",
	
	"description": """
Main features :
 - Fast encoding of the sale.
 - Allow to choose one payment mode (the quick way) or to split the payment between several payment mode.
 - Computation of the amount of money to return.
 - Create and confirm picking list automatically.
 - Allow the user to create invoice automatically.
 - Allow to refund former sales.

	""",
	
	"category" : "Generic Modules/Sales & Purchases",
	"depends" : ["sale","purchase","account","account_tax_include"],
	"init_xml" : [],
	"demo_xml" : [],
	"update_xml" : ["pos_report.xml","pos_wizard.xml","pos_view.xml","pos_sequence.xml","pos_data.xml"],
	"active": False,
	"installable": True,
}
