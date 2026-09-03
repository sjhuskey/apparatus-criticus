<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:math="http://www.w3.org/2005/xpath-functions/math"
    xmlns:tei="http://www.tei-c.org/ns/1.0"
    exclude-result-prefixes="xs math tei"
    version="3.0">
    
    <xsl:template match="/">
        <xsl:apply-templates select="//tei:div[@type='bibliography']"/>
    </xsl:template>
    
    <xsl:template match="//tei:listWit[@xml:id='editions-witnesses']">
        <xsl:for-each select=".//tei:witness">
            <xsl:text>{&#10;</xsl:text>
            <xsl:text>"siglum": "</xsl:text><xsl:value-of select="normalize-space(@xml:id)"/><xsl:text>",&#10;</xsl:text>
            <xsl:text>"editor": "</xsl:text><xsl:value-of select="normalize-space(./tei:bibl/tei:editor/tei:name/text())"/><xsl:text>",&#10;</xsl:text>
            <xsl:choose>
                <xsl:when test="./tei:bibl/tei:title[normalize-space()][2]">
                    <xsl:text>"title": "</xsl:text><xsl:value-of select="normalize-space(./tei:bibl/tei:title[1])"/><xsl:text>",&#10;</xsl:text>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>"title": "</xsl:text><xsl:value-of select="normalize-space(./tei:bibl/tei:title)"/><xsl:text>",&#10;</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
            <xsl:text>"place": "</xsl:text><xsl:value-of select="normalize-space(./tei:bibl/tei:pubPlace)"/><xsl:text>",&#10;</xsl:text>
            <xsl:text>"publisher": "</xsl:text><xsl:value-of select="normalize-space(./tei:bibl/tei:publisher)"/><xsl:text>",&#10;</xsl:text>
            <xsl:text>"date": "</xsl:text><xsl:value-of select="normalize-space(./tei:bibl/tei:date)"/><xsl:text>",&#10;</xsl:text>
            <xsl:if test="./tei:ptr">
                <xsl:text>"url": "</xsl:text><xsl:value-of select="normalize-space(./tei:ptr/@target)"/><xsl:text>",&#10;</xsl:text>
            </xsl:if>
            <xsl:text>}&#10;</xsl:text>
        </xsl:for-each>
    </xsl:template>
    
    <xsl:template match="//tei:listBibl[@xml:id='editions-sources']">
        <xsl:for-each select=".//tei:bibl">
            <xsl:text>{&#10;</xsl:text>
            <xsl:text>"siglum": "</xsl:text><xsl:value-of select="normalize-space(@xml:id)"/><xsl:text>",&#10;</xsl:text>
            <xsl:text>"editor": "</xsl:text><xsl:value-of select="normalize-space(./tei:editor)"/><xsl:text>",&#10;</xsl:text>
            <xsl:choose>
                <xsl:when test="./tei:title[normalize-space()][2]">
                    <xsl:text>"title": "</xsl:text><xsl:value-of select="normalize-space(./tei:title[1])"/><xsl:text>",&#10;</xsl:text>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>"title": "</xsl:text><xsl:value-of select="normalize-space(./tei:title)"/><xsl:text>",&#10;</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
            <xsl:text>"place": "</xsl:text><xsl:value-of select="normalize-space(./tei:pubPlace)"/><xsl:text>",&#10;</xsl:text>
            <xsl:text>"publisher": "</xsl:text><xsl:value-of select="normalize-space(./tei:publisher)"/><xsl:text>",&#10;</xsl:text>
            <xsl:text>"date": "</xsl:text><xsl:value-of select="normalize-space(./tei:date)"/><xsl:text>",&#10;</xsl:text>
            <xsl:if test="./tei:ptr">
                <xsl:text>"url": "</xsl:text><xsl:value-of select="normalize-space(./tei:ptr/@target)"/><xsl:text>",&#10;</xsl:text>
            </xsl:if>
            <xsl:text>}&#10;</xsl:text>
        </xsl:for-each>
    </xsl:template>
    
    <xsl:template match="//tei:listBibl[@xml:id='secondary-sources']">
        <xsl:for-each select=".//tei:bibl">
            <xsl:text>{&#10;</xsl:text>
            <xsl:if test="./tei:editor">
                <xsl:text>"editor": "</xsl:text><xsl:value-of select="normalize-space(.)"/><xsl:text>",&#10;</xsl:text>
            </xsl:if>
            <xsl:for-each select="./tei:author">
                <xsl:text>"author": "</xsl:text><xsl:value-of select="normalize-space(.)"/><xsl:text>",&#10;</xsl:text>
            </xsl:for-each>
            <xsl:for-each select="./tei:title">
                <xsl:choose>
                    <xsl:when test="@level='a'">
                        <xsl:text>"article_title": "</xsl:text><xsl:value-of select="normalize-space(.)"/><xsl:text>",&#10;</xsl:text>
                    </xsl:when>
                    <xsl:when test="@level='j'">
                        <xsl:text>"journal_title": "</xsl:text><xsl:value-of select="normalize-space(.)"/><xsl:text>",&#10;</xsl:text>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>"title": "</xsl:text><xsl:value-of select="normalize-space(.)"/><xsl:text>",&#10;</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:for-each>
                <xsl:if test="./tei:biblScope[@unit='volume']">
                    <xsl:text>"volume": "</xsl:text><xsl:value-of select="normalize-space(./tei:biblScope[@unit='volume'])"/><xsl:text>",&#10;</xsl:text>
                </xsl:if>
                <xsl:if test="./tei:biblScope[@unit='page']">
                    <xsl:text>"pagination": "</xsl:text><xsl:value-of select="normalize-space(./tei:biblScope[@unit='page'])"/><xsl:text>",&#10;</xsl:text>
                </xsl:if>
                <xsl:if test="./tei:pubPlace">
                    <xsl:text>"place": "</xsl:text><xsl:value-of select="normalize-space(./tei:pubPlace)"/><xsl:text>",&#10;</xsl:text>
                </xsl:if>
                <xsl:if test="./tei:publisher">
                    <xsl:text>"publisher": "</xsl:text><xsl:value-of select="normalize-space(./tei:publisher)"/><xsl:text>",&#10;</xsl:text>
                </xsl:if>
                <xsl:text>"date": "</xsl:text><xsl:value-of select="normalize-space(./tei:date)"/><xsl:text>",&#10;</xsl:text>
                <xsl:if test="./tei:ptr">
                    <xsl:text>"url": "</xsl:text><xsl:value-of select="normalize-space(./tei:ptr/@target)"/><xsl:text>",&#10;</xsl:text>
                </xsl:if>
            <xsl:text>}&#10;</xsl:text>
        </xsl:for-each>
    </xsl:template>
    
    <xsl:template match="//tei:listPerson[@xml:id='scholars']">
        <xsl:for-each select="./tei:person">
            <xsl:text>{&#10;</xsl:text>
            <xsl:text>"uri": "</xsl:text><xsl:value-of select="normalize-space(./tei:persName/@ref)"/><xsl:text>",&#10;</xsl:text>
            <xsl:text>"abbreviation": "</xsl:text><xsl:value-of select="normalize-space(././tei:persName/tei:abbr)"/><xsl:text>",&#10;</xsl:text>
            <xsl:text>"name": "</xsl:text><xsl:value-of select="normalize-space(./tei:persName/text()[last()])"/><xsl:text>",&#10;</xsl:text>
          
            <xsl:choose>
                <xsl:when test="./tei:note/tei:bibl">
                    <xsl:text>"note": "See citation",&#10;</xsl:text>
                    <xsl:text>"citation": {&#10;</xsl:text>
                    <xsl:text>"author": "</xsl:text><xsl:value-of select="./normalize-space(./tei:note/tei:bibl/tei:author)"/><xsl:text>",&#10;</xsl:text>
                    <xsl:text>"title": "</xsl:text><xsl:value-of select="./normalize-space(./tei:note/tei:bibl/tei:title)"/><xsl:text>",&#10;</xsl:text>
                    <xsl:text>"place": "</xsl:text><xsl:value-of select="./normalize-space(./tei:note/tei:bibl/tei:pubPlace)"/><xsl:text>",&#10;</xsl:text>
                    <xsl:text>"publisher": "</xsl:text><xsl:value-of select="./normalize-space(./tei:note/tei:bibl/tei:publisher)"/><xsl:text>",&#10;</xsl:text>
                    <xsl:text>"date": "</xsl:text><xsl:value-of select="./normalize-space(./tei:note/tei:bibl/tei:date)"/><xsl:text>",&#10;</xsl:text>
                    <xsl:text>"url": "</xsl:text><xsl:value-of select="./normalize-space(./tei:note/tei:bibl/tei:ptr/@target)"/><xsl:text>",&#10;</xsl:text>
                    <xsl:text>}&#10;</xsl:text>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>"note": "</xsl:text><xsl:value-of select="normalize-space(string(./tei:note))"/><xsl:text>",&#10;</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
            <xsl:text>}&#10;</xsl:text>
        </xsl:for-each>
    </xsl:template>
    
    
</xsl:stylesheet>