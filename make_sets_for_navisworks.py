#coding=utf-8
#!/usr/bin/env python
#C.C.J. Claus 

import sys
import os 
import uuid
import lxml 
import ifcopenshell 
import itertools 
import unicodedata

from datetime import datetime
from collections import defaultdict
from lxml import etree as ET
from operator import itemgetter
from collections import OrderedDict
from itertools import combinations

fname = input('Give in absolute file path to IFC file:')

while fname.endswith('.ifc') == False:
    print ('The path you gave is not an IFC file.')
    fname = input('Give in file path to IFC file:')
    
ifcfile = ifcopenshell.open(fname)
products = ifcfile.by_type('IfcProduct')

project = ifcfile.by_type('IfcProject')
site = ifcfile.by_type('IfcSite')

head, tail = os.path.split(fname)
folder_name = 'sets_Navisworks_Manage_' + tail.replace('.ifc','') 

class GetIDMdata():
    def get_software(self):
        print ('get software')
        
        software_list = []
        
        for j in project:
            if j.OwnerHistory is not None:
                software_list.append(j.OwnerHistory.OwningApplication.ApplicationFullName)
                   
        return software_list 
    
    def get_origins(self):
        print ('get origins')
        
        coordinates_list = []
        site = ifcfile.by_type('IfcSite')
        for j in site:
            coordinates_list.append(['Latitude', j.RefLatitude,]) 
            coordinates_list.append(['Longitude', j.RefLongitude])
            coordinates_list.append(['Elevation',j.RefElevation])
            
            for i in j.ObjectPlacement.ReferencedByPlacements:
                coordinates_list.append(['XYZ', i.RelativePlacement.Location.Coordinates])
                
        return coordinates_list
    
    def get_building_storey(self):  
        print ('get building storey')
        
        building_storey_list = []
        
        for product in products:
            if product.is_a('IfcBuildingStorey'):
                building_storey_list.append(product.Name)
                
        return building_storey_list 
             
    def get_entities(self):
        print ('get type entities')
        
        ifcproduct_list = []
        product_list = []
        product_names_list = [] 
        
        for item, product in enumerate(products):
            product_list.append(product.is_a())
            product_names_list.append([(product.is_a(),str(product.Name))])
        
        
        ifcproduct_list = (list(OrderedDict.fromkeys(product_list)))
        product_names_list.sort() 
        ifcproduct_name_list = list(product_names_list for product_names_list, _ in itertools.groupby(product_names_list))
        
        product_type_list = []
        
        for i in ifcproduct_name_list:
            if ':' in (i[0][1]):
                product_type_list.append([i[0][0],i[0][1].split(':')[1]] )  
            else:
                product_type_list.append([i[0][0], i[0][1]])
                   
        sorted_product_type_list = (sorted(product_type_list, key=itemgetter(0)))
         
        #Oplossing M. Berends
        pointer =  sorted_product_type_list[0][0]
        previous = pointer 
        content = []
        entity_list = []
    
        for i in sorted_product_type_list:
            pointer = i[0] 
            if pointer == previous:
                content.append(i[1])
            else: 
                entity_list.append([previous,content])
                previous=pointer
                content=[]
                content.append(i[1])
                       
        entity_list.append([previous,content])   
        entity_dict = {}
        
        for i in entity_list:
            entity_dict[i[0]] = (set(i[1]))
            
        return entity_dict
    
    def get_type_entities(self):
        
        product_type_list = []
        
        for product in products:  
            for relating_type in product.IsDefinedBy:
                if relating_type.is_a('IfcRelDefinesByType'):
                    if relating_type.RelatingType.Name is not None:
                        product_type_list.append([relating_type.RelatingType.is_a(), relating_type.RelatingType.Name])
                        
        if (len(product_type_list)) == 0 :
            product_type_list.append(['No RelatingType Found', 'No RelatingType Name found'])
            
        sorted_product_type_list = (sorted(product_type_list, key=itemgetter(0)))
        
        #Oplossing M. Berends
        pointer =  sorted_product_type_list[0][0]
        previous = pointer 
        content = []
        entity_list = []
    
        for i in sorted_product_type_list:
            pointer = i[0] 
            if pointer == previous:
                content.append(i[1])
            else: 
                entity_list.append([previous,content])
                previous=pointer
                content=[]
                content.append(i[1])
                      
        entity_list.append([previous,content])   
        entity_dict = {}
        
        for i in entity_list:
            entity_dict[i[0]] = (set(i[1]))
            
        return entity_dict                
    
        
    def get_classification(self):
        print ('get classification')
        
        classification_name_list = []
        classification_list = [] 
        
        for product in products:
            for has_associations in product.HasAssociations:
                if has_associations.is_a('IfcRelAssociatesClassification'):
                    if has_associations.RelatingClassification.Name is not None:
                       
                        classification_name_list.append(has_associations.Name)
                        classification_list.append([has_associations.Name, 
                                                   str(has_associations.RelatingClassification.ItemReference) ,  str(has_associations.RelatingClassification.Name)
                                                    ])
              
        classification_name_list = list(dict.fromkeys(classification_name_list))
        classification_list.sort()
        sorted_classification_list = list(classification_list for classification_list,_ in itertools.groupby(classification_list))
        
        if (len(sorted_classification_list)) == 0:
            sorted_classification_list.append(['Classification', 'No Classification Found', '!'])
  
        return sorted_classification_list
    

    def get_materials(self):
        print ('get materials')
        
        material_list = []
        
        for product in products:
            if product.HasAssociations:
                for j in product.HasAssociations:
                    if j.is_a('IfcRelAssociatesMaterial'):
                        
                        if j.RelatingMaterial.is_a('IfcMaterial'):
                            material_list.append(j.RelatingMaterial.Name)
                           
                        if j.RelatingMaterial.is_a('IfcMaterialList'):
                            for materials in j.RelatingMaterial.Materials:
                                material_list.append(materials.Name)
                       
                                
                        if j.RelatingMaterial.is_a('IfcMaterialLayerSetUsage'):
                            for materials in j.RelatingMaterial.ForLayerSet.MaterialLayers:
                                material_list.append(materials.Material.Name)
                                
                        else:
                            pass
              
        materials_list = list(dict.fromkeys(material_list))   
        
        if (len(materials_list)) == 0:
            materials_list.append(['Materials', 'No Materials Found', '!'])
        
        return materials_list
    
    def get_loadbearing(self):
        print ('get loadbearing')
        
        pset_list = []
        
        for product in products:
            for properties in product.IsDefinedBy:
                if properties.is_a('IfcRelDefinesByProperties'):
                    if properties.RelatingPropertyDefinition:
                        if properties.RelatingPropertyDefinition.is_a('IfcPropertySet'):
                            if properties.RelatingPropertyDefinition.Name.startswith("Pset_"):
                                for loadbearing in properties.RelatingPropertyDefinition.HasProperties:
                                    if loadbearing.Name == "LoadBearing":
                                        pset_list.append([properties.RelatingPropertyDefinition.Name, loadbearing.Name, loadbearing.NominalValue[0]])     
        
        loadbearing_list = [list(x) for x in set(tuple(x) for x in pset_list)]
        
        if len(loadbearing_list) == 0:
            loadbearing_list.append(['LoadBearing','No LoadBearing property found', '!'])
        
        return loadbearing_list 
    
    def get_isexternal(self):
        print ('get isexternal')
        
        pset_list = []
        for product in products:
            for properties in product.IsDefinedBy:
                if properties.is_a('IfcRelDefinesByProperties'):
                    if properties.RelatingPropertyDefinition:
                        if properties.RelatingPropertyDefinition.is_a('IfcPropertySet'):
                            if properties.RelatingPropertyDefinition.Name.startswith("Pset_"):
                                for isexternal in properties.RelatingPropertyDefinition.HasProperties:
                                    if isexternal.Name == "IsExternal":
                                        pset_list.append([properties.RelatingPropertyDefinition.Name, isexternal.Name, isexternal.NominalValue[0]])
            
        isexternal_list = [list(x) for x in set(tuple(x) for x in pset_list)]
    
        if len(isexternal_list) == 0:
            isexternal_list.append(['IsExternal', 'No IsExternal property found', '!'])
            
        return isexternal_list
    
    def get_firerating(self):
        print ('get firerating')
        
        pset_list = []
        
        for product in products:
            for properties in product.IsDefinedBy:
                if properties.is_a('IfcRelDefinesByProperties'):
                    if properties.RelatingPropertyDefinition:
                        if properties.RelatingPropertyDefinition.is_a('IfcPropertySet'):
                            if properties.RelatingPropertyDefinition.Name.startswith("Pset_"):
                                for firerating in properties.RelatingPropertyDefinition.HasProperties:
                                    if firerating.Name == "FireRating":
                                        if firerating.NominalValue is not None:
                                                                              
                                            pset_list.append([properties.RelatingPropertyDefinition.Name, firerating.Name, firerating.NominalValue[0]])
        
    
        fire_rating_list = [list(x) for x in set(tuple(x) for x in pset_list)]
        
        if len(fire_rating_list) == 0:
            fire_rating_list.append(['FireRating', 'No FireRating found', 'No FireRating found'])
            
        return fire_rating_list
    
    def get_phase(self):
        
        print ('get phase')
        
        pset_phase_list =['Phasing','AC_Pset_RenovationAndPhasing','Pset_Phasing', 'Phase', 'Phase Created', 'Renovation Status']
        phase_list = []
        phase_name_list = []
        
        for product in products:
            for properties in product.IsDefinedBy:
                if properties.is_a('IfcRelDefinesByProperties'):
                    if properties.RelatingPropertyDefinition.is_a('IfcPropertySet'):
    
                        for phasing in properties.RelatingPropertyDefinition.HasProperties:
                            #print (phasing)
                            if properties.RelatingPropertyDefinition.Name is not None:
                                #print (properties.RelatingPropertyDefinition.Name)
                                
                                if (phasing.NominalValue):
                                    if phasing.Name in pset_phase_list:
                                        #print ('hallo', phasing.Name)
                                    
                                    
                                        if properties.RelatingPropertyDefinition.Name in pset_phase_list:
                                            #print ('hier', phasing.Name)
                                            phase_name_list.append(properties.RelatingPropertyDefinition.Name)
                                            phase_list.append([properties.RelatingPropertyDefinition.Name, phasing.Name, phasing.NominalValue[0]])
                    
        phase_name_list = list(dict.fromkeys(phase_name_list))
        phase_list.sort()
        sorted_phase_list = list(phase_list for phase_list,_ in itertools.groupby(phase_list))

        if (len(sorted_phase_list)) == 0:
            sorted_phase_list.append(['Phase', 'No Phasing Found', 'No Phasing found!'])
            
        return sorted_phase_list


