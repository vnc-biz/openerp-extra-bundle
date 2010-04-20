<?php
/**
 * @copyright (C) 2010 BCIM sprl. All rights reserved.
 * @license GNU/GPL
 */

// no direct access
defined( '_JEXEC' ) or die( 'Restricted access' );

jimport( 'joomla.plugin.plugin' );
require_once (JPATH_ADMINISTRATOR.DS.'components'.DS.'com_virtuemart'.DS.'virtuemart.cfg.php');


function trace($s) {
  $plugin =& JPluginHelper::getPlugin('xmlrpc','openerp2vm');
  $params = new JParameter( $plugin->params );
  $config = new JConfig();
  $f=$params->get('logfile');
  if($f){
    $fp = fopen($config->log_path.DS.$f, "a");
    fwrite($fp, $s."\n");
    fclose($fp);
  }
}
function debug($s) {
  trace(" | ".$s);
}
function debugfn($s) {
  trace("-- Call to function '".$s."' -----------------------------------------------");
}
function query($db,$s,$run=1) {
  $db->setQuery($s);
  if($run) {
    $db->query();
  }
  debug("query: ".$db->_sql);
}

class plgXMLRPCOpenERP2Vm extends JPlugin {
    function plgXMLRPCOpenERP2Vm(&$subject, $config) {
        parent::__construct($subject, $config);
        //$this->loadLanguage( '', JPATH_ADMINISTRATOR );
    }

