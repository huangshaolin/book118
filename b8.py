#!/usr/bin/env python3

import os
import sys
import json
import time
import imghdr
import inspect
import requests
import urllib.parse as urlparse

from fpdf import FPDF


_self_dir = os.path.dirname(os.path.realpath(
    inspect.getfile(inspect.currentframe())))


def get_url_params(url):
    parts = urlparse.urlparse(url)
    params = dict(urlparse.parse_qsl(parts.query))
    return params


def update_url_params(url, new_params):
    parts = urlparse.urlparse(url)
    params = dict(urlparse.parse_qsl(parts.query))
    params.update(new_params)
    new_query = urlparse.urlencode(params, doseq=True)
    new_parts = parts._replace(query=new_query)
    new_url = urlparse.urlunparse(new_parts)
    return new_url


def chunk_download(url, path):
    r = requests.get(url, stream=True)
    r.raise_for_status()
    with open(path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)


def safe_download(url, path):
    temp_path = path + '.temp'
    print("downloading to %s ...    " % path, end='', flush=True)
    chunk_download(url, temp_path)
    os.rename(temp_path, path)
    print("done", flush=True)


class Api(object):

    def __init__(self, document_id):
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': 'https',
            'Sec-Fetch-Mode': 'cors',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko)',
            'X-Requested-With': 'XMLHttpRequest',
        }
        raw_url = json.loads(requests.post('https://m.book118.com/home/View/viewUrl', data='id=%s&onlyread=' % document_id,
                                           headers=headers).text)['data']
        params = get_url_params(raw_url)
        self.base_url = update_url_params('https://openapi.book118.com/getPreview.html', {
            'aid': params['aid'],
            'view_token': params['token'],
            'project_id': params['project_id'],
        })
        pass

    def get_preview_pages_info(self, page):
        url = update_url_params(self.base_url, {'page': page})
        json_str_raw = requests.get(url).text
        json_str = json_str_raw[json_str_raw.find(
            '{'): json_str_raw.rfind('}')+1]
        preview_info = json.loads(json_str)
        return preview_info


class Book(object):

    def __init__(self, html_url):
        self.document_id = html_url[html_url.rfind('/')+1: html_url.rfind('.')]
        self.download_dir = {
            'img': os.path.join(_self_dir, 'download/%s/img' % self.document_id),
            'pdf': os.path.join(_self_dir, 'download/%s/pdf' % self.document_id),
        }
        self.api = Api(self.document_id)
        self.img_urls = {}
        self.get_img_url_by_page(1)
        first_img_url = self.img_urls['1']
        self.img_ext = first_img_url[first_img_url.rfind('.')+1:]

    def get_img_url_by_page(self, page, *, retry_times=0):
        if str(page) in self.img_urls:
            return self.img_urls[str(page)]
        preview_info = self.api.get_preview_pages_info(page)
        url_data = preview_info['data']
        if not url_data:
            print("ERROR: page=%d, url_data=%s" % (page, url_data))
            return {}
        keys = list(url_data.keys())
        if len(keys) > 0 and not url_data[keys[0]]:
            if retry_times < 3:
                print(
                    "WARNING: retrieve preview data page=%d failed, we will retry after 3 seconds" % page)
                time.sleep(3)
                return self.get_img_url_by_page(page, retry_times=retry_times + 1)
            else:
                print(
                    "WARNING: retrieve preview data page=%d failed three times, we will not retry any more" % page)

        if not hasattr(self, 'pages'):
            self.pages = {
                'actual': int(preview_info['pages']['actual']),
                'preview': int(preview_info['pages']['preview']),
                'preview_size': len(keys)
            }
            if self.pages['preview'] < self.pages['actual']:
                print('WARNING: document_id=%s, preview_pages=%d < actual_pages=%d'
                      % (self.document_id, self.pages['preview'], self.pages['actual']))

        self.img_urls.update(url_data)
        return self.img_urls[str(page)]

    def download_all_imgs(self):
        os.makedirs(self.download_dir['img'], exist_ok=True)
        for page in range(1, self.pages['preview'] + 1):
            file_name = str(page).zfill(
                len(str(self.pages['preview']))) + '.' + self.img_ext
            file_path = os.path.join(self.download_dir['img'], file_name)
            if os.path.isfile(file_path):
                print("INFO: file=%s already exists, we will skip it." % file_path)
                continue
            url = self.get_img_url_by_page(page)
            if url.startswith('//'):
                url = 'https:' + url
            safe_download(url, file_path)
            img_ext = imghdr.what(file_path)
            base_file, ext = os.path.splitext(file_path)
            if ext != img_ext:
                os.rename(file_path, base_file + '.' + img_ext)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: b8 <book118_document_url>")
        sys.exit()
    book1 = Book(sys.argv[1])
    book1.download_all_imgs()
    img_dir = book1.download_dir['img']
    pdf_dir = book1.download_dir['pdf']
    img_list = [os.path.join(img_dir, x) for x in os.listdir(img_dir)]
    pdf = FPDF()
    for img in img_list:
        pdf.add_page()
        pdf.image(img)
    os.makedirs(book1.download_dir['pdf'], exist_ok=True)
    pdf_path = os.path.join(book1.download_dir['pdf'], 'output.pdf')
    print('Converting images to %s ...' % pdf_path)
    pdf.output(pdf_path, 'F')
    print('done')
