<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

	<xsl:template match="/">
        <template>
			<xsl:variable name="twidth" select="/report/cols/attribute::twidth" />
            <xsl:attribute name="pageSize">
                <xsl:value-of select="$twidth + 20"/>cm,25.0cm</xsl:attribute>
            <xsl:attribute name="title">Test</xsl:attribute>
            <xsl:attribute name="author">Martin Simon</xsl:attribute>
            <xsl:attribute name="allowSplitting">20</xsl:attribute>
			<pageTemplate>
		        <frame>
		            <xsl:attribute name="id">first</xsl:attribute>
		            <xsl:attribute name="x1">10cm</xsl:attribute>
		            <xsl:attribute name="y1">0cm</xsl:attribute>
		            <xsl:attribute name="width">
						<xsl:value-of select="$twidth"/>cm</xsl:attribute>
		            <xsl:attribute name="height">17cm</xsl:attribute>
		        </frame>
				<pageGraphics>
					<xsl:variable name="cpoint" select=" ($twidth +20 ) div 2" />
					<setFont name="Helvetica" size="8"/>
					<fill color="black"/>
					<stroke color="black"/>
					<drawCentredString>
			            <xsl:attribute name="x">
			                <xsl:value-of select="$cpoint"/>cm</xsl:attribute>
			            <xsl:attribute name="y">23.2cm</xsl:attribute>Perio : <xsl:value-of select="/report/date/attribute::from_month_year"/> to <xsl:value-of select="/report/date/attribute::to_month_year"/></drawCentredString>
					<drawCentredString>
			            <xsl:attribute name="x">
			                <xsl:value-of select="$cpoint"/>cm</xsl:attribute>
			            <xsl:attribute name="y">22.8cm</xsl:attribute>Level: <xsl:value-of select="/report/header/attribute::level"/> Result: <xsl:value-of select="/report/header/attribute::result"/> Name : <xsl:value-of select="/report/header/attribute::name"/> Splited by: <xsl:value-of select="/report/header/attribute::split_by"/></drawCentredString>
					 <place x="10cm" y="13.5cm" width="900.0" height="8cm">
					 	<blockTable colWidths="400.0,78,85,78,78,78" style="month">
					 		<tr>
					 			<td><para style="normal-title" >Origin</para></td>
					 			<td><para style="normal-title" >VG</para></td>
					 			<td><para style="normal-title" >Sale Orders</para></td>
					 			<td><para style="normal-title" >Tx Conv</para></td>
					 			<td><para style="normal-title" >C.A</para></td>
					 			<td><para style="normal-title" >Mmc</para></td>
							</tr>				 	
						 	<xsl:for-each select="/report/origin">
						 		<tr>
						 			<td><para style="normal"><xsl:value-of select="attribute::name" /></para></td>
						 			<td><para style="normal1"><xsl:value-of select="vg" /></para></td>
						 			<td><para style="normal1"><xsl:value-of select="so" /></para></td>
						 			<td><para style="normal1"><xsl:value-of select="tx_conv"/>%</para></td>
						 			<td><para style="normal1"><xsl:value-of select="format-number(ca,'##,##,###.##')"/></para></td>
						 			<td><para style="normal1"><xsl:value-of select="format-number(mmc,'##,##,###.##')" /></para></td>
								</tr>
							</xsl:for-each>
						 </blockTable>
					 </place>
				</pageGraphics>
			</pageTemplate>
		</template>	
	</xsl:template>
</xsl:stylesheet>
