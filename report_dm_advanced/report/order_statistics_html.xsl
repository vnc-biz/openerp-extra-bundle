<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:import href="order_statistics_report_header1.xsl"/>
	<xsl:template match="/">
		<xsl:call-template name="html" />
	</xsl:template>

	<xsl:template name="html">
		<!--document filename="example.pdf">
            <template pageSize="45cm,21cm" title="Test" author="Martin Simon" allowSplitting="20">
                <pageTemplate id="first">
                    <frame id="first"  x1="10cm" y1="2.5cm" width="24.7cm" height="17cm"/>
    			</pageTemplate>
			</template-->
		<html>
		<head>
			<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
		    <style type="text/css">
			    p.normal {font-size:"6"; alignment="center"}
		        p {margin:0px; font-size:12px;}
		        td {font-size:14px;}
				p.normal {font-size:11.0px; text-align:center}
				p.normal-title {font-size:11.0px}
				p.title {font-size:23.0px; text-align:center}
				p.date {font-size:15.0px}
				p.glande {font-size:12.0px}
				p.normal_people {font-size:12.0px}
				p.esclave {font-size:12.0px}			    

				table.sample {
					border-width: 1px 1px 1px 1px;
					border-spacing: 2px;
					border-style: outset outset outset outset;
					border-color: gray gray gray gray;
					border-collapse: separate;
					background-color: white;
			</style>
	</meta>
		</head>
			<xsl:call-template name="story"/>
	</html>
	</xsl:template>

	<xsl:template name="story">
		<xsl:for-each select="report/story">	
		<xsl:variable name="s_id" select="attribute::s_id"/>
        <body>
		    <p style="title" t="1"> <xsl:value-of select="attribute::name"/> </p>
		   	 <spacer length="1cm" />
		    <table border='0' width='983'>
			    <xsl:attribute name="style">month</xsl:attribute>
			    <xsl:attribute name="colWidths"><xsl:value-of select="report/cols" /></xsl:attribute>
					<tr>
				        <td>
				            <xsl:value-of select="//date/attribute::from_month_year" /> -
				            <xsl:value-of select="//date/attribute::to_month_year" />
				        </td>
						<xsl:for-each select="//days/day">
				            <td>
				                <p> 
				                    <xsl:value-of select="attribute::string" /></p>
							</td>
						</xsl:for-each>
						<td t="1">Total</td>
					</tr>
			    <xsl:apply-templates select="row"/>
			    <xsl:for-each select="row">
				    <xsl:variable name="id" select="attribute::id"/>
						<tr>
							<td><p><xsl:value-of select="attribute::name"/></p></td>
							<xsl:for-each select="//report/days/day">
							<xsl:variable name="today" select="attribute::string" />
		                    <td>
		                        <p>
									  <xsl:value-of select="format-number(sum(//story[@s_id=$s_id]/row[@id=$id]/time-element[@date=$today]), '##.##')" />
									</p>
								</td>
							</xsl:for-each>
							<td>
							    <p> 
		        				     <xsl:value-of select="format-number(sum(//story[@s_id=$s_id]/row[@id=$id]/time-element),'##.##')"/>
		    					</p>
							</td>
						</tr>
			    </xsl:for-each>
					<tr>
						<td t="1">Total</td>
						<xsl:for-each select="//report/days/day">
							<xsl:variable name="today" select="attribute::string"/>
				                <td>
				                <p>
				                	<xsl:value-of select="format-number(sum(//story[@s_id=$s_id]/row/time-element[@date=$today]),'##.##')"/></p>
								</td>
						</xsl:for-each>
						<td><xsl:value-of select="format-number(sum(//story[@s_id=$s_id]/row/time-element),'##.##')"/></td>
					</tr>
		    </table>
    	</body>
	</xsl:for-each>
	</xsl:template>
</xsl:stylesheet>