class WriteToNavisworksXML(): 
    
    def __init__(self):
        get_idm_data = GetIDMdata()
     
    def write_software_to_navisworks_xml(self, file_path_xml):
        get_idm_data = GetIDMdata()
        software_list = []
        for i in get_idm_data.get_software():
            software_list.append(i)
            
        
        root = ET.Element('exchange')
        doc = ET.SubElement(root, "selectionsets")
        viewfolder = ET.SubElement(doc, "viewfolder", name='3.0 Software Used', guid=str(uuid.uuid4()))
        selectionset = ET.SubElement(viewfolder, "selectionset", name=str(software_list[0]), guid=str(uuid.uuid4()))
        findspec = ET.SubElement(selectionset, "findspec", mode="all", disjoint="0")      
        conditions = ET.SubElement(findspec, "conditions")
        condition = ET.SubElement(conditions, "condition", test="equals", flags="10")  
        category = ET.SubElement(condition, "category")
        name = ET.SubElement(category, "name", internal="LcIFCProperty").text = 'IFCAPPLICATION'
        property = ET.SubElement(condition, "property")
        name = ET.SubElement(property, "name", internal="IFCString").text = "APPLICATIONFULLNAME"
        value = ET.SubElement(condition, "value")
        ifc_data = ET.SubElement(value, "data", type="wstring").text = str(software_list[0])
        locator = ET.SubElement(findspec, "locator").text = "/"
        
        tree = ET.ElementTree(root)
        tree.write(str(file_path_xml), encoding="utf-8", xml_declaration=True, pretty_print=True)
        self.write_declaration_for_navisworks_xml(str(file_path_xml))
        
    def write_origins_to_navisworks_xml(self, file_path_xml):

        get_idm_data = GetIDMdata()
        origin_list = get_idm_data.get_origins()
        
        root = ET.Element('exchange')
        doc = ET.SubElement(root, "selectionsets")
        viewfolder = ET.SubElement(doc, "viewfolder", name='3.2 Local Position and Orientation', guid=str(uuid.uuid4()))
        
        for items in origin_list:
            selectionset = ET.SubElement(viewfolder, "selectionset", name=str(items[0]) + ': ' + str(items[1]), guid=str(uuid.uuid4()))
            findspec = ET.SubElement(selectionset, "findspec", mode="all", disjoint="0")      
            conditions = ET.SubElement(findspec, "conditions")
            condition = ET.SubElement(conditions, "condition", test="equals", flags="10")  
            category = ET.SubElement(condition, "category")
            name = ET.SubElement(category, "name", internal="LcIFCProperty").text = 'IFC'
            property = ET.SubElement(condition, "property")
            name = ET.SubElement(property, "name", internal="IFCString").text = '<none>'
            value = ET.SubElement(condition, "value")
            ifc_data = ET.SubElement(value, "data", type="wstring").text = str(items[0]) + ': ' + str(items[1])   
            locator = ET.SubElement(findspec, "locator").text = "/"
            
        tree = ET.ElementTree(root)
        tree.write(str(file_path_xml), encoding="utf-8", xml_declaration=True, pretty_print=True)
        
        self.write_declaration_for_navisworks_xml(str(file_path_xml))
        
    def write_entities_to_navisworks_xml(self, file_path_xml):
        get_idm_data = GetIDMdata()
        get_entities_dict = get_idm_data.get_entities()
        
        root = ET.Element('exchange')
        doc = ET.SubElement(root, "selectionsets")
        mainfolder = ET.SubElement(doc, "viewfolder", name="3.4 Correct Use Of Entities" , guid=str(uuid.uuid4()))
        
        for folder_name, entities in get_entities_dict.items():
            viewfolder = ET.SubElement(mainfolder, "viewfolder", name=str(folder_name), guid=str(uuid.uuid4()))
            for entity in filter(None, entities):
                x = entity.replace('','')
             
                selectionset = ET.SubElement(viewfolder, "selectionset", name=str(x), guid=str(uuid.uuid4()))
                findspec = ET.SubElement(selectionset, "findspec", mode="all", disjoint="0")      
                conditions = ET.SubElement(findspec, "conditions")
                condition = ET.SubElement(conditions, "condition", test="contains", flags="10")  
                category = ET.SubElement(condition, "category")
                name = ET.SubElement(category, "name", internal="LcIFCProperty").text = 'IFC' #folder_name.upper()
                property = ET.SubElement(condition, "property")
                name = ET.SubElement(property, "name", internal="IFCString").text = 'NAME'
                value = ET.SubElement(condition, "value")
                ifc_data = ET.SubElement(value, "data", type="wstring").text = str(x)
                locator = ET.SubElement(findspec, "locator").text = "/"
            
        tree = ET.ElementTree(root)
        tree.write(str(file_path_xml), encoding="utf-8", xml_declaration=True, pretty_print=True)
        
        self.write_declaration_for_navisworks_xml(str(file_path_xml))
        
    def write_type_entities_to_navisworks_xml(self, file_path_xml):

        get_idm_data = GetIDMdata()
        get_type_dict = get_idm_data.get_type_entities()
        
        root = ET.Element('exchange')
        doc = ET.SubElement(root, "selectionsets")
        mainfolder = ET.SubElement(doc, "viewfolder", name="3.4 Correct Use Of Type" , guid=str(uuid.uuid4()))
        
        for folder_name, entities in get_type_dict.items():
            viewfolder = ET.SubElement(mainfolder, "viewfolder", name=str(folder_name), guid=str(uuid.uuid4()))
            for entity in entities:
                selectionset = ET.SubElement(viewfolder, "selectionset", name=str(entity), guid=str(uuid.uuid4()))
                findspec = ET.SubElement(selectionset, "findspec", mode="all", disjoint="0")      
                conditions = ET.SubElement(findspec, "conditions")
                condition = ET.SubElement(conditions, "condition", test="contains", flags="10")  
                category = ET.SubElement(condition, "category")
                name = ET.SubElement(category, "name", internal="LcIFCProperty").text = folder_name.upper()
                property = ET.SubElement(condition, "property")
                name = ET.SubElement(property, "name", internal="IFCString").text = 'NAME'
                value = ET.SubElement(condition, "value")
                ifc_data = ET.SubElement(value, "data", type="wstring").text = str(entity)   
                locator = ET.SubElement(findspec, "locator").text = "/"
            
        tree = ET.ElementTree(root)
        tree.write(str(file_path_xml), encoding="utf-8", xml_declaration=True, pretty_print=True)
        self.write_declaration_for_navisworks_xml(str(file_path_xml))    
        
    def write_classification_to_navisworks_xml(self, file_path_xml):
        get_idm_data = GetIDMdata()
        get_classification_list = get_idm_data.get_classification()
        
        root = ET.Element('exchange')
        doc = ET.SubElement(root, "selectionsets")
        mainfolder = ET.SubElement(doc, "viewfolder", name="3.6 Classification System" , guid=str(uuid.uuid4()))
        
        classification_folder_list = []
        classification_list = []
        for i in (get_classification_list):
            classification_folder_list.append(i[0])
            classification_list.append(i)
            
        folder_names =  (set(classification_folder_list))
        
        
        for folder_name in folder_names:
            viewfolder = ET.SubElement(mainfolder, "viewfolder", name=str(folder_name), guid=str(uuid.uuid4()))
        
            for classification in classification_list:   
                selectionset = ET.SubElement(viewfolder, "selectionset", name=str(classification[1]) + ' ' + str(classification[2]), guid=str(uuid.uuid4()))
                findspec = ET.SubElement(selectionset, "findspec", mode="all", disjoint="0")      
                conditions = ET.SubElement(findspec, "conditions")
                condition = ET.SubElement(conditions, "condition", test="contains", flags="10")  
                category = ET.SubElement(condition, "category")
                name = ET.SubElement(category, "name", internal="LcIFCProperty").text = 'Classification:'+classification[0]
                property = ET.SubElement(condition, "property")
                name = ET.SubElement(property, "name", internal="IFCString").text = 'ITEMREFERENCE'
                value = ET.SubElement(condition, "value")
                ifc_data = ET.SubElement(value, "data", type="wstring").text = str(classification[1]) 
                locator = ET.SubElement(findspec, "locator").text = "/"
            
        tree = ET.ElementTree(root)
        tree.write(str(file_path_xml), encoding="utf-8", xml_declaration=True, pretty_print=True)
        self.write_declaration_for_navisworks_xml(str(file_path_xml))
    
    def write_materials_to_navisworks_xml(self, file_path_xml):

        root = ET.Element('exchange')
        doc = ET.SubElement(root, "selectionsets")
        viewfolder = ET.SubElement(doc, "viewfolder", name='3.7 Materials', guid=str(uuid.uuid4()))
        
        get_idm_data = GetIDMdata()
        material_list = get_idm_data.get_materials()
        
        for material in material_list:
            selectionset = ET.SubElement(viewfolder, "selectionset", name=str(material), guid=str(uuid.uuid4()))
            findspec = ET.SubElement(selectionset, "findspec", mode="all", disjoint="0")      
            conditions = ET.SubElement(findspec, "conditions")
            condition = ET.SubElement(conditions, "condition", test="contains", flags="10")  
            category = ET.SubElement(condition, "category")
            name = ET.SubElement(category, "name", internal="LcIFCProperty").text ='Material'
            property = ET.SubElement(condition, "property")
            name = ET.SubElement(property, "name", internal="IFCString").text = 'Name'
            value = ET.SubElement(condition, "value")
            
            ifc_data = ET.SubElement(value, "data", type="wstring").text = str(material)
            locator = ET.SubElement(findspec, "locator").text = "/"

        tree = ET.ElementTree(root)
        tree.write(str(file_path_xml), encoding="utf-8", xml_declaration=True, pretty_print=True)
        self.write_declaration_for_navisworks_xml(str(file_path_xml))  
          
        
    def write_loadbearing_to_navisworks_xml(self, file_path_xml):
    
        get_idm_data = GetIDMdata()
        loadbearing_list  = get_idm_data.get_loadbearing()
        
        root = ET.Element('exchange')
        doc = ET.SubElement(root, "selectionsets")
        viewfolder = ET.SubElement(doc, "viewfolder", name='4.1 LoadBearing', guid=str(uuid.uuid4()))
        
        loadbearing_bool_list = ['True', 'False']
    
        for true_false in loadbearing_bool_list:
            
            if len(loadbearing_list) == 1:
                if true_false == 'True':
                    selectionset = ET.SubElement(viewfolder, "selectionset", name='No Items Found', guid=str(uuid.uuid4()))
                    findspec = ET.SubElement(selectionset, "findspec", mode="all", disjoint="0")      
                    conditions = ET.SubElement(findspec, "conditions")
                    condition = ET.SubElement(conditions, "condition", test="equals", flags="10")  
                    category = ET.SubElement(condition, "category")
                    name = ET.SubElement(category, "name", internal="LcIFCProperty").text ='<none>'
                    property = ET.SubElement(condition, "property")
                    name = ET.SubElement(property, "name", internal="IFCString").text = '<none>'
                    value = ET.SubElement(condition, "value")
                    
                    ifc_data = ET.SubElement(value, "data", type="wstring").text = '<none>'
                    locator = ET.SubElement(findspec, "locator").text = "/"
                
                
            else:
                
                loadbearing_bool_folder = ET.SubElement(viewfolder, "viewfolder", name=str(true_false), guid=str(uuid.uuid4()) )
    
                for items in loadbearing_list:
                    if true_false == 'True':
                    
                        if str(items[2]) == 'True':
                            
                            selectionset = ET.SubElement(loadbearing_bool_folder, "selectionset", name=str(items[0]) + ': ' + str(items[1]) + ':' + str(items[2]), guid=str(uuid.uuid4()))
                            findspec = ET.SubElement(selectionset, "findspec", mode="all", disjoint="0")      
                            conditions = ET.SubElement(findspec, "conditions")
                            condition = ET.SubElement(conditions, "condition", test="equals", flags="10")  
                            category = ET.SubElement(condition, "category")
                            name = ET.SubElement(category, "name", internal="LcIFCProperty").text = str(items[0])
                            property = ET.SubElement(condition, "property")
                            name = ET.SubElement(property, "name", internal="IFCString").text = str(items[1])
                            value = ET.SubElement(condition, "value")
                            
                            ifc_data = ET.SubElement(value, "data", type="wstring").text = str(items[2]).upper()   
                            locator = ET.SubElement(findspec, "locator").text = "/"
                        
                    if true_false == 'False':
                        if str(items[2]) == 'False':
                            selectionset = ET.SubElement(loadbearing_bool_folder, "selectionset", name=str(items[0]) + ': ' + str(items[1]) + ':' + str(items[2]), guid=str(uuid.uuid4()))
                            findspec = ET.SubElement(selectionset, "findspec", mode="all", disjoint="0")      
                            conditions = ET.SubElement(findspec, "conditions")
                            condition = ET.SubElement(conditions, "condition", test="equals", flags="10")  
                            category = ET.SubElement(condition, "category")
                            name = ET.SubElement(category, "name", internal="LcIFCProperty").text = str(items[0])
                            property = ET.SubElement(condition, "property")
                            name = ET.SubElement(property, "name", internal="IFCString").text =  str(items[1])
                            value = ET.SubElement(condition, "value")
                            ifc_data = ET.SubElement(value, "data", type="wstring").text = str(items[2]).upper()   
                            locator = ET.SubElement(findspec, "locator").text = "/"
                        
            
        tree = ET.ElementTree(root)
        tree.write(str(file_path_xml), encoding="utf-8", xml_declaration=True, pretty_print=True)
        self.write_declaration_for_navisworks_xml(str(file_path_xml))
        
    def write_isexternal_to_navisworks_xml(self, file_path_xml):
    
        get_idm_data = GetIDMdata()
        isexternal_list  = get_idm_data.get_isexternal()
        
        root = ET.Element('exchange')
        doc = ET.SubElement(root, "selectionsets")
        viewfolder = ET.SubElement(doc, "viewfolder", name='4.2 IsExternal', guid=str(uuid.uuid4()))
        
        bool_list = ['True', 'False']
    
        for true_false in bool_list:
            
            if len(isexternal_list) == 1:
                if true_false == 'True':
                    selectionset = ET.SubElement(viewfolder, "selectionset", name='No Items Found', guid=str(uuid.uuid4()))
                    findspec = ET.SubElement(selectionset, "findspec", mode="all", disjoint="0")      
                    conditions = ET.SubElement(findspec, "conditions")
                    condition = ET.SubElement(conditions, "condition", test="equals", flags="10")  
                    category = ET.SubElement(condition, "category")
                    name = ET.SubElement(category, "name", internal="LcIFCProperty").text ='<none>'
                    property = ET.SubElement(condition, "property")
                    name = ET.SubElement(property, "name", internal="IFCString").text = '<none>'
                    value = ET.SubElement(condition, "value")
                    
                    ifc_data = ET.SubElement(value, "data", type="wstring").text = '<none>'
                    locator = ET.SubElement(findspec, "locator").text = "/"
                
            else:
                
                loadbearing_bool_folder = ET.SubElement(viewfolder, "viewfolder", name=str(true_false), guid=str(uuid.uuid4()) )
    
                for items in isexternal_list:
                    if true_false == 'True':
                    
                        if str(items[2]) == 'True':
                            
                            selectionset = ET.SubElement(loadbearing_bool_folder, "selectionset", name=str(items[0]) + ': ' + str(items[1]) + ':' + str(items[2]), guid=str(uuid.uuid4()))
                            findspec = ET.SubElement(selectionset, "findspec", mode="all", disjoint="0")      
                            conditions = ET.SubElement(findspec, "conditions")
                            condition = ET.SubElement(conditions, "condition", test="equals", flags="10")  
                            category = ET.SubElement(condition, "category")
                            name = ET.SubElement(category, "name", internal="LcIFCProperty").text = str(items[0])
                            property = ET.SubElement(condition, "property")
                            name = ET.SubElement(property, "name", internal="IFCString").text = str(items[1])
                            value = ET.SubElement(condition, "value")
                            
                            ifc_data = ET.SubElement(value, "data", type="wstring").text = str(items[2]).upper()   
                            locator = ET.SubElement(findspec, "locator").text = "/"
                        
                    if true_false == 'False':
                        if str(items[2]) == 'False':
                            selectionset = ET.SubElement(loadbearing_bool_folder, "selectionset", name=str(items[0]) + ': ' + str(items[1]) + ':' + str(items[2]), guid=str(uuid.uuid4()))
                            findspec = ET.SubElement(selectionset, "findspec", mode="all", disjoint="0")      
                            conditions = ET.SubElement(findspec, "conditions")
                            condition = ET.SubElement(conditions, "condition", test="equals", flags="10")  
                            category = ET.SubElement(condition, "category")
                            name = ET.SubElement(category, "name", internal="LcIFCProperty").text = str(items[0])
                            property = ET.SubElement(condition, "property")
                            name = ET.SubElement(property, "name", internal="IFCString").text =  str(items[1])
                            value = ET.SubElement(condition, "value")
                            ifc_data = ET.SubElement(value, "data", type="wstring").text = str(items[2]).upper()   
                            locator = ET.SubElement(findspec, "locator").text = "/"
                        
            
        tree = ET.ElementTree(root)
        tree.write(str(file_path_xml), encoding="utf-8", xml_declaration=True, pretty_print=True)
        self.write_declaration_for_navisworks_xml(str(file_path_xml))
        
        
    def write_firerating_to_navisworks_xml(self, file_path_xml):
 
        get_idm_data = GetIDMdata()
        firerating_list  = get_idm_data.get_firerating()
        
        folder_firerating_list = []
        
        for i in firerating_list:
            if i[2]:
                folder_firerating_list.append(i[2])
            
        root = ET.Element('exchange')
        doc = ET.SubElement(root, "selectionsets")
        viewfolder = ET.SubElement(doc, "viewfolder", name='4.3 FireRating', guid=str(uuid.uuid4()))
        
        for j in (list((set(folder_firerating_list)))):
            firerating_folder = ET.SubElement(viewfolder, "viewfolder", name=str(j), guid=str(uuid.uuid4()))
            for fire_rating in firerating_list:  

                if j == fire_rating[2]:  
                  
                    selectionset = ET.SubElement(firerating_folder, "selectionset", name=str(fire_rating[0]) + ': ' + str(fire_rating[1]) + ':' + str(fire_rating[2]), guid=str(uuid.uuid4())) 
                    findspec = ET.SubElement(selectionset, "findspec", mode="all", disjoint="0")      
                    conditions = ET.SubElement(findspec, "conditions")
                    condition = ET.SubElement(conditions, "condition", test="equals", flags="10")  
                    category = ET.SubElement(condition, "category")
                    name = ET.SubElement(category, "name", internal="LcIFCProperty").text = str(fire_rating[0])
                    property = ET.SubElement(condition, "property")
                    name = ET.SubElement(property, "name", internal="IFCString").text =  str(fire_rating[1])
                    value = ET.SubElement(condition, "value")
                    ifc_data = ET.SubElement(value, "data", type="wstring").text = fire_rating[2] #str(i[2]).upper()   
                    locator = ET.SubElement(findspec, "locator").text = "/"
                                
                
        tree = ET.ElementTree(root)
        tree.write(str(file_path_xml), encoding="utf-8", xml_declaration=True, pretty_print=True)
        self.write_declaration_for_navisworks_xml(str(file_path_xml))
        
        
    def write_phase_to_navisworks_xml(self, file_path_xml):
     
        get_idm_data = GetIDMdata()
        phasing_list = GetIDMdata().get_phase()
        
        root = ET.Element('exchange')
        doc = ET.SubElement(root, "selectionsets")
        viewfolder = ET.SubElement(doc, "viewfolder", name='5.0 Phasing', guid=str(uuid.uuid4()))
        
        for i in phasing_list: 
            selectionset = ET.SubElement(viewfolder, "selectionset", name=str(i[2]), guid=str(uuid.uuid4()))
            findspec = ET.SubElement(selectionset, "findspec", mode="all", disjoint="0")      
            conditions = ET.SubElement(findspec, "conditions")
            condition = ET.SubElement(conditions, "condition", test="equals", flags="10")  
            category = ET.SubElement(condition, "category")
            name = ET.SubElement(category, "name", internal="LcIFCProperty").text = str(i[0])
            property = ET.SubElement(condition, "property")
            name = ET.SubElement(property, "name", internal="IFCString").text = str(i[1])
            value = ET.SubElement(condition, "value")
            ifc_data = ET.SubElement(value, "data", type="wstring").text = str(i[2])
            locator = ET.SubElement(findspec, "locator").text = "/"
            
            
        tree = ET.ElementTree(root)
        tree.write(str(file_path_xml), encoding="utf-8", xml_declaration=True, pretty_print=True)
        self.write_declaration_for_navisworks_xml(str(file_path_xml)) 

    def write_declaration_for_navisworks_xml(self, file_path_xml):

        xml_declaration =   '<?xml version="1.0" encoding="UTF-8" ?>'
        schema_location_string = '<exchange xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://download.autodesk.com/us/navisworks/schemas/nw-exchange-12.0.xsd">'

        with open(file_path_xml, 'r') as xml_file:
            xml_data = xml_file.readlines()
            
        
        xml_data[0] = xml_declaration + '\n'
        xml_data[1] = schema_location_string + '\n'
        
        with open(file_path_xml, 'w') as xml_file:
            xml_file.writelines(xml_data)
        
