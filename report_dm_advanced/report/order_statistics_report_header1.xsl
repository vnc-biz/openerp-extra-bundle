<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

	<xsl:template match="/">
        <template>
			<xsl:variable name="twidth" select="/report/cols/attribute::twidth" />
            <xsl:attribute name="pageSize">
                <xsl:value-of select="format-number( $twidth + 20,'#####.##')"/>cm,50cm</xsl:attribute>
            <xsl:attribute name="title">Test</xsl:attribute>
            <xsl:attribute name="author">Martin Simon</xsl:attribute>
            <xsl:attribute name="allowSplitting">20</xsl:attribute>
			<pageTemplate>
		        <frame>
		            <xsl:attribute name="id">first</xsl:attribute>
		            <xsl:attribute name="x1">10cm</xsl:attribute>
		            <xsl:attribute name="y1">2.5cm</xsl:attribute>
		            <xsl:attribute name="width">
						<xsl:value-of select="format-number( $twidth,'####.##')"/>cm</xsl:attribute>
		            <xsl:attribute name="height">43cm</xsl:attribute>
		        </frame>
				<pageGraphics>
					<xsl:variable name="cpoint" select=" ($twidth + 20 ) div 2" />
					<setFont name="Helvetica" size="25"/>
					<fill color="black"/>
					<stroke color="black"/>
					<drawCentredString>
			            <xsl:attribute name="x">
			                <xsl:value-of select="format-number( $cpoint,'####.##')"/>cm</xsl:attribute>
			            <xsl:attribute name="y">48.5cm</xsl:attribute>Period : <xsl:value-of select="/report/date/attribute::from_month_year"/> to <xsl:value-of select="/report/date/attribute::to_month_year"/></drawCentredString>
					<setFont name="Helvetica" size="18"/>
					<drawCentredString>
			            <xsl:attribute name="x">
			                <xsl:value-of select="$cpoint"/>cm</xsl:attribute>
			            <xsl:attribute name="y">47.5cm</xsl:attribute>Level: <xsl:value-of select="/report/header/attribute::level"/> Result: <xsl:value-of select="/report/header/attribute::result"/> Name : <xsl:value-of select="/report/header/attribute::name"/> Splited by: <xsl:value-of select="/report/header/attribute::split_by"/></drawCentredString>
				</pageGraphics>
			</pageTemplate>
		</template>	
	</xsl:template>
</xsl:stylesheet>
