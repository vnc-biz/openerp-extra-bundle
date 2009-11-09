<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:import href="order_statistics_report_header1.xsl"/>
	<xsl:template match="/">
		<xsl:call-template name="rml" />
	</xsl:template>

	<xsl:template name="rml">
        <document filename="example.pdf">
		<xsl:apply-imports />		
		<stylesheet>
			<paraStyle name="normal1" fontName="Helvetica" fontSize="8" alignment="right" />		
			<paraStyle name="normal" fontName="Helvetica" fontSize="8" />
			<paraStyle name="normal-title" fontName="Helvetica-Bold" fontSize="9" />
			<paraStyle name="title" fontName="Helvetica" fontSize="18" alignment="center" />
			<paraStyle name="date" fontName="Helvetica-Oblique" fontSize="10" textColor="blue" />
			<paraStyle name="glande" textColor="red" fontSize="7" fontName="Helvetica"/>
			<paraStyle name="normal_people" textColor="green" fontSize="7" fontName="Helvetica"/>
			<paraStyle name="esclave" textColor="purple" fontSize="7" fontName="Helvetica"/>
			<blockTableStyle id="month">
				<blockAlignment value="CENTER" start="1,0" stop="-1,-1" />
				<lineStyle kind="LINEABOVE" colorName="#000000" start="0,0" stop="-1,-1" />
				<lineStyle kind="LINEBEFORE" colorName="#000000" start="0,0" stop="-1,-1"/>
				<lineStyle kind="LINEAFTER" colorName="#000000" start="-1,0" stop="-1,-1"/>
				<lineStyle kind="LINEBELOW" colorName="#000000" start="0,-1" stop="-1,-1"/>
				<blockValign value="TOP"/>
			</blockTableStyle>
		</stylesheet>
			<xsl:call-template name="story"/>
		</document>
	</xsl:template>

	<xsl:template name="story">
		<xsl:for-each select="report/story">	
		<xsl:variable name="s_id" select="attribute::s_id"/>
		<story>
		    <para style="title" t="1"> <xsl:value-of select="attribute::name"/> </para>
            <spacer length="1cm" />
		    <blockTable>
			    <xsl:attribute name="style">month</xsl:attribute>
                <xsl:attribute name="colWidths"><xsl:value-of select="//cols" /></xsl:attribute>
			    <tr>
                    <td>
                        <xsl:value-of select="//date/attribute::from_month_year" /> -
                        <xsl:value-of select="//date/attribute::to_month_year" /></td>
				    <xsl:for-each select="//days/day">
					    <td>
						    <xsl:value-of select="attribute::string" />
					    </td>
				    </xsl:for-each>
				    <td >Total</td>
			    </tr>
			    <xsl:apply-templates select="row"/>
			    <xsl:for-each select="row">
				    <xsl:variable name="id" select="attribute::id"/>
				    <tr>
					    <td><para><xsl:value-of select="attribute::name"/></para></td>
					    <xsl:for-each select="//report/days/day">
					    <xsl:variable name="today" select="attribute::number" />
                            <td>
                                <para>
								     <xsl:value-of select="format-number(sum(//story[@s_id=$s_id]/row[@id=$id]/time-element[@date=$today]), '##.##')" />
							    </para>
						    </td>
					    </xsl:for-each>
					    <td>
					        <para> 
            				     <xsl:value-of select="format-number(sum(//story[@s_id=$s_id]/row[@id=$id]/time-element),'##.##')"/>
        					</para>
					    </td>
				    </tr>
			    </xsl:for-each>
			    <tr>
				    <td t="1">Total</td>
				    <xsl:for-each select="//report/days/day">
					    <xsl:variable name="today" select="attribute::number"/>
					    <td>
                        <para><xsl:value-of select="format-number(sum(//story[@s_id=$s_id]/row/time-element[@date=$today]),'##.##')"/></para>
					    </td>
				    </xsl:for-each>
				    <td><xsl:value-of select="format-number(sum(//story[@s_id=$s_id]/row/time-element),'##.##')"/></td>
			    </tr>
            </blockTable>
    	</story>
	</xsl:for-each>
	
	</xsl:template>
</xsl:stylesheet>
