import csv
import io
from typing import List
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

class FeedExporter:
    def generate_google_merchant_xml(self, products) -> str:
        rss = Element('rss', {'version': '2.0', 'xmlns:g': 'http://base.google.com/ns/1.0'})
        channel = SubElement(rss, 'channel')
        SubElement(channel, 'title').text = 'AI Optimized Product Feed'
        SubElement(channel, 'description').text = 'Products optimized for AI shopping assistants'
        
        for product in products:
            item = SubElement(channel, 'item')
            SubElement(item, 'g:id').text = product.product_id
            SubElement(item, 'g:title').text = product.ai_title
            SubElement(item, 'g:description').text = product.ai_description
            SubElement(item, 'g:availability').text = 'in_stock'
            SubElement(item, 'g:condition').text = 'new'
            
            if product.semantic_tags:
                SubElement(item, 'g:custom_label_0').text = '|'.join(product.semantic_tags[:5])
        
        rough_string = tostring(rss, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")
    
    def generate_meta_tiktok_csv(self, products) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        
        headers = ['id', 'title', 'description', 'availability', 'condition', 'custom_label_0']
        writer.writerow(headers)
        
        for product in products:
            row = [
                product.product_id,
                product.ai_title,
                product.ai_description,
                'in_stock',
                'new',
                '|'.join(product.semantic_tags[:5]) if product.semantic_tags else ''
            ]
            writer.writerow(row)
        
        return output.getvalue()