    /**
    * @return array An array of associative arrays defining the available methods
    */
    function onGetWebServices() {
        global $xmlrpcI4, $xmlrpcInt, $xmlrpcBoolean, $xmlrpcDouble, $xmlrpcString, $xmlrpcDateTime, $xmlrpcBase64, $xmlrpcArray, $xmlrpcStruct, $xmlrpcValue;

        return array(
            "openerp2vm.get_languages" => array(
                "function" => "plgXMLRPCOpenERP2VmServices::get_languages",
                "docstring" => JText::_('Export the languages.'),
                "signature" => array(array($xmlrpcStruct,$xmlrpcString,$xmlrpcString))
                ),
            "openerp2vm.get_translation" => array(
                "function" => "plgXMLRPCOpenERP2VmServices::get_translation",
                "docstring" => JText::_('Export the translation of a field.'),
                "signature" => array(array($xmlrpcArray,$xmlrpcString,$xmlrpcString,$xmlrpcInt,$xmlrpcString,$xmlrpcString,$xmlrpcInt))
                ),
            "openerp2vm.set_translation" => array(
                "function" => "plgXMLRPCOpenERP2VmServices::set_translation",
                "docstring" => JText::_('Import the translation of a field.'),
                "signature" => array(array($xmlrpcBoolean,$xmlrpcString,$xmlrpcString,$xmlrpcInt,$xmlrpcString,$xmlrpcString,$xmlrpcInt,$xmlrpcString))
                ),

            "openerp2vm.get_categories" => array(
                "function" => "plgXMLRPCOpenERP2VmServices::get_categories",
                "docstring" => JText::_('Export the categories.'),
                "signature" => array(array($xmlrpcArray,$xmlrpcString,$xmlrpcString))
                ),
            "openerp2vm.set_category" => array(
                "function" => "plgXMLRPCOpenERP2VmServices::set_category",
                "docstring" => JText::_('Import a category.'),
                "signature" => array(array($xmlrpcInt,$xmlrpcString,$xmlrpcString,$xmlrpcStruct))
                ),
            "openerp2vm.set_categories_parents" => array(
                "function" => "plgXMLRPCOpenERP2VmServices::set_categories_parents",
                "docstring" => JText::_('Set the categories structure.'),
                "signature" => array(array($xmlrpcInt,$xmlrpcString,$xmlrpcString,$xmlrpcArray))
                ),
            "openerp2vm.delete_category" => array(
                "function" => "plgXMLRPCOpenERP2VmServices::delete_category",
                "docstring" => JText::_('Delete a category.'),
                "signature" => array(array($xmlrpcInt,$xmlrpcString,$xmlrpcString,$xmlrpcInt))
                ),

            "openerp2vm.get_taxes" => array(
                "function" => "plgXMLRPCOpenERP2VmServices::get_taxes",
                "docstring" => JText::_('Export the taxes.'),
                "signature" => array(array($xmlrpcArray,$xmlrpcString,$xmlrpcString))
                ),
            "openerp2vm.set_tax" => array(
                "function" => "plgXMLRPCOpenERP2VmServices::set_tax",
                "docstring" => JText::_('Import a tax.'),
                "signature" => array(array($xmlrpcInt,$xmlrpcString,$xmlrpcString,$xmlrpcStruct))
                ),
            "openerp2vm.delete_tax" => array(
                "function" => "plgXMLRPCOpenERP2VmServices::delete_tax",
                "docstring" => JText::_('Delete a tax.'),
                "signature" => array(array($xmlrpcInt,$xmlrpcString,$xmlrpcString,$xmlrpcInt))
                ),

            "openerp2vm.get_producttypes" => array(
                "function" => "plgXMLRPCOpenERP2VmServices::get_producttypes",
                "docstring" => JText::_('Export the product types and their attributes.'),
                "signature" => array(array($xmlrpcArray,$xmlrpcString,$xmlrpcString))
                ),

            "openerp2vm.set_product" => array(
                "function" => "plgXMLRPCOpenERP2VmServices::set_product",
                "docstring" => JText::_('Import a product.'),
                "signature" => array(array($xmlrpcInt,$xmlrpcString,$xmlrpcString,$xmlrpcStruct))
                ),
            "openerp2vm.delete_product" => array(
                "function" => "plgXMLRPCOpenERP2VmServices::delete_product",
                "docstring" => JText::_('Delete a product.'),
                "signature" => array(array($xmlrpcInt,$xmlrpcString,$xmlrpcString,$xmlrpcInt))
                ),

            "openerp2vm.set_stock" => array(
                "function" => "plgXMLRPCOpenERP2VmServices::set_stock",
                "docstring" => JText::_('Update a product stock quantity.'),
                "signature" => array(array($xmlrpcInt,$xmlrpcString,$xmlrpcString,$xmlrpcStruct))
                ),

            "openerp2vm.get_orders" => array(
                "function" => "plgXMLRPCOpenERP2VmServices::get_orders",
                "docstring" => JText::_('Export the sale orders.'),
                "signature" => array(array($xmlrpcArray,$xmlrpcString,$xmlrpcString))
                ),
        );
    }
}