def make_set_folder(set_folder):
    
    print ('__________________________________')

    try:
        os.mkdir(head + '\\' + set_folder)  
    except OSError:
        print ("The directory: '%s' already exists" % set_folder)
    else:
        print ("Successfully created the directory %s " % set_folder)
        return set_folder

    print ('__________________________________')  
    
      
if __name__ == '__main__':
    
    make_set_folder(set_folder=folder_name)
    write_to_navisworks_xml = WriteToNavisworksXML()
    path = head + '\\' + folder_name
	warning = 'Path name is over 256 characters long, xml creation software used is not possible'
    
    if len(path+'\\3.0_software_used'+tail.replace('.ifc','.xml')) <255:
        write_to_navisworks_xml.write_software_to_navisworks_xml(file_path_xml=str(path) + '\\3.0_software_used_' +tail.replace('.ifc','.xml'))    
    else:
        print (warning)
        
    if len(path+'\\3.2_local_position_and_orientation.xml'+ tail.replace('.ifc','.xml')) <255:   
        write_to_navisworks_xml.write_origins_to_navisworks_xml(file_path_xml=str(path) +  '\\3.2_local_position_and_orientation_'+ tail.replace('.ifc','.xml'))
    else:
        print (warning)
            
    if len(path+'\\3.4_correct_use_of_entities.xml'+ tail.replace('.ifc','.xml')) < 255:    
        write_to_navisworks_xml.write_entities_to_navisworks_xml(file_path_xml=str(path) +  '\\3.4_correct_use_of_entities_'+ tail.replace('.ifc','.xml'))
    else:
        print (warning)   
    
    if len(path+'\\3.4_correct_use_of_type.xml'+ tail.replace('.ifc','.xml')) < 255:  
        write_to_navisworks_xml.write_type_entities_to_navisworks_xml(file_path_xml=str(path) +  '\\3.4_correct_use_of_type_'+ tail.replace('.ifc','.xml'))
    else:
        print (warning)
         
    if len(path+'\\3.6_classification_system.xml'+ tail.replace('.ifc','.xml')) < 255:     
        write_to_navisworks_xml.write_classification_to_navisworks_xml(file_path_xml=str(path) +  '\\3.6_classification_system_'+ tail.replace('.ifc','.xml'))
    else:
        print (warning)  
        
    if len(path+'\\3.7_materials.xml'+ tail.replace('.ifc','.xml')) < 255:  
        write_to_navisworks_xml.write_materials_to_navisworks_xml(file_path_xml=str(path) +  '\\3.7_materials_'+ tail.replace('.ifc','.xml'))
    else:
        print (warning)
            
    if len(path+'\\4.1_loadbearing.xml'+ tail.replace('.ifc','.xml')) < 255:      
        write_to_navisworks_xml.write_loadbearing_to_navisworks_xml(file_path_xml=str(path) +  '\\4.1_loadbearing_'+ tail.replace('.ifc','.xml'))
    else:
        print (warning) 
            
    if len(path+'\\4.2_isexternal.xml'+ tail.replace('.ifc','.xml')) < 255:      
        write_to_navisworks_xml.write_isexternal_to_navisworks_xml(file_path_xml=str(path) +  '\\4.2_isexternal_'+ tail.replace('.ifc','.xml'))
    else:
        print (warning)
             
    if len(path+'\\4.3_firerating.xml'+ tail.replace('.ifc','.xml')) < 255:      
        write_to_navisworks_xml.write_firerating_to_navisworks_xml(file_path_xml=str(path) +  '\\4.3_firerating_'+ tail.replace('.ifc','.xml'))
    else:
        print (warning)
       
    if len(path+'\\5.0_phasing.xml'+ tail.replace('.ifc','.xml')) < 255:      
        write_to_navisworks_xml.write_phase_to_navisworks_xml(file_path_xml=str(path) +  '\\5.0_phasing_'+ tail.replace('.ifc','.xml'))
    else:
        print (warning)

    print ('__________________________________')
    enter = input('Press enter to open folder: \n' + str(head + '\\\\' + folder_name))
    print ('__________________________________') 
 
    if enter == '':  # hitting enter == ''  empty string
        xml_path = (str(head + '\\\\' + folder_name))
        path = os.path.realpath(xml_path)
        os.startfile(path)
        print ('Folder opened: ' + str(head + '\\\\' + folder_name))
        print ('__________________________________')  
        
        close_app = input('Press enter to close the application')
        
    else:
        xml_path = (str(head + '\\\\' + folder_name))
        path = os.path.realpath(xml_path)
        os.startfile(path)
        print ('Folder openend: ' + str(head + '\\\\' + folder_name))
        print ('__________________________________')  
        close_app = input('Press enter to close the application')
        
