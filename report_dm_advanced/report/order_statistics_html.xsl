<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:import href="order_statistics_report_header1.xsl"/>
	<xsl:template match="/">
		<xsl:call-template name="html" />
	</xsl:template>

	<xsl:template name="html">
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
        <body>
			<h4 align="center">Period : <xsl:value-of select="/report/date/attribute::from_month_year"/> to <xsl:value-of select="/report/date/attribute::to_month_year"/></h4>
 			<h4 align="center">Level: <xsl:value-of select="/report/header/attribute::level"/> Result: <xsl:value-of select="/report/header/attribute::result"/> Name : <xsl:value-of select="/report/header/attribute::name"/> Splited by: <xsl:value-of select="/report/header/attribute::split_by"/></h4>
		    <table frame="border" align="center">
		 		<tr>
		 			<th>Origin</th>
		 			<th>VG</th>
		 			<th>Sale Orders</th>
		 			<th>Tx Conv</th>
		 			<th>C.A</th>
		 			<th>Mmc</th>
				</tr>				 	
			 	<xsl:for-each select="report/origin">
			 		<tr>
			 			<td><xsl:value-of select="attribute::name" /></td>
			 			<td><xsl:value-of select="vg" /></td>
			 			<td align="right"><xsl:value-of select="so" /></td>
			 			<td><xsl:value-of select="tx_conv"/>%</td>
			 			<td align="right"><xsl:value-of select="format-number(ca,'##,##,###.##')"/></td>
			 			<td align="right"><xsl:value-of select="format-number(mmc,'##,##,###.##')" /></td>
					</tr>
				</xsl:for-each>
			</table>				
			<xsl:for-each select="report/story">	
			<xsl:variable name="s_id" select="attribute::s_id"/>
		    <h4 align="center"><xsl:value-of select="attribute::name"/></h4>
		    <table frame="border" >
					<tr>
				        <th>
				            <xsl:value-of select="//date/attribute::from_month_year" /> - <xsl:value-of select="//date/attribute::to_month_year" />
				        </th>
						<xsl:for-each select="//days/day">
				            <th><xsl:value-of select="attribute::string" /></th>
						</xsl:for-each>
						<th>Total</th>
					</tr>
				    <xsl:for-each select="row">
				    <xsl:variable name="id" select="attribute::id"/>
						<tr>
							<td nowrap="nowrap"><xsl:value-of select="attribute::name"/></td>
							<xsl:for-each select="//report/days/day">
							<xsl:variable name="today" select="attribute::number" />
		                    <td align="right">
									  <xsl:value-of select="format-number(sum(//story[@s_id=$s_id]/row[@id=$id]/time-element[@date=$today]), '##.##')" />
								</td>
							</xsl:for-each>
							<td align="right">
		        				    <xsl:value-of select="format-number(sum(//story[@s_id=$s_id]/row[@id=$id]/time-element),'##.##')"/>
							</td>
						</tr>
				    </xsl:for-each>
						<tr>
							<th align="left">Total</th>
								<xsl:for-each select="//report/days/day">
								<xsl:variable name="today" select="attribute::number"/>
									<th align="right">
					                	<xsl:value-of select="format-number(sum(//story[@s_id=$s_id]/row/time-element[@date=$today]),'##.##')"/>
								</th>
						</xsl:for-each>
						<th align="right"><xsl:value-of select="format-number(sum(//story[@s_id=$s_id]/row/time-element),'##.##')"/></th>
					</tr>
		    </table>
		</xsl:for-each>
	</body>
	</xsl:template>
</xsl:stylesheet>