class plgXMLRPCOpenERP2VmServices {
    function get_languages($username,$password) {
        global $mainframe, $xmlrpcerruser, $xmlrpcI4, $xmlrpcInt, $xmlrpcBoolean, $xmlrpcDouble, $xmlrpcString, $xmlrpcDateTime, $xmlrpcBase64, $xmlrpcArray, $xmlrpcStruct, $xmlrpcValue;
        if(!plgXMLRPCOpenERP2VmHelper::authenticateUser($username, $password)) {
            debug('login failed ('.$username.')');
            return new xmlrpcresp(0, $xmlrpcerruser+1, JText::_("Login Failed"));
        }
        $db =& JFactory::getDBO();
        $languages = array();
        query($db,"select id,shortcode from #__languages where active=1;",0);
        foreach($db->loadObjectList() as $row) {
            $languages[$row->shortcode]=new xmlrpcval($row->id, $xmlrpcInt);
        }
        return new xmlrpcresp( new xmlrpcval($languages, $xmlrpcStruct));
    }
    function get_translation($username,$password,$lang_id,$rtable,$rfield,$rid) {
        global $mainframe, $xmlrpcerruser, $xmlrpcI4, $xmlrpcInt, $xmlrpcBoolean, $xmlrpcDouble, $xmlrpcString, $xmlrpcDateTime, $xmlrpcBase64, $xmlrpcArray, $xmlrpcStruct, $xmlrpcValue;
        if(!plgXMLRPCOpenERP2VmHelper::authenticateUser($username, $password)) {
            return new xmlrpcresp(0, $xmlrpcerruser+1, JText::_("Login Failed"));
        }
        $db =& JFactory::getDBO();
        query($db,"select value from #__jf_content where language_id=".$lang_id." and reference_table='".$rtable."' and reference_field='".$rfield."' and reference_id=".$rid.";",0);
        if($row=$db->loadObject()) {
            $value=$row->value;
            $r=array(new xmlrpcval(1, $xmlrpcBoolean),new xmlrpcval($value, $xmlrpcString));
        } else {
            $r=array(new xmlrpcval(0, $xmlrpcBoolean),new xmlrpcval('', $xmlrpcString));
        }
        return new xmlrpcresp( new xmlrpcval($r, $xmlrpcArray));
    }
    function set_translation($username,$password,$lang_id,$rtable,$rfield,$rid,$value) {
        global $mainframe, $xmlrpcerruser, $xmlrpcI4, $xmlrpcInt, $xmlrpcBoolean, $xmlrpcDouble, $xmlrpcString, $xmlrpcDateTime, $xmlrpcBase64, $xmlrpcArray, $xmlrpcStruct, $xmlrpcValue;
        if(!plgXMLRPCOpenERP2VmHelper::authenticateUser($username, $password)) {
            return new xmlrpcresp(0, $xmlrpcerruser+1, JText::_("Login Failed"));
        }
        $db =& JFactory::getDBO();
        query($db,"select id from #__jf_content where language_id=".$lang_id." and reference_table='".$rtable."' and reference_field='".$rfield."' and reference_id=".$rid.";");
        if($db->getNumRows()) {
            query($db,"update #__jf_content set value='".$value."', published=1 where language_id=".$lang_id." and reference_table='".$rtable."' and reference_field='".$rfield."' and reference_id=".$rid.";");
        }
        else {
            query($db,"insert into #__jf_content (language_id,reference_table,reference_field,reference_id,value,published) values (".$lang_id.",'".$rtable."','".$rfield."',".$rid.",'".$value."',1);");
        }
        return new xmlrpcresp(new xmlrpcval(1, $xmlrpcBoolean));
    }

