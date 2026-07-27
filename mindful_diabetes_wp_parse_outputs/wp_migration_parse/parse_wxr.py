#!/usr/bin/env python3
import csv, json, re, sys
from pathlib import Path
import xml.etree.ElementTree as ET
from html import unescape

xml_path = Path('/mnt/data/wp_migration_parse/mindfuldiabetesinc.WordPress.2026-06-17.xml')
out_dir = Path('/mnt/data/wp_migration_outputs')
out_dir.mkdir(parents=True, exist_ok=True)

NS = {
    'content': 'http://purl.org/rss/1.0/modules/content/',
    'excerpt': 'http://wordpress.org/export/1.2/excerpt/',
    'wp': 'http://wordpress.org/export/1.2/',
    'dc': 'http://purl.org/dc/elements/1.1/',
}

def t(el, path, default=''):
    found = el.find(path, NS)
    return (found.text or '').strip() if found is not None and found.text is not None else default

def strip_html(s):
    s = re.sub(r'<script\b.*?</script>', ' ', s, flags=re.I|re.S)
    s = re.sub(r'<style\b.*?</style>', ' ', s, flags=re.I|re.S)
    s = re.sub(r'<[^>]+>', ' ', s)
    s = unescape(s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

shortcode_re = re.compile(r'\[([A-Za-z0-9_-]+)(?:\s|\]|\/)', re.M)
url_re = re.compile(r'''(?:src|href)=["']([^"']+)["']|https?://[^\s"'<>]+''', re.I)

def extract_urls(html):
    urls=[]
    for m in url_re.finditer(html or ''):
        u = m.group(1) or m.group(0)
        u = u.rstrip(').,;\']\"')
        if u.startswith('http') or 'wp-content/uploads' in u or u.startswith('/'):
            urls.append(u)
    # stable unique order
    seen=set(); out=[]
    for u in urls:
        if u not in seen:
            seen.add(u); out.append(u)
    return out

items=[]
media_refs=[]
shortcodes=[]
site={}

# Get channel-level metadata cheaply
root = ET.parse(xml_path).getroot()
channel = root.find('channel')
if channel is not None:
    site = {
        'title': t(channel, 'title'),
        'link': t(channel, 'link'),
        'description': t(channel, 'description'),
        'pubDate': t(channel, 'pubDate'),
        'wxr_version': t(channel, 'wp:wxr_version'),
        'base_site_url': t(channel, 'wp:base_site_url'),
        'base_blog_url': t(channel, 'wp:base_blog_url'),
    }
    # avoid holding full tree longer than needed
    root.clear()

# Stream parse items
context = ET.iterparse(xml_path, events=('end',))
for _, elem in context:
    if elem.tag == 'item':
        content = t(elem, 'content:encoded')
        excerpt = t(elem, 'excerpt:encoded')
        postmeta = {}
        meta_rows = []
        for pm in elem.findall('wp:postmeta', NS):
            k = t(pm, 'wp:meta_key')
            v = t(pm, 'wp:meta_value')
            if k:
                # preserve duplicate keys as joined; full rows below are not exported to keep inventory compact
                if k in postmeta and v:
                    postmeta[k] = postmeta[k] + ' | ' + v
                else:
                    postmeta[k] = v
                meta_rows.append({'key': k, 'value': v})
        cats=[]; tags=[]; terms=[]
        for c in elem.findall('category'):
            domain = c.attrib.get('domain','')
            nicename = c.attrib.get('nicename','')
            label = (c.text or '').strip()
            if domain == 'category': cats.append(label or nicename)
            elif domain == 'post_tag': tags.append(label or nicename)
            else: terms.append(f'{domain}:{label or nicename}' if domain else (label or nicename))
        row = {
            'post_id': t(elem, 'wp:post_id'),
            'post_type': t(elem, 'wp:post_type'),
            'status': t(elem, 'wp:status'),
            'title': t(elem, 'title'),
            'slug': t(elem, 'wp:post_name'),
            'link': t(elem, 'link'),
            'creator': t(elem, 'dc:creator'),
            'pub_date_rss': t(elem, 'pubDate'),
            'post_date': t(elem, 'wp:post_date'),
            'post_date_gmt': t(elem, 'wp:post_date_gmt'),
            'modified': t(elem, 'wp:post_modified'),
            'modified_gmt': t(elem, 'wp:post_modified_gmt'),
            'post_parent': t(elem, 'wp:post_parent'),
            'menu_order': t(elem, 'wp:menu_order'),
            'comment_status': t(elem, 'wp:comment_status'),
            'ping_status': t(elem, 'wp:ping_status'),
            'is_sticky': t(elem, 'wp:is_sticky'),
            'categories': ' | '.join([x for x in cats if x]),
            'tags': ' | '.join([x for x in tags if x]),
            'terms_other': ' | '.join([x for x in terms if x]),
            'attachment_url': t(elem, 'wp:attachment_url'),
            'featured_image_id': postmeta.get('_thumbnail_id',''),
            'template': postmeta.get('_wp_page_template',''),
            'content_html': content,
            'excerpt_html': excerpt,
            'content_text_preview': strip_html(content)[:500],
            'content_char_count': str(len(content or '')),
            'has_wordpress_blocks': 'yes' if '<!-- wp:' in (content or '') else 'no',
            'shortcodes': ' | '.join(sorted(set(shortcode_re.findall(content or '')))),
            'media_url_count': str(len(extract_urls(content))),
            'meta_keys': ' | '.join(sorted(postmeta.keys())),
        }
        items.append(row)
        for sc in sorted(set(shortcode_re.findall(content or ''))):
            shortcodes.append({'post_id': row['post_id'], 'post_type': row['post_type'], 'slug': row['slug'], 'title': row['title'], 'shortcode': sc})
        for u in extract_urls(content):
            media_refs.append({'post_id': row['post_id'], 'post_type': row['post_type'], 'slug': row['slug'], 'title': row['title'], 'url': u, 'is_upload': 'yes' if 'wp-content/uploads' in u else 'no'})
        elem.clear()

fields = ['post_id','post_type','status','title','slug','link','creator','pub_date_rss','post_date','post_date_gmt','modified','modified_gmt','post_parent','menu_order','comment_status','ping_status','is_sticky','categories','tags','terms_other','attachment_url','featured_image_id','template','content_html','excerpt_html','content_text_preview','content_char_count','has_wordpress_blocks','shortcodes','media_url_count','meta_keys']

def write_csv(path, rows, fields):
    with open(path,'w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader(); w.writerows(rows)

write_csv(out_dir/'wordpress_all_items_inventory.csv', items, fields)
for typ in sorted(set(r['post_type'] for r in items)):
    typ_rows=[r for r in items if r['post_type']==typ]
    safe = re.sub(r'[^A-Za-z0-9_-]+','_', typ or 'unknown')
    write_csv(out_dir/f'wordpress_{safe}.csv', typ_rows, fields)
write_csv(out_dir/'wordpress_media_references.csv', media_refs, ['post_id','post_type','slug','title','url','is_upload'])
write_csv(out_dir/'wordpress_shortcodes.csv', shortcodes, ['post_id','post_type','slug','title','shortcode'])

# Create JSON seed for Flask content, avoiding attachments/nav_menu_item by default
content_seed=[]
for r in items:
    if r['post_type'] in {'page','post'} and r['status'] in {'publish','draft','private'}:
        content_seed.append({
            'id': r['post_id'],
            'type': r['post_type'],
            'status': r['status'],
            'title': r['title'],
            'slug': r['slug'],
            'url': r['link'],
            'date': r['post_date'],
            'modified': r['modified'],
            'parent': r['post_parent'],
            'menu_order': r['menu_order'],
            'categories': [x for x in r['categories'].split(' | ') if x],
            'tags': [x for x in r['tags'].split(' | ') if x],
            'featured_image_id': r['featured_image_id'],
            'template': r['template'],
            'excerpt_html': r['excerpt_html'],
            'content_html': r['content_html'],
        })
with open(out_dir/'flask_content_seed.json','w',encoding='utf-8') as f:
    json.dump(content_seed, f, ensure_ascii=False, indent=2)

# Summaries
from collections import Counter, defaultdict
summary = {
    'site': site,
    'total_items': len(items),
    'by_post_type': dict(Counter(r['post_type'] or 'unknown' for r in items)),
    'by_status': dict(Counter(r['status'] or 'unknown' for r in items)),
    'by_type_status': {typ: dict(Counter(r['status'] or 'unknown' for r in items if r['post_type']==typ)) for typ in sorted(set(r['post_type'] for r in items))},
    'published_pages': len([r for r in items if r['post_type']=='page' and r['status']=='publish']),
    'published_posts': len([r for r in items if r['post_type']=='post' and r['status']=='publish']),
    'attachments': len([r for r in items if r['post_type']=='attachment']),
    'media_references_in_content': len(media_refs),
    'upload_references_in_content': len([m for m in media_refs if m['is_upload']=='yes']),
    'items_with_wordpress_blocks': len([r for r in items if r['has_wordpress_blocks']=='yes']),
    'items_with_shortcodes': len({s['post_id'] for s in shortcodes}),
    'shortcode_counts': dict(Counter(s['shortcode'] for s in shortcodes)),
    'top_level_pages': [
        {'title': r['title'], 'slug': r['slug'], 'status': r['status'], 'menu_order': r['menu_order'], 'link': r['link']}
        for r in sorted([r for r in items if r['post_type']=='page' and (r['post_parent'] in {'','0'})], key=lambda x: (int(x['menu_order'] or 0), x['title'].lower()))
    ],
}
with open(out_dir/'migration_summary.json','w',encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print(json.dumps(summary, indent=2, ensure_ascii=False)[:6000])
print('\nWrote files to', out_dir)