    function _parent_category_id($id) {
        $db =& JFactory::getDBO();
        $parent=0;
        query($db,"select category_parent_id from #__vm_category_xref where category_child_id=".$id.";",0);
        foreach($db->loadObjectList() as $row) {
            $parent=$row->category_parent_id;
        }
        return $parent;
    }
    function get_categories($username,$password) {
        global $mainframe, $xmlrpcerruser, $xmlrpcI4, $xmlrpcInt, $xmlrpcBoolean, $xmlrpcDouble, $xmlrpcString, $xmlrpcDateTime, $xmlrpcBase64, $xmlrpcArray, $xmlrpcStruct, $xmlrpcValue;
        if(!plgXMLRPCOpenERP2VmHelper::authenticateUser($username, $password)) {
            return new xmlrpcresp(0, $xmlrpcerruser+1, JText::_("Login Failed"));
        }
        $db =& JFactory::getDBO();
        $categories=array();
        query($db,"select category_id, category_name from #__vm_category;",0);
        foreach($db->loadObjectList() as $row) {
            $name = urlencode($row->category_name);
            $categories[] = new xmlrpcval(array(new xmlrpcval($row->category_id, $xmlrpcInt), new xmlrpcval($name, $xmlrpcString), new xmlrpcval(plgXMLRPCOpenERP2VmServices::_parent_category_id($row->category_id), $xmlrpcInt)), $xmlrpcArray);
    #path,id,name,parent
        }
        return new xmlrpcresp( new xmlrpcval($categories, $xmlrpcArray));
    }
    function set_category($username,$password,$cat){
        global $mainframe, $xmlrpcerruser, $xmlrpcI4, $xmlrpcInt, $xmlrpcBoolean, $xmlrpcDouble, $xmlrpcString, $xmlrpcDateTime, $xmlrpcBase64, $xmlrpcArray, $xmlrpcStruct, $xmlrpcValue;
        if(!plgXMLRPCOpenERP2VmHelper::authenticateUser($username, $password)) {
            return new xmlrpcresp(0, $xmlrpcerruser+1, JText::_("Login Failed"));
        }
        $db =& JFactory::getDBO();
        $insert=1;
        $id=$cat['id'];
        debug('id='.$id);
        if($id) {
            query($db,"select category_id from #__vm_category where category_id=".$id.";");
            if($db->getNumRows()) {
                query($db,"update #__vm_category set category_name='".$cat['name']."' where category_id=".$id.";");
                $insert=0;
            }
        }
        if($insert) {
            query($db,"insert into #__vm_category (category_name,category_publish,vendor_id,category_browsepage,products_per_row,category_flypage) values ('".$cat['name']."','Y','1','".CATEGORY_TEMPLATE."','".PRODUCTS_PER_ROW."','".FLYPAGE."');");
            $id=$db->insertid();
            debug('  new id='.$id);
        }
        return new xmlrpcresp(new xmlrpcval($id, $xmlrpcInt));
    }
    function set_categories_parents($username,$password,$categories){
        global $mainframe, $xmlrpcerruser, $xmlrpcI4, $xmlrpcInt, $xmlrpcBoolean, $xmlrpcDouble, $xmlrpcString, $xmlrpcDateTime, $xmlrpcBase64, $xmlrpcArray, $xmlrpcStruct, $xmlrpcValue;
        if(!plgXMLRPCOpenERP2VmHelper::authenticateUser($username, $password)) {
            return new xmlrpcresp(0, $xmlrpcerruser+1, JText::_("Login Failed"));
        }
        $db =& JFactory::getDBO();
        foreach($categories as $cat) {
            debug('id='.$cat['child']);
            query($db,"select category_child_id from #__vm_category_xref where category_child_id=".$cat['child'].";");
            if($db->getNumRows()) {
                query($db,"update #__vm_category_xref set category_parent_id='".$cat['parent']."' where category_child_id=".$cat['child'].";");
            } else {
                query($db,"insert into #__vm_category_xref (category_parent_id,category_child_id) values (".$cat['parent'].",".$cat['child'].");");
            }
        }
        return new xmlrpcresp(new xmlrpcval(1,$xmlrpcInt));
    }
    function delete_category($username,$password,$id) {
        global $mainframe, $xmlrpcerruser, $xmlrpcI4, $xmlrpcInt, $xmlrpcBoolean, $xmlrpcDouble, $xmlrpcString, $xmlrpcDateTime, $xmlrpcBase64, $xmlrpcArray, $xmlrpcStruct, $xmlrpcValue;
        if(!plgXMLRPCOpenERP2VmHelper::authenticateUser($username, $password)) {
            return new xmlrpcresp(0, $xmlrpcerruser+1, JText::_("Login Failed"));
        }
        $db =& JFactory::getDBO();
        query($db,"delete from #__vm_category where category_id=".$id.";");
        query($db,"delete from #__vm_category_xref where category_child_id=".$id.";");
        return new xmlrpcresp(new xmlrpcval(1, $xmlrpcInt));
    }

    function get_taxes($username,$password) {
        global $mainframe, $xmlrpcerruser, $xmlrpcI4, $xmlrpcInt, $xmlrpcBoolean, $xmlrpcDouble, $xmlrpcString, $xmlrpcDateTime, $xmlrpcBase64, $xmlrpcArray, $xmlrpcStruct, $xmlrpcValue;
        if(!plgXMLRPCOpenERP2VmHelper::authenticateUser($username, $password)) {
            return new xmlrpcresp(0, $xmlrpcerruser+1, JText::_("Login Failed"));
        }
        $db =& JFactory::getDBO();
        $taxes=array();
        query($db,"select t.tax_rate_id, c.country_2_code, t.tax_rate from #__vm_tax_rate t, #__vm_country c where t.tax_country=c.country_3_code;",0);
        foreach($db->loadRowList() as $row) {
            $taxes[]=new xmlrpcval(array(new xmlrpcval($row[0], $xmlrpcInt), new xmlrpcval($row[1], $xmlrpcString), new xmlrpcval($row[2], $xmlrpcString)), $xmlrpcArray);
        }
        return new xmlrpcresp( new xmlrpcval($taxes, $xmlrpcArray));
    }

    function set_tax($username,$password,$tax){
        global $mainframe, $xmlrpcerruser, $xmlrpcI4, $xmlrpcInt, $xmlrpcBoolean, $xmlrpcDouble, $xmlrpcString, $xmlrpcDateTime, $xmlrpcBase64, $xmlrpcArray, $xmlrpcStruct, $xmlrpcValue;
        if(!plgXMLRPCOpenERP2VmHelper::authenticateUser($username, $password)) {
            return new xmlrpcresp(0, $xmlrpcerruser+1, JText::_("Login Failed"));
        }
        $db =& JFactory::getDBO();
        $insert=1;
        $id=$tax['id'];
        debug('id='.$id);
        if($id) {
            query($db,"select tax_rate_id from #__vm_tax_rate where tax_rate_id=".$id.";");
            if($db->getNumRows()) {
                query($db,"update #__vm_tax_rate set tax_country=(select country_3_code from #__vm_country where country_2_code='".$tax['country']."'), tax_rate='".$tax['rate']."' where tax_rate_id=".$id.";");
                $insert=0;
            }
        }
        if($insert) {
            query($db,"insert into #__vm_tax_rate (tax_country,tax_rate,vendor_id) select country_3_code,'".$tax['rate']."','1' from #__vm_country where country_2_code='".$tax['country']."';");
            $id=$db->insertid();
            debug('  new id='.$id);
        }
        return new xmlrpcresp(new xmlrpcval($id, $xmlrpcInt));
    }

    function delete_tax($username,$password,$id) {
        global $mainframe, $xmlrpcerruser, $xmlrpcI4, $xmlrpcInt, $xmlrpcBoolean, $xmlrpcDouble, $xmlrpcString, $xmlrpcDateTime, $xmlrpcBase64, $xmlrpcArray, $xmlrpcStruct, $xmlrpcValue;
        if(!plgXMLRPCOpenERP2VmHelper::authenticateUser($username, $password)) {
            return new xmlrpcresp(0, $xmlrpcerruser+1, JText::_("Login Failed"));
        }
        $db =& JFactory::getDBO();
        query($db,"delete from #__vm_tax_rate where tax_rate_id=".$id.";");
        return new xmlrpcresp(new xmlrpcval(1, $xmlrpcInt));
    }

    function get_producttypes($username,$password) {
        global $mainframe, $xmlrpcerruser, $xmlrpcI4, $xmlrpcInt, $xmlrpcBoolean, $xmlrpcDouble, $xmlrpcString, $xmlrpcDateTime, $xmlrpcBase64, $xmlrpcArray, $xmlrpcStruct, $xmlrpcValue;
        if(!plgXMLRPCOpenERP2VmHelper::authenticateUser($username, $password)) {
            return new xmlrpcresp(0, $xmlrpcerruser+1, JText::_("Login Failed"));
        }
        $db =& JFactory::getDBO();
        $types=array();
        query($db,"select product_type_id, product_type_name from #__vm_product_type;",0);
        foreach($db->loadRowList() as $row) {
            query($db,"select parameter_name, parameter_label from #__vm_product_type_parameter where product_type_id='".$row[0]."';",0);
            $params=array();
            foreach($db->loadRowList() as $row2) {
                $params[]=new xmlrpcval(array(new xmlrpcval($row2[0], $xmlrpcString), new xmlrpcval($row2[1], $xmlrpcString)), $xmlrpcArray);
            }
            $types[]=new xmlrpcval(array(new xmlrpcval($row[0], $xmlrpcInt), new xmlrpcval($row[1], $xmlrpcString), new xmlrpcval($params, $xmlrpcArray)), $xmlrpcArray);
        }
        return new xmlrpcresp( new xmlrpcval($types, $xmlrpcArray));
    }

    function set_product($username,$password,$product){
        global $mainframe, $xmlrpcerruser, $xmlrpcI4, $xmlrpcInt, $xmlrpcBoolean, $xmlrpcDouble, $xmlrpcString, $xmlrpcDateTime, $xmlrpcBase64, $xmlrpcArray, $xmlrpcStruct, $xmlrpcValue;
        if(!plgXMLRPCOpenERP2VmHelper::authenticateUser($username, $password)) {
            return new xmlrpcresp(0, $xmlrpcerruser+1, JText::_("Login Failed"));
        }
        $db =& JFactory::getDBO();
        $values=array();
        $values[]=array("product_sku",mysql_escape_string($product['sku']));
        $values[]=array("product_s_desc",mysql_escape_string($product['s_desc']));
        $values[]=array("product_desc",mysql_escape_string($product['desc']));
        $values[]=array("product_thumb_image",mysql_escape_string($product['image']));
        $values[]=array("product_full_image",mysql_escape_string($product['image']));
        $values[]=array("product_publish",mysql_escape_string($product['publish']));
        $values[]=array("product_weight",$product['weight']);
        $values[]=array("product_length",$product['length']);
        $values[]=array("product_width",$product['width']);
        $values[]=array("product_height",$product['height']);
        $values[]=array("product_url",mysql_escape_string($product['url']));
        $values[]=array("product_in_stock",$product['in_stock']);
        $values[]=array("product_special",mysql_escape_string($product['special']));
        $values[]=array("product_discount_id",0);
        $values[]=array("product_name",mysql_escape_string($product['name']));
        $values[]=array("attribute","");
        $values[]=array("product_tax_id",$product['tax_id']);
        $values[]=array("product_unit","");
        $values[]=array("product_packaging",$product['packaging']);
        $values[]=array("vendor_id",1);
        $insert=1;
        $id=$product['id'];
        if($id) {
            query($db,"select product_id from #__vm_product where product_id=".$id.";");
            if($db->getNumRows()) {
                $insert=0;
                $q="update #__vm_product set ";
                $f=array();
                foreach($values as $v) {
                    $f[]=$v[0]."='".$v[1]."'";
                }
                $q.=join(",",$f);
                $q.=" where product_id='".$product['id']."';";
                query($db,$q);
                $q="update #__vm_product_price set";
                $q.=" product_price='".$product['price']."'";
                $q.=",product_currency='".mysql_escape_string($product['currency'])."'";
                $q.=",product_price_vdate='0',product_price_edate='0'";
                $q.=",shopper_group_id=(select shopper_group_id from #__vm_shopper_group shopper where shopper.vendor_id='1' and shopper.default='1')";
                $q.=" where product_id='".$product['id']."';";
                query($db,$q);
            }
        }
        if($insert) {
            $q="insert into #__vm_product ";
            $f1=array();
            $f2=array();
            foreach($values as $v) {
                $f1[]=$v[0];
                $f2[]="'".$v[1]."'";
            }
            $q.="(".join(",",$f1).") values (".join(",",$f2).");";
            query($db,$q);
            $id=$db->insertid();
            debug('  new id='.$id);
            query($db,"delete from #__vm_product_price where product_id='".$id."';");
            $q="insert into #__vm_product_price ";
            $q.="(product_id,product_price,product_currency,product_price_vdate,product_price_edate,shopper_group_id) ";
            $q.="select '".$id."','".$product['price']."','".mysql_escape_string($product['currency'])."','0','0',shopper_group_id from #__vm_shopper_group shopper where shopper.vendor_id='1' and shopper.default='1';";
            query($db,$q);
            query($db,"delete from #__vm_product_mf_xref where product_id='".$product['id']."';");
            $q="insert into #__vm_product_mf_xref ";
            $q.="(product_id,manufacturer_id) values ('".$id."','1');";
            query($db,$q);
        }
        query($db,"delete from #__vm_product_category_xref where product_id='".$id."';");
        foreach($product['category_id'] as $cat) {
            $q="insert into #__vm_product_category_xref ";
            $q.="(product_id,category_id) values ('".$id."','".$cat."');";
            query($db,$q);
        }
        foreach($product['params'] as $pt_id => $pt_attrs) {
            query($db,"delete from #__vm_product_type_xref where product_id=".$id.";");
            query($db,"insert into #__vm_product_type_xref (product_type_id,product_id) values ('".$pt_id."','".$id."');");
            query($db,"delete from #__vm_product_type_".$pt_id." where product_id='".$id."';");
            $q="insert into #__vm_product_type_".$pt_id." ";
            $f1=array('product_id');
            $f2=array("'".$id."'");
            foreach($pt_attrs as $k => $v) {
                $f1[]=$k;
                $f2[]="'".$v."'";
            }
            $q.="(".join(",",$f1).") values (".join(",",$f2).");";
            query($db,$q);
        }
        return new xmlrpcresp(new xmlrpcval($id, $xmlrpcInt));
    }

    function delete_product($username,$password,$id) {
        global $mainframe, $xmlrpcerruser, $xmlrpcI4, $xmlrpcInt, $xmlrpcBoolean, $xmlrpcDouble, $xmlrpcString, $xmlrpcDateTime, $xmlrpcBase64, $xmlrpcArray, $xmlrpcStruct, $xmlrpcValue;
        if(!plgXMLRPCOpenERP2VmHelper::authenticateUser($username, $password)) {
            return new xmlrpcresp(0, $xmlrpcerruser+1, JText::_("Login Failed"));
        }
        $db =& JFactory::getDBO();
        query($db,"delete from #__vm_product where product_id=".$id.";");
        query($db,"delete from #__vm_product_attribute where product_id=".$id.";");
        query($db,"delete from #__vm_product_category_xref where product_id=".$id.";");
        query($db,"delete from #__vm_product_mf_xref where product_id=".$id.";");
        query($db,"delete from #__vm_product_price where product_id=".$id.";");
        query($db,"select product_type_id from #__vm_product_type_xref where product_id=".$id.";",0);
        foreach($db->loadRowList() as $row) {
            query($db,"delete from #__vm_product_type_".$row[0]." where product_id=".$id.";");
        }
        query($db,"delete from #__vm_product_type_xref where product_id=".$id.";");
        query($db,"delete from #__jf_content where reference_table='vm_product' and reference_field in ('product_s_desc','product_desc') ;");
        return new xmlrpcresp(new xmlrpcval(1, $xmlrpcInt));
    }

    function set_stock($username,$password,$product){
        global $mainframe, $xmlrpcerruser, $xmlrpcI4, $xmlrpcInt, $xmlrpcBoolean, $xmlrpcDouble, $xmlrpcString, $xmlrpcDateTime, $xmlrpcBase64, $xmlrpcArray, $xmlrpcStruct, $xmlrpcValue;
        if(!plgXMLRPCOpenERP2VmHelper::authenticateUser($username, $password)) {
            return new xmlrpcresp(0, $xmlrpcerruser+1, JText::_("Login Failed"));
        }
        $db =& JFactory::getDBO();
        $values=array();
        $values[]=array("product_in_stock",$product['in_stock']);
        $id=$product['id'];
        if($id) {
            query($db,"select product_id from #__vm_product where product_id=".$id.";");
            if($db->getNumRows()) {
                $q="update #__vm_product set ";
                $f=array();
                foreach($values as $v) {
                    $f[]=$v[0]."='".$v[1]."'";
                }
                $q.=join(",",$f);
                $q.=" where product_id='".$product['id']."';";

                olidebug($q);
                query($db,$q);
            }
        }
        return new xmlrpcresp(new xmlrpcval($id, $xmlrpcInt));
    }

    function get_orders($username,$password) {
        global $mainframe, $xmlrpcerruser, $xmlrpcI4, $xmlrpcInt, $xmlrpcBoolean, $xmlrpcDouble, $xmlrpcString, $xmlrpcDateTime, $xmlrpcBase64, $xmlrpcArray, $xmlrpcStruct, $xmlrpcValue;
        if(!plgXMLRPCOpenERP2VmHelper::authenticateUser($username, $password)) {
            return new xmlrpcresp(0, $xmlrpcerruser+1, JText::_("Login Failed"));
        }
        $db =& JFactory::getDBO();
        $orders=array();
        query($db,"select product_type_id, product_type_name from #__vm_product_type;",0);
        foreach($db->loadRowList() as $row) {
            query($db,"select parameter_name, parameter_label from #__vm_product_type_parameter where product_type_id='".$row[0]."';",0);
            $params=array();
            foreach($db->loadRowList() as $row2) {
                $params[]=new xmlrpcval(array(new xmlrpcval($row2[0], $xmlrpcString), new xmlrpcval($row2[1], $xmlrpcString)), $xmlrpcArray);
            }
            $orders[]=new xmlrpcval(array(new xmlrpcval($row[0], $xmlrpcInt), new xmlrpcval($row[1], $xmlrpcString), new xmlrpcval($params, $xmlrpcArray)), $xmlrpcArray);
        }
        return new xmlrpcresp( new xmlrpcval($orders, $xmlrpcArray));



#order_id , user_id , vendor_id , order_number                     , user_info_id                     , order_total , order_subtotal , order_tax , order_tax_details         , order_shipping , order_shipping_tax , coupon_discount , coupon_code , order_discount , order_currency , order_status , cdate      , mdate      , ship_method_id    , customer_note , ip_address
#1        , 62      , 1         , 62_c7ed68c6bfc1d6e98f1dae42c23df , 1a62ae63f858475284e39149ae1d8e06 , 41.93000    , 14.15000       , 0.00      , a:2:{i:0;d:0;s:0:"";d:0;} , 25.78          , 0.00               , 0.00            ,             , -2.00          , EUR            , P            , 1271227673 , 1271227673 , standard_shipping , DHL           , Europe > 4kg , 25.78 , 9 ,  , ::ffff:127.0.0. , 


    }

}

function olidebug($s) {
  $fp = fopen("/tmp/debug.xmlrpc.txt","a");
  fwrite($fp, $s."\n");
  fclose($fp);
}


class plgXMLRPCOpenERP2VmHelper {
    function authenticateUser($username, $password) {
        // Get the global JAuthentication object
        jimport( 'joomla.user.authentication');
        $auth = & JAuthentication::getInstance();
        $credentials = array( 'username' => $username, 'password' => $password );
        $options = array();
        $response = $auth->authenticate($credentials, $options);
        //TODO CHECK that registred users do not have access
        //$user =& JFactory::getUser($username);
        //plgXMLRPCOpenERP2VmHelper::getUserAid( $user );
        return $response->status === JAUTHENTICATE_STATUS_SUCCESS;
    }
    function getUserAid( &$user ) {

        $acl = &JFactory::getACL();

        //Get the user group from the ACL
        $grp = $acl->getAroGroup($user->get('id'));

        // Mark the user as logged in
        $user->set('guest', 0);
        $user->set('aid', 1);

        // Fudge Authors, Editors, Publishers and Super Administrators into the special access group
        if ($acl->is_group_child_of($grp->name, 'Registered')      ||
            $acl->is_group_child_of($grp->name, 'Public Backend')) {
             $user->set('aid', 2);
         }
    }
}

/* vim: set expandtab tabstop=4 : */
